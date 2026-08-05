"""Catalogue local des entreprises / jeux de données."""

from pathlib import Path
from typing import List, Dict, Any
import json

from config import settings


ENTITY_FILES = {
    "customers": "customers.json",
    "orders": "orders.json",
    "campaigns": "campaigns.json",
    "products": "products.json",
}


def data_root() -> Path:
    return Path(settings.data_dir)


def list_companies() -> List[Dict[str, Any]]:
    """
    Scanne data_dir et retourne les company_id avec les entités présentes.
    """
    root = data_root()
    if not root.exists():
        return []

    companies = []
    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        company_id = path.name
        entities = []
        counts = {}
        for entity, filename in ENTITY_FILES.items():
            f = path / filename
            if f.exists():
                entities.append(entity)
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    counts[entity] = len(data) if isinstance(data, list) else 1
                except Exception:
                    counts[entity] = "?"
        profile_name = company_id
        profile_path = path / "profile.json"
        if profile_path.exists():
            try:
                profile = json.loads(profile_path.read_text(encoding="utf-8"))
                profile_name = profile.get("name") or company_id
            except Exception:
                pass

        companies.append({
            "company_id": company_id,
            "name": profile_name,
            "entities": entities,
            "counts": counts,
            "has_customers": "customers" in entities,
            "has_orders": "orders" in entities,
            "has_campaigns": "campaigns" in entities,
        })
    return companies