#!/usr/bin/env python3
"""Crear, verificar o restaurar respaldos del proyecto Creador-kiosk."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.history import BackupManager


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    create = sub.add_parser("create"); create.add_argument("source"); create.add_argument("--backup-dir", default="./backups"); create.add_argument("--label", default="manual")
    verify = sub.add_parser("verify"); verify.add_argument("archive"); verify.add_argument("--backup-dir", default="./backups")
    restore = sub.add_parser("restore"); restore.add_argument("archive"); restore.add_argument("destination"); restore.add_argument("--backup-dir", default="./backups")
    args = parser.parse_args(); manager = BackupManager(args.backup_dir)
    if args.action == "create": result = manager.create(args.source, args.label)
    elif args.action == "verify": result = manager.verify(args.archive)
    else: result = {"restored_to": manager.restore(args.archive, args.destination)}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
