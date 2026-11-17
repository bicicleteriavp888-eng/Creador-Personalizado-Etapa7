#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Uso:
  ./apply-etapa7-overlay.sh /ruta/al/Creador-Personalizado-3.0.0-alpha.3

Aplica el parche de Etapa 7 sobre un árbol base existente.
No crea un proyecto completo desde cero.
EOF
}

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

DEST="$(realpath -e "$1")"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE="$SCRIPT_DIR/Etapa7-overlay.tar.gz"

if [[ ! -d "$DEST" || ! -f "$DEST/main.py" || ! -d "$DEST/core" || ! -d "$DEST/gui" ]]; then
  echo "ERROR: el destino no parece ser la raíz del proyecto Creador Personalizado." >&2
  exit 1
fi
if [[ ! -f "$ARCHIVE" ]]; then
  echo "ERROR: no se encuentra Etapa7-overlay.tar.gz junto al script." >&2
  exit 1
fi

tar -tzf "$ARCHIVE" >/dev/null

BACKUP="$(mktemp -d "${TMPDIR:-/tmp}/creador-etapa7-backup.XXXXXX")"
while IFS= read -r rel; do
  if [[ -f "$DEST/$rel" ]]; then
    mkdir -p "$BACKUP/$(dirname "$rel")"
    cp -a "$DEST/$rel" "$BACKUP/$rel"
  fi
done <<'EOF'
main.py
pyproject.toml
core/projects/__init__.py
core/projects/catalog.py
core/projects/manager.py
gui/tab_meta.py
gui/custom_distro.py
tests/test_project_store.py
tests/test_branding_3.py
CHANGELOG-ETAPA7.md
INFORME_ETAPA7.md
documentation/ETAPA7_GESTION_PROYECTOS.md
EOF

tar --no-same-owner -xzf "$ARCHIVE" -C "$DEST"
echo "Etapa 7 aplicada en: $DEST"
echo "Copia previa de archivos reemplazados: $BACKUP"
echo "Validación recomendada:"
echo "  cd \"$DEST\""
echo "  python -m compileall -q main.py core gui tests"
echo "  python -m pytest -q tests/test_project_store.py tests/test_branding_3.py tests/test_project_templates.py tests/test_profiles_catalog.py tests/test_history.py tests/test_software_policy.py"
