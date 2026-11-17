#!/usr/bin/env bash
# Publica el árbol fuente completo usando la copia alpha.3 que ya existe en Fedora.
# No requiere descargar el ZIP de ChatGPT.
# Uso desde el clon del repositorio:
#   bash import-full-app-from-local-source.sh ~/Descargas/Creador-Personalizado-3.0.0-alpha.3
set -Eeuo pipefail

EXPECTED_REPO="Creador-Personalizado-Etapa7"
REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  echo "Uso: bash $0 /ruta/a/Creador-Personalizado-3.0.0-alpha.3" >&2
  exit 2
}
[[ $# -eq 1 ]] || usage
SRC="$(realpath -e "$1")"

command -v git >/dev/null || { echo "Falta git." >&2; exit 1; }
command -v tar >/dev/null || { echo "Falta tar." >&2; exit 1; }

[[ -f "$SRC/main.py" && -f "$SRC/pyproject.toml" && -d "$SRC/core" && -d "$SRC/gui" ]] || {
  echo "La carpeta indicada no parece ser el árbol fuente completo de Creador Personalizado." >&2
  echo "Se esperaba main.py, pyproject.toml, core/ y gui/." >&2
  exit 1
}
REMOTE="$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null || true)"
[[ "$REMOTE" == *"$EXPECTED_REPO"* ]] || {
  echo "Este clon no apunta al repositorio esperado: $REMOTE" >&2
  exit 1
}
BRANCH="$(git -C "$REPO_DIR" branch --show-current)"
[[ "$BRANCH" == "main" ]] || {
  echo "Cambiá a main antes de continuar (rama actual: $BRANCH)." >&2
  exit 1
}
[[ -f "$REPO_DIR/Etapa7-overlay-GPLv3.tar.gz" && -x "$REPO_DIR/apply-etapa7-overlay.sh" || -f "$REPO_DIR/apply-etapa7-overlay.sh" ]] || {
  echo "Faltan el overlay o su instalador. Ejecutá primero: git pull --ff-only origin main" >&2
  exit 1
}
[[ -z "$(git -C "$REPO_DIR" status --porcelain)" ]] || {
  echo "El clon tiene cambios locales. Revisá 'git status --short' y dejalo limpio antes de continuar." >&2
  echo "Si el único cambio es el permiso ejecutable que agregaste al import-full-app.sh, ejecutá:" >&2
  echo "  git restore -- import-full-app.sh" >&2
  exit 1
}

TMP="$(mktemp -d "${TMPDIR:-/tmp}/creador-full-source.XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
STAGE="$TMP/source"
mkdir -p "$STAGE"

echo "[1/5] Copiando el árbol local a una zona temporal..."
tar -C "$SRC" \
  --exclude='./.git' \
  --exclude='./.venv' --exclude='./venv' \
  --exclude='./__pycache__' --exclude='*/__pycache__' \
  --exclude='./.pytest_cache' --exclude='*/.pytest_cache' \
  --exclude='./.mypy_cache' --exclude='*/.mypy_cache' \
  --exclude='./.ruff_cache' --exclude='*/.ruff_cache' \
  --exclude='./build' --exclude='./dist' --exclude='*/build' --exclude='*/dist' \
  --exclude='*.egg-info' --exclude='./test-reports' --exclude='./.coverage' \
  --exclude='*.iso' --exclude='*.raw' \
  -cf - . | tar -C "$STAGE" -xf -

for required in main.py pyproject.toml requirements.txt core gui profiles; do
  [[ -e "$STAGE/$required" ]] || {
    echo "El árbol local no contiene el componente requerido: $required" >&2
    exit 1
  }
done

echo "[2/5] Aplicando Etapa 7 y la gestión de proyectos..."
bash "$REPO_DIR/apply-etapa7-overlay.sh" "$STAGE"

echo "[3/5] Conservando avisos y archivos históricos del repositorio..."
PRESERVE="$TMP/preserve"
mkdir -p "$PRESERVE"
for item in LICENSE LICENSING-NOTICE.md SHA256SUMS.txt Etapa7-overlay-GPLv3.tar.gz Etapa7-overlay.tar.gz apply-etapa7-overlay.sh CHANGELOG-ETAPA7.md INFORME_ETAPA7.md documentation; do
  [[ -e "$REPO_DIR/$item" ]] && cp -a "$REPO_DIR/$item" "$PRESERVE/"
done

# README basado en el que ya acompaña a la aplicación, con la nota de publicación completa.
if [[ -f "$STAGE/README.md" ]]; then
  cat >> "$STAGE/README.md" <<'README_APPEND'

---

## Publicación pública de alpha.4

Este repositorio contiene el código fuente completo de **Creador Personalizado 3.0.0-alpha.4**, incluidos los cambios de Etapa 7 para gestionar proyectos independientes y sus perfiles. La licencia del proyecto es **GNU GPL-3.0-or-later**; consulte `LICENSE` y `LICENSING-NOTICE.md`. Las dependencias de terceros conservan sus propias licencias.

El archivo `Etapa7-overlay-GPLv3.tar.gz` se conserva como parche histórico para instalaciones que parten de alpha.3 / Etapa 6. Para una instalación nueva, utilice directamente el árbol fuente de la raíz del repositorio.

### Validación en Fedora 44

```bash
python -m compileall -q main.py core gui tests
python -m pytest -q
```

La ejecución completa de pruebas, la GUI en el equipo de destino y la generación de ISO deben verificarse en el Fedora 44 donde se vaya a utilizar.
README_APPEND
fi

cp -a "$STAGE/." "$REPO_DIR/"
for item in "$PRESERVE"/*; do
  [[ -e "$item" ]] || continue
  cp -a "$item" "$REPO_DIR/"
done

# Retirar el importador que dependía del ZIP no descargable.
rm -f "$REPO_DIR/import-full-app.sh"

echo "[4/5] Comprobando estructura y preparando publicación..."
for required in main.py pyproject.toml requirements.txt core/projects/manager.py gui/custom_distro.py profiles/terminal-atencion.json LICENSE LICENSING-NOTICE.md; do
  [[ -f "$REPO_DIR/$required" ]] || {
    echo "Falta un archivo esperado después de integrar Etapa 7: $required" >&2
    exit 1
  }
done

git -C "$REPO_DIR" add -A
if git -C "$REPO_DIR" diff --cached --quiet; then
  echo "No hay cambios para publicar; el árbol parece ya integrado."
  exit 0
fi

echo "[5/5] Creando commit y enviando a GitHub..."
git -C "$REPO_DIR" commit -m "release: publish complete Creador Personalizado alpha.4 source"
git -C "$REPO_DIR" push origin main

echo
echo "Publicación enviada."
echo "Repositorio: $REMOTE"
echo "Commit: $(git -C "$REPO_DIR" rev-parse HEAD)"
echo "Archivos versionados: $(git -C "$REPO_DIR" ls-files | wc -l)"
