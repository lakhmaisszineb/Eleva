"""
Map arbitrary CSV column names to Eleva schema using LLM + alias fallback.
"""

from typing import Dict, List, Any, Optional
import json
import re

from data.importer.schema import SCHEMA, REQUIRED, ALIASES
from llm.groq_client import chat
from config import get_logger

logger = get_logger(__name__)

MAPPER_SYSTEM = """Tu es un expert en intégration de données e-commerce.
On te donne la liste des colonnes d'un fichier CSV/Excel et le schéma cible Eleva.
Tu dois proposer un mapping JSON strict.

Règles:
- Mappe uniquement vers les champs du schéma cible fourni.
- Si aucune colonne ne correspond à un champ, mets null.
- Liste dans "ignored" toutes les colonnes source non utilisées.
- N'invente aucun nom de colonne source: utilise uniquement ceux fournis.
- Réponds UNIQUEMENT avec un JSON valide, sans texte autour.
"""

MAPPER_USER = """Type de fichier: {entity}

Colonnes présentes dans le fichier:
{columns}

Schéma Eleva cible (champs autorisés):
{target_fields}

Champs obligatoires:
{required_fields}

Format de réponse JSON attendu:
{{
  "mapping": {{
    "champ_eleva": "nom_colonne_source ou null",
    ...
  }},
  "ignored": ["colonne_source_non_utilisee", ...]
}}
"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1)
    return json.loads(text)


def _alias_fallback(columns: List[str], entity: str) -> Dict[str, Optional[str]]:
    """Deterministic fallback using ALIASES."""
    normalized = {c: re.sub(r"[^a-z0-9]", "", c.lower()) for c in columns}
    mapping: Dict[str, Optional[str]] = {field: None for field in SCHEMA[entity]}

    for field in SCHEMA[entity]:
        aliases = [re.sub(r"[^a-z0-9]", "", a.lower()) for a in ALIASES.get(field, [])]
        for col, col_norm in normalized.items():
            if col_norm in aliases or col_norm == re.sub(r"[^a-z0-9]", "", field.lower()):
                mapping[field] = col
                break
    return mapping


def map_columns_with_llm(columns: List[str], entity: str) -> Dict[str, Any]:
    """
    Use LLM to map source columns to Eleva schema.
    Falls back to alias matching if LLM fails.
    """
    if entity not in SCHEMA:
        raise ValueError(f"Unknown entity: {entity}. Expected one of {list(SCHEMA.keys())}")

    target_fields = SCHEMA[entity]
    required_fields = REQUIRED[entity]

    user_prompt = MAPPER_USER.format(
        entity=entity,
        columns="\n".join(f"- {c}" for c in columns),
        target_fields=", ".join(target_fields),
        required_fields=", ".join(required_fields),
    )

    try:
        raw = chat(MAPPER_SYSTEM, user_prompt)
        data = _extract_json(raw)
        mapping = data.get("mapping", {})
        ignored = data.get("ignored", [])

        # Keep only known target fields
        clean_mapping = {f: mapping.get(f) for f in target_fields}

        # Validate that mapped source columns exist
        for field, source in list(clean_mapping.items()):
            if source is not None and source not in columns:
                logger.warning(f"LLM mapped {field} -> '{source}' but column missing. Setting null.")
                clean_mapping[field] = None

        # Ensure ignored only contains real columns
        ignored = [c for c in ignored if c in columns]

        logger.info(f"[Mapper] LLM mapping for {entity}: {clean_mapping}")
        return {"mapping": clean_mapping, "ignored": ignored, "source": "llm"}

    except Exception as e:
        logger.error(f"[Mapper] LLM mapping failed ({e}) – using alias fallback")
        mapping = _alias_fallback(columns, entity)
        used = {v for v in mapping.values() if v}
        ignored = [c for c in columns if c not in used]
        return {"mapping": mapping, "ignored": ignored, "source": "alias_fallback"}


def validate_mapping(mapping: Dict[str, Optional[str]], entity: str) -> List[str]:
    """Return list of errors (empty if OK)."""
    errors = []
    for field in REQUIRED.get(entity, []):
        if not mapping.get(field):
            errors.append(f"Required field '{field}' could not be mapped.")
    return errors