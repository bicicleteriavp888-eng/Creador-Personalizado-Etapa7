#!/usr/bin/env bash
# Publica el código completo alpha.4 (la Etapa 7 ya está integrada) y limpia el repositorio.
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
command -v tar >/dev/null || { echo "Falta tar." >&2; exit 1; }
command -v sha256sum >/dev/null || { echo "Falta sha256sum." >&2; exit 1; }

REMOTE="$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null || true)"
[[ "$REMOTE" == *"$EXPECTED_REPO"* ]] || { echo "Clon incorrecto: $REMOTE" >&2; exit 1; }
BRANCH="$(git -C "$REPO_DIR" branch --show-current)"
[[ "$BRANCH" == "main" ]] || { echo "Cambiá a main (rama actual: $BRANCH)." >&2; exit 1; }
[[ -z "$(git -C "$REPO_DIR" status --porcelain)" ]] || {
  echo "Hay cambios locales. Revisá git status --short antes de continuar." >&2; exit 1;
}

echo "[1/7] Sincronizando main..."
git -C "$REPO_DIR" fetch origin
LOCAL="$(git -C "$REPO_DIR" rev-parse HEAD)"
UPSTREAM="$(git -C "$REPO_DIR" rev-parse origin/main)"
if git -C "$REPO_DIR" merge-base --is-ancestor "$LOCAL" "$UPSTREAM"; then
  git -C "$REPO_DIR" merge --ff-only origin/main
elif git -C "$REPO_DIR" merge-base --is-ancestor "$UPSTREAM" "$LOCAL"; then
  echo "La rama local ya contiene origin/main."
else
  echo "La rama local y origin/main divergieron. No se sobrescribirá ningún commit." >&2
  exit 1
fi

TMP="$(mktemp -d "${TMPDIR:-/tmp}/creador-alpha4-clean.XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo "[2/7] Verificando el ZIP..."
ACTUAL_SHA="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
[[ "$ACTUAL_SHA" == "$EXPECTED_SHA" ]] || {
  echo "El SHA-256 no coincide con el paquete auditado." >&2
  echo "Esperado: $EXPECTED_SHA" >&2
  echo "Recibido: $ACTUAL_SHA" >&2
  exit 1
}
unzip -q "$ARCHIVE" -d "$TMP/unpacked"
SRC="$(find "$TMP/unpacked" -mindepth 2 -maxdepth 3 -type f -name main.py -printf '%h\n' | head -n 1)"
[[ -n "$SRC" ]] || { echo "No se encontró main.py dentro del ZIP." >&2; exit 1; }

for required in pyproject.toml requirements.txt core gui profiles tests LICENSE LICENSING-NOTICE.md README.md; do
  [[ -e "$SRC/$required" ]] || { echo "Falta en el paquete: $required" >&2; exit 1; }
done
[[ -f "$SRC/core/projects/manager.py" && -f "$SRC/core/projects/catalog.py" ]] || {
  echo "Falta la gestión de proyectos de Etapa 7; se detiene." >&2; exit 1;
}
grep -q 'version = "3.0.0a4"' "$SRC/pyproject.toml" || {
  echo "La versión del paquete no es 3.0.0-alpha.4." >&2; exit 1;
}
echo "Versión: 3.0.0-alpha.4"
echo "Etapa 7: integrada en main.py y core/projects/."
echo "SHA-256 verificado: $ACTUAL_SHA"

echo "[3/7] Preparando únicamente fuentes y documentación..."
STAGE="$TMP/source"
mkdir -p "$STAGE"
tar -C "$SRC" \
  --exclude='./.git' --exclude='./.venv' --exclude='./venv' \
  --exclude='./__pycache__' --exclude='*/__pycache__' \
  --exclude='*.pyc' --exclude='*.pyo' \
  --exclude='./.pytest_cache' --exclude='*/.pytest_cache' \
  --exclude='./.mypy_cache' --exclude='*/.mypy_cache' \
  --exclude='./.ruff_cache' --exclude='*/.ruff_cache' \
  --exclude='./build' --exclude='./dist' --exclude='*/build' --exclude='*/dist' \
  --exclude='*.egg-info' --exclude='./test-reports' --exclude='./.coverage' \
  --exclude='*.iso' --exclude='*.raw' \
  --exclude='./Creador-Personalizado-Skill-Renovacion-Interfaz.zip' \
  -cf - . | tar -C "$STAGE" -xf -

echo "[4/7] Limpiando el árbol antiguo del repositorio..."
# Conserva .git (historial), pero reemplaza todos los archivos de trabajo por el paquete auditado.
find "$REPO_DIR" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf -- {} +
cp -a "$STAGE/." "$REPO_DIR/"

echo "[5/7] Generando manifiestos nuevos y documentación de publicación..."
printf '%s  %s\n' "$ACTUAL_SHA" "$(basename "$ARCHIVE")" > "$REPO_DIR/FULL-SOURCE-SHA256.txt"
rm -f "$REPO_DIR/SHA256SUMS.txt"
(
  cd "$REPO_DIR"
  find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt
)
cat >> "$REPO_DIR/README.md" <<'README_APPEND'

---

## Estado de publicación del repositorio

La rama principal contiene el código fuente completo de **Creador Personalizado 3.0.0-alpha.4**, incluida la Etapa 7. Para instalaciones nuevas no se debe aplicar ningún overlay.

- Licencia del proyecto: **GPL-3.0-or-later** (archivo LICENSE).
- Avisos de dependencias: LICENSING-NOTICE.md.
- Gestión de proyectos: core/projects/.
- Perfiles editables: profiles/.
- Pruebas automatizadas: tests/.
- Integridad de archivos: SHA256SUMS.txt.
- Integridad del ZIP fuente auditado: FULL-SOURCE-SHA256.txt.

Los parches de migración y scripts temporales de publicación anteriores se retiraron del árbol principal. El historial de Git se conserva.
README_APPEND

echo "[6/7] Comprobando estructura antes del commit..."
for required in main.py core/projects/manager.py core/projects/catalog.py gui/custom_distro.py profiles/terminal-atencion.json tests/test_project_store.py tests/test_project_templates.py LICENSE LICENSING-NOTICE.md SHA256SUMS.txt; do
  [[ -f "$REPO_DIR/$required" ]] || { echo "Falta archivo: $required" >&2; exit 1; }
done
if find "$REPO_DIR" -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.iso' \) -print -quit | grep -q .; then
  echo "Se encontraron artefactos que no deben publicarse." >&2; exit 1
fi
if [[ -e "$REPO_DIR/Etapa7-overlay-GPLv3.tar.gz" || -e "$REPO_DIR/apply-etapa7-overlay.sh" ]]; then
  echo "Quedaron artefactos de migración antiguos." >&2; exit 1
fi

git -C "$REPO_DIR" add -A
git -C "$REPO_DIR" commit -m "release: publish clean complete alpha.4 source with Etapa 7"

echo "[7/7] Publicando en GitHub..."
git -C "$REPO_DIR" push origin main
echo
echo "Publicación completa."
echo "Repositorio: $REMOTE"
echo "Commit: $(git -C "$REPO_DIR" rev-parse HEAD)"
echo "Archivos versionados: $(git -C "$REPO_DIR" ls-files | wc -l)"
