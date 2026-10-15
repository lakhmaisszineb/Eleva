"""Vérifie et répare la base SQLite d'Eleva sans supprimer les JSON."""

from __future__ import annotations

import argparse
from pathlib import Path

from config import settings
from data.db import DB_PATH, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Vérifier/réparer la base SQLite Eleva")
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help="Chemin de la base SQLite (par défaut: %(default)s)",
    )
    parser.add_argument(
        "--no-json-restore",
        action="store_true",
        help="Ne pas restaurer les JSON après détection d'une corruption",
    )
    args = parser.parse_args()

    result = init_db(
        args.db,
        restore_json_on_corruption=not args.no_json_restore,
    )
    print(f"Base vérifiée : {args.db}")
    print(f"État avant vérification : {result['status']}")
    if result["backup"]:
        print(f"Ancienne base conservée dans : {result['backup']}")
        print(f"Entreprises restaurées depuis les JSON : {len(result['restored'])}")
    else:
        print("Aucune corruption détectée ; aucune reconstruction nécessaire.")


if __name__ == "__main__":
    main()
