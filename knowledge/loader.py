"""
Load marketing playbooks from YAML files.
"""

from pathlib import Path
from typing import List, Dict, Any
import yaml

from config import settings, get_logger

logger = get_logger(__name__)


def load_playbooks(playbooks_dir: Path | None = None) -> List[Dict[str, Any]]:
    """
    Load all YAML playbooks from the playbooks directory.
    Returns a list of dictionaries.
    """
    directory = playbooks_dir or settings.knowledge_dir
    playbooks = []

    if not directory.exists():
        logger.warning(f"Playbooks directory not found: {directory}")
        return playbooks

    for file_path in directory.glob("*.yaml"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    data["_source_file"] = file_path.name
                    playbooks.append(data)
                    logger.debug(f"Loaded playbook: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")

    logger.info(f"Loaded {len(playbooks)} playbooks")
    return playbooks