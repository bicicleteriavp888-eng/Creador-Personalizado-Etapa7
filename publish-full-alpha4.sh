#!/usr/bin/env bash
# Importa el ZIP completo alpha.4 (ya incluye Etapa 7) al repositorio y lo publica.
# Uso: bash publish-full-alpha4.sh /ruta/al/Creador-Personalizado-3.0.0-alpha.4-Full-GPLv3.zip
set -Eeuo pipefail

EXPECTED_REPO="Creador-Personalizado-Etapa7"
REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_SHA="6776c0596255901d1fcdc445713c2d2d0d500f393f3bfd16b15a218d32021646"

[[ $# -eq 1 ]] || { echo "Uso: bash $0 /ruta/al/ZIP-completo.zip" >&2; exit 2; }
ARCHIVE="$(realpath -e "$1")"
[[ -f "$ARCHIVE" ]] || { echo "No es un archivo: $ARCHIVE" >&2; exit 1; }
command -v git >/dev/null || { echo "Falta git." >&2; exit 1; }
command -v unzip >/dev/null || { echo "Falta unzip. Instalá con: sudo dnf install unzip" >&2; exit 1; }

REMOTE="$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null || true)"
[[ "$REMOTE" == *"$EXPECTED_REPO"* ]] || { echo "Clon incorrecto: $REMOTE" >&2; exit 1; }
BRANCH="$(git -C "$REPO_DIR" branch --show-current)"
[[ "$BRANCH" == "main" ]] || { echo "Cambiá a main (rama actual: $BRANCH)." >&2; exit 1; }
[[ -z "$(git -C "$REPO_DIR" status --porcelain)" ]] || {
  echo "Hay cambios locales. Revisá git status --short antes de continuar." >&2; exit 1;
}

echo "[1/6] Sincronizando main..."
git -C "$REPO_DIR" fetch origin
LOCAL="$(git -C "$REPO_DIR" rev-parse HEAD)"
UPSTREAM="$(git -C "$REPO_DIR" rev-parse origin/main)"
if git -C "$REPO_DIR" merge-base --is-ancestor "$LOCAL" "$UPSTREAM"; then
  git -C "$REPO_DIR" merge --ff-only origin/main
elif git -C "$REPO_DIR" merge-base --is-ancestor "$UPSTREAM" "$LOCAL"; then
  echo "La rama local ya contiene origin/main; se preservan los commits locales."
else
  echo "La rama local y origin/main divergieron. No voy a sobrescribir commits." >&2
  echo "Ejecutá git rebase origin/main, resolvé los conflictos y volvé a correr el script." >&2
  exit 1
fi

TMP="$(mktemp -d "${TMPDIR:-/tmp}/creador-alpha4-publish.XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
echo "[2/6] Comprobando e inspeccionando el ZIP..."
ACTUAL_SHA="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
if [[ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]]; then
  echo "Aviso: SHA-256 distinto del archivo recibido originalmente: $ACTUAL_SHA"
fi
unzip -q "$ARCHIVE" -d "$TMP/unpacked"
SRC="$(find "$TMP/unpacked" -mindepth 2 -maxdepth 3 -type f -name main.py -printf '%h\n' | head -n 1)"
[[ -n "$SRC" ]] || { echo "No se encontró main.py dentro del ZIP." >&2; exit 1; }

for required in pyproject.toml requirements.txt core gui profiles tests LICENSE LICENSING-NOTICE.md; do
  [[ -e "$SRC/$required" ]] || { echo "Falta en el paquete: $required" >&2; exit 1; }
done
[[ -f "$SRC/core/projects/manager.py" && -f "$SRC/core/projects/catalog.py" ]] || {
  echo "El paquete no incluye la gestión de proyectos de Etapa 7; se detiene." >&2; exit 1;
}
grep -q 'version = "3.0.0a4"' "$SRC/pyproject.toml" || {
  echo "La versión del paquete no es 3.0.0-alpha.4." >&2; exit 1;
}
echo "Versión: 3.0.0-alpha.4"
echo "Etapa 7: ya integrada; no se aplica ningún parche adicional."
echo "SHA-256 ZIP: $ACTUAL_SHA"

echo "[3/6] Preparando árbol limpio..."
STAGE="$TMP/source"
mkdir -p "$STAGE"
tar -C "$SRC" \
  --exclude='./.git' \
  --exclude='./.venv' --exclude='./venv' \
  --exclude='./__pycache__' --exclude='*/__pycache__' \
  --exclude='*.pyc' --exclude='*.pyo' \
  --exclude='./.pytest_cache' --exclude='*/.pytest_cache' \
  --exclude='./.mypy_cache' --exclude='*/.mypy_cache' \
  --exclude='./.ruff_cache' --exclude='*/.ruff_cache' \
  --exclude='./build' --exclude='./dist' --exclude='*/build' --exclude='*/dist' \
  --exclude='*.egg-info' --exclude='./test-reports' --exclude='./.coverage' \
  --exclude='*.iso' --exclude='*.raw' \
  -cf - . | tar -C "$STAGE" -xf -

echo "[4/6] Integrando el código completo y conservando el overlay GPL histórico..."
PRESERVE="$TMP/preserve"
mkdir -p "$PRESERVE"
for item in Etapa7-overlay-GPLv3.tar.gz apply-etapa7-overlay.sh; do
  [[ -e "$REPO_DIR/$item" ]] && cp -a "$REPO_DIR/$item" "$PRESERVE/"
done
cp -a "$STAGE/." "$REPO_DIR/"
for item in "$PRESERVE"/*; do
  [[ -e "$item" ]] || continue
  cp -a "$item" "$REPO_DIR/"
done

rm -f "$REPO_DIR/Etapa7-overlay.tar.gz"
rm -f "$REPO_DIR/import-full-app.sh" "$REPO_DIR/import-full-app-from-local-source.sh"
printf '%s  %s\n' "$ACTUAL_SHA" "$(basename "$ARCHIVE")" > "$REPO_DIR/FULL-SOURCE-SHA256.txt"

cat >> "$REPO_DIR/README.md" <<'README_APPEND'

---

## Código fuente completo publicado

La rama principal contiene el árbol fuente completo de **Creador Personalizado 3.0.0-alpha.4**, con la Etapa 7 integrada: almacenamiento de proyectos independientes, perfiles nominales y plantillas. No es necesario aplicar el overlay para una instalación nueva.

- Licencia del proyecto: **GPL-3.0-or-later** (archivo LICENSE).
- Avisos de dependencias: LICENSING-NOTICE.md.
- El overlay Etapa7-overlay-GPLv3.tar.gz se conserva únicamente para migrar árboles alpha.3 / Etapa 6.
- Verificación del ZIP fuente recibido: FULL-SOURCE-SHA256.txt.
README_APPEND

echo "[5/6] Verificando los componentes..."
for required in main.py core/projects/manager.py core/projects/catalog.py gui/custom_distro.py profiles/terminal-atencion.json tests/test_project_store.py tests/test_project_templates.py LICENSE LICENSING-NOTICE.md; do
  [[ -f "$REPO_DIR/$required" ]] || { echo "Falta archivo: $required" >&2; exit 1; }
done
if find "$REPO_DIR" -type f \( -name '*.pyc' -o -name '*.pyo' \) -print -quit | grep -q .; then
  echo "Se encontraron archivos bytecode; no se publicará." >&2; exit 1;
fi

git -C "$REPO_DIR" add -A
if ! git -C "$REPO_DIR" diff --cached --quiet; then
  git -C "$REPO_DIR" commit -m "release: publish complete Creador Personalizado alpha.4 with Etapa 7"
fi

echo "[6/6] Enviando a GitHub..."
git -C "$REPO_DIR" push origin main
echo
echo "Publicación finalizada."
echo "Repositorio: $REMOTE"
echo "Commit: $(git -C "$REPO_DIR" rev-parse HEAD)"
echo "Archivos versionados: $(git -C "$REPO_DIR" ls-files | wc -l)"
