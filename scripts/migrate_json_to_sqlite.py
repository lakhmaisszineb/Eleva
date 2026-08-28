"""
One-off migration: data/sample_data/<company_id>/*.json -> SQLite.
"""

import argparse
import json
from pathlib import Path

from config import settings, get_logger
from data.db import get_connection, init_db, upsert_profile, replace_customers, replace_orders, replace_campaigns

logger = get_logger(__name__)


def _load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def migrate_company(conn, company_id: str, data_dir: Path) -> dict:
    company_dir = data_dir / company_id
    if not company_dir.exists():
        logger.warning(f"[{company_id}] folder not found in {data_dir}, skipped")
        return {}

    stats = {}
    profile_path = company_dir / "profile.json"
    if profile_path.exists():
        upsert_profile(conn, company_id, _load_json(profile_path))
        stats["profile"] = True
    else:
        stats["profile"] = False

    customers_path = company_dir / "customers.json"
    stats["customers"] = replace_customers(conn, company_id, _load_json(customers_path)) if customers_path.exists() else 0

    orders_path = company_dir / "orders.json"
    stats["orders"] = replace_orders(conn, company_id, _load_json(orders_path)) if orders_path.exists() else 0

    campaigns_path = company_dir / "campaigns.json"
    stats["campaigns"] = replace_campaigns(conn, company_id, _load_json(campaigns_path)) if campaigns_path.exists() else 0

    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--companies", nargs="*", default=None)
    parser.add_argument("--delete-json", action="store_true")
    args = parser.parse_args()

    data_dir = Path(settings.data_dir)
    init_db()
    companies = args.companies or [p.name for p in data_dir.iterdir() if p.is_dir()]

    conn = get_connection()
    all_stats = {}
    try:
        for company_id in companies:
            all_stats[company_id] = migrate_company(conn, company_id, data_dir)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("Migration terminée :")
    for company_id, stats in all_stats.items():
        print(f"  {company_id}: {stats}")

    if args.delete_json:
        for company_id, stats in all_stats.items():
            if not stats:
                continue
            company_dir = data_dir / company_id
            for fname in ("profile.json", "customers.json", "orders.json", "campaigns.json"):
                fpath = company_dir / fname
                if fpath.exists():
                    fpath.unlink()
            print(f"  {company_id}: JSON supprimés.")


if __name__ == "__main__":
    main()
