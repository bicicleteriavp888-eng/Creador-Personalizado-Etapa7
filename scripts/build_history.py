#!/usr/bin/env python3
"""Consultar el historial local de compilaciones de Creador-kiosk."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.history import BuildHistory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", help="Ruta alternativa a history.sqlite3")
    sub = parser.add_subparsers(dest="action", required=True)
    listing = sub.add_parser("list"); listing.add_argument("--limit", type=int, default=50)
    detail = sub.add_parser("show"); detail.add_argument("build_id")
    args = parser.parse_args(); history = BuildHistory(args.database)
    result = history.list(args.limit) if args.action == "list" else history.get(args.build_id)
    if result is None:
        print("No se encontró esa compilación.", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
