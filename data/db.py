"""Couche SQLite fiable pour Eleva.

La couche conserve les mêmes tables et les mêmes fonctions publiques que la
version précédente. Elle ajoute uniquement :
- un contrôle d'intégrité au démarrage ;
- une sauvegarde de toute base détectée comme corrompue ;
- une reconstruction depuis les JSON présents dans ``settings.data_dir`` ;
- un timeout et un verrou d'écriture adaptés aux opérations Streamlit/API.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import settings

DB_PATH: Path = Path(settings.data_dir) / "eleva.db"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS company_profile (
    company_id      TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    industry        TEXT NOT NULL,
    description     TEXT,
    current_focus   TEXT,
    goals_json      TEXT NOT NULL DEFAULT '[]',
    metadata_json   TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS customers (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id              TEXT NOT NULL,
    customer_id             TEXT NOT NULL,
    total_orders            INTEGER DEFAULT 0,
    total_spent             REAL DEFAULT 0.0,
    days_since_last_order   INTEGER,
    churn_risk_score        REAL,
    email                   TEXT,
    segment                 TEXT,
    extra_json              TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_customers_company ON customers(company_id);

CREATE TABLE IF NOT EXISTS orders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id     TEXT NOT NULL,
    order_id       TEXT NOT NULL,
    customer_id    TEXT,
    status         TEXT,
    total          REAL DEFAULT 0.0,
    order_date     TEXT,
    extra_json     TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_orders_company ON orders(company_id);

CREATE TABLE IF NOT EXISTS campaigns (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id         TEXT NOT NULL,
    campaign_id        TEXT,
    name               TEXT,
    type               TEXT,
    conversion_rate    REAL,
    roi                REAL,
    extra_json         TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_campaigns_company ON campaigns(company_id);
"""

CUSTOMER_CORE_FIELDS = [
    "customer_id", "total_orders", "total_spent",
    "days_since_last_order", "churn_risk_score", "email", "segment",
]
ORDER_CORE_FIELDS = ["order_id", "customer_id", "status", "total", "order_date"]
CAMPAIGN_CORE_FIELDS = ["campaign_id", "name", "type", "conversion_rate", "roi"]


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Ouvre une connexion configurée pour des opérations répétées et concurrentes."""
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    # WAL évite qu'une lecture Streamlit bloque une écriture API et inversement.
    # Le réglage est persistant et ne modifie pas la logique métier.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _integrity_status(path: Path) -> tuple[bool, str]:
    """Retourne ``(True, 'ok')`` si SQLite peut lire correctement la base."""
    if not path.exists() or path.stat().st_size == 0:
        return True, "new"
    conn = None
    try:
        conn = sqlite3.connect(str(path), timeout=5.0)
        result = conn.execute("PRAGMA quick_check").fetchone()
        status = str(result[0]) if result else "unknown"
        return status.lower() == "ok", status
    except sqlite3.DatabaseError as exc:
        return False, str(exc)
    finally:
        if conn is not None:
            conn.close()


def _quarantine_corrupt_database(path: Path) -> Path:
    """Conserve la copie brute de la base avant sa reconstruction."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_name(f"{path.name}.corrupt-{stamp}.bak")
    shutil.copy2(path, backup)
    return backup


def _load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _restore_json_sources(conn: sqlite3.Connection, data_dir: Path) -> dict[str, dict[str, int | bool]]:
    """Restaure les JSON d'entreprises dans une base nouvellement reconstruite."""
    restored: dict[str, dict[str, int | bool]] = {}
    if not data_dir.exists():
        return restored

    for company_dir in sorted(data_dir.iterdir()):
        if not company_dir.is_dir() or company_dir.name.startswith("__"):
            continue
        company_id = company_dir.name
        profile = _load_json(company_dir / "profile.json", None)
        if not profile:
            continue
        upsert_profile(conn, company_id, profile)
        stats: dict[str, int | bool] = {"profile": True}
        for entity, loader in (
            ("customers", replace_customers),
            ("orders", replace_orders),
            ("campaigns", replace_campaigns),
        ):
            rows = _load_json(company_dir / f"{entity}.json", [])
            stats[entity] = loader(conn, company_id, rows) if isinstance(rows, list) else 0
        restored[company_id] = stats
    return restored


def _create_empty_database(path: Path) -> None:
    """Crée une base neuve dans un fichier temporaire puis la remplace atomiquement."""
    temp = path.with_name(f".{path.name}.rebuild-{os.getpid()}.tmp")
    if temp.exists():
        temp.unlink()
    conn = sqlite3.connect(str(temp), timeout=30.0)
    try:
        conn.executescript(_SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
    os.replace(temp, path)


def init_db(db_path: Optional[Path] = None, *, restore_json_on_corruption: bool = True) -> dict:
    """Initialise ou répare la base sans toucher au cycle de décision.

    Une base saine est simplement vérifiée et son schéma est créé si nécessaire.
    Une base illisible est renommée en sauvegarde ``*.corrupt-*.bak``. Une base
    neuve est alors créée et, si possible, les JSON de ``settings.data_dir`` sont
    restaurés dedans.
    """
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    healthy, status = _integrity_status(path)
    recovery = {"status": status, "backup": None, "restored": {}}

    if not healthy:
        recovery["backup"] = str(_quarantine_corrupt_database(path))
        for suffix in ("-wal", "-shm"):
            sidecar = Path(f"{path}{suffix}")
            if sidecar.exists():
                sidecar.unlink()
        path.unlink(missing_ok=True)
        _create_empty_database(path)
        if restore_json_on_corruption:
            conn = get_connection(path)
            try:
                recovery["restored"] = _restore_json_sources(conn, Path(settings.data_dir))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        return recovery

    conn = get_connection(path)
    try:
        conn.executescript(_SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
    return recovery


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads(value: Optional[str]):
    if not value:
        return {}
    return json.loads(value)


def split_core_extra(row: dict, core_fields: list):
    core = {k: row.get(k) for k in core_fields}
    extra = {k: v for k, v in row.items() if k not in core_fields}
    return core, extra


def replace_customers(conn: sqlite3.Connection, company_id: str, rows) -> int:
    conn.execute("DELETE FROM customers WHERE company_id = ?", (company_id,))
    for row in rows:
        core, extra = split_core_extra(row, CUSTOMER_CORE_FIELDS)
        conn.execute(
            """
            INSERT INTO customers (company_id, customer_id, total_orders, total_spent,
                                   days_since_last_order, churn_risk_score, email, segment, extra_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (company_id, core.get("customer_id"), core.get("total_orders", 0),
             core.get("total_spent", 0.0), core.get("days_since_last_order"),
             core.get("churn_risk_score"), core.get("email"), core.get("segment"), dumps(extra)),
        )
    return len(rows)


def replace_orders(conn: sqlite3.Connection, company_id: str, rows) -> int:
    conn.execute("DELETE FROM orders WHERE company_id = ?", (company_id,))
    for row in rows:
        core, extra = split_core_extra(row, ORDER_CORE_FIELDS)
        conn.execute(
            """
            INSERT INTO orders (company_id, order_id, customer_id, status, total, order_date, extra_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (company_id, core.get("order_id"), core.get("customer_id"), core.get("status"),
             core.get("total", 0.0), core.get("order_date"), dumps(extra)),
        )
    return len(rows)


def replace_campaigns(conn: sqlite3.Connection, company_id: str, rows) -> int:
    conn.execute("DELETE FROM campaigns WHERE company_id = ?", (company_id,))
    for row in rows:
        core, extra = split_core_extra(row, CAMPAIGN_CORE_FIELDS)
        conn.execute(
            """
            INSERT INTO campaigns (company_id, campaign_id, name, type, conversion_rate, roi, extra_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (company_id, core.get("campaign_id"), core.get("name"), core.get("type"),
             core.get("conversion_rate"), core.get("roi"), dumps(extra)),
        )
    return len(rows)


def upsert_profile(conn: sqlite3.Connection, company_id: str, profile: dict) -> None:
    conn.execute(
        """
        INSERT INTO company_profile (company_id, name, industry, description, current_focus, goals_json, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(company_id) DO UPDATE SET
            name=excluded.name, industry=excluded.industry, description=excluded.description,
            current_focus=excluded.current_focus, goals_json=excluded.goals_json, metadata_json=excluded.metadata_json
        """,
        (company_id, profile["name"], profile["industry"], profile.get("description"),
         profile.get("current_focus"), dumps(profile.get("goals", [])),
         dumps(profile.get("metadata", {}))),
    )


REPLACE_BY_ENTITY = {
    "customers": replace_customers,
    "orders": replace_orders,
    "campaigns": replace_campaigns,
}
