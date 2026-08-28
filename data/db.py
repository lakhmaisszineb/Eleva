"""
SQLite access layer (connection + schema).
"""

import json
import sqlite3
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
    extra_json               TEXT NOT NULL DEFAULT '{}'
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


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(_SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads(value: Optional[str]):
    if not value:
        return {}
    return json.loads(value)


CUSTOMER_CORE_FIELDS = [
    "customer_id", "total_orders", "total_spent",
    "days_since_last_order", "churn_risk_score", "email", "segment",
]
ORDER_CORE_FIELDS = ["order_id", "customer_id", "status", "total", "order_date"]
CAMPAIGN_CORE_FIELDS = ["campaign_id", "name", "type", "conversion_rate", "roi"]


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
            (
                company_id, core.get("customer_id"), core.get("total_orders", 0), core.get("total_spent", 0.0),
                core.get("days_since_last_order"), core.get("churn_risk_score"),
                core.get("email"), core.get("segment"), dumps(extra),
            ),
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
            (
                company_id, core.get("order_id"), core.get("customer_id"), core.get("status"),
                core.get("total", 0.0), core.get("order_date"), dumps(extra),
            ),
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
            (
                company_id, core.get("campaign_id"), core.get("name"), core.get("type"),
                core.get("conversion_rate"), core.get("roi"), dumps(extra),
            ),
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
        (
            company_id, profile["name"], profile["industry"], profile.get("description"),
            profile.get("current_focus"), dumps(profile.get("goals", [])), dumps(profile.get("metadata", {})),
        ),
    )


REPLACE_BY_ENTITY = {
    "customers": replace_customers,
    "orders": replace_orders,
    "campaigns": replace_campaigns,
}
