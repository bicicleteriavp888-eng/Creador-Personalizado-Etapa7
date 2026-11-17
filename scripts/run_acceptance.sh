#!/usr/bin/env bash
# Ejecuta las comprobaciones reproducibles en el Fedora destino.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${CREADOR_KIOSK_TEST_REPORT_DIR:-$ROOT/test-reports/$STAMP}"
mkdir -p "$OUT"
FAIL=0
run() {
  local name="$1"; shift
  echo "== $name =="
  "$@" >"$OUT/$name.log" 2>&1
  local rc=$?
  cat "$OUT/$name.log"
  echo "$name=$rc" | tee -a "$OUT/summary.txt"
  [[ $rc -eq 0 ]] || FAIL=1
}
run compileall python3 -m compileall -q .
run pytest python3 -m pytest -q
run package_build python3 -m pip wheel --no-deps --no-build-isolation -w "$OUT/wheels" .
{
  echo "PySide6=$(python3 -c 'import PySide6; print(PySide6.__version__)' 2>&1 || true)"
  echo "QEMU=$(command -v qemu-system-x86_64 || echo unavailable)"
  echo "OVMF_CODE=$(find /usr/share -name 'OVMF_CODE*.fd' -print -quit 2>/dev/null || true)"
  echo "Date=$(date --iso-8601=seconds)"
} > "$OUT/environment.txt"
if [[ -n "${1:-}" ]]; then
  run iso_lab python3 scripts/validate_iso.py "$@"
fi
printf '\nInforme guardado en: %s\n' "$OUT"
exit "$FAIL"
