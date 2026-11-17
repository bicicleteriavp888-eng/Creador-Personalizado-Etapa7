#!/usr/bin/env bash
# Integra el código completo alpha.4 en el repositorio GitHub existente.
# Uso: ./import-full-app.sh /ruta/Creador-Personalizado-3.0.0-alpha.4-Full-GPLv3.zip [directorio-del-clon]
set -Eeuo pipefail

usage() {
  echo "Uso: $0 /ruta/al/paquete-full.zip [directorio-del-repositorio]" >&2
  exit 2
}
[[ $# -ge 1 && $# -le 2 ]] || usage
ARCHIVE="$(realpath "$1")"
REPO_DIR="$(realpath "${2:-$PWD}")"
EXPECTED_REPO="Creador-Personalizado-Etapa7"

[[ -f "$ARCHIVE" ]] || { echo "No existe el paquete: $ARCHIVE" >&2; exit 1; }
[[ -d "$REPO_DIR/.git" ]] || { echo "El destino no es un clon Git: $REPO_DIR" >&2; exit 1; }
command -v unzip >/dev/null || { echo "Falta unzip (sudo dnf install unzip)." >&2; exit 1; }
command -v git >/dev/null || { echo "Falta git (sudo dnf install git)." >&2; exit 1; }

REMOTE="$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null || true)"
[[ "$REMOTE" == *"$EXPECTED_REPO"* ]] || {
  echo "El origin no parece ser el repositorio esperado: $REMOTE" >&2
  exit 1
}
BRANCH="$(git -C "$REPO_DIR" branch --show-current)"
[[ "$BRANCH" == "main" ]] || { echo "Cambiá a main antes de ejecutar (rama actual: $BRANCH)." >&2; exit 1; }
[[ -z "$(git -C "$REPO_DIR" status --porcelain)" ]] || {
  echo "El clon tiene cambios locales. Guardalos o descartalos antes de continuar." >&2
  exit 1
}

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
unzip -q "$ARCHIVE" -d "$TMP"

SRC="$(find "$TMP" -mindepth 2 -maxdepth 3 -type f -name main.py -printf '%h\n' | head -n 1)"
[[ -n "$SRC" && -f "$SRC/core/projects/manager.py" && -f "$SRC/gui/custom_distro.py" ]] || {
  echo "El ZIP no contiene el árbol alpha.4 esperado." >&2
  exit 1
}
[[ -f "$SRC/LICENSE" && -f "$SRC/LICENSING-NOTICE.md" ]] || {
  echo "El ZIP no incluye LICENSE y LICENSING-NOTICE.md." >&2
  exit 1
}

# Preservar la documentación y los metadatos GPL que ya estaban en el repositorio.
PRESERVE="$TMP/preserve"
mkdir -p "$PRESERVE"
for item in LICENSE LICENSING-NOTICE.md SHA256SUMS.txt INFORME_ETAPA7.md CHANGELOG-ETAPA7.md Etapa7-overlay-GPLv3.tar.gz Etapa7-overlay.tar.gz apply-etapa7-overlay.sh; do
  [[ -e "$REPO_DIR/$item" ]] && cp -a "$REPO_DIR/$item" "$PRESERVE/"
done

# Copiar el proyecto completo sin borrar archivos históricos del repositorio.
cp -a "$SRC/." "$REPO_DIR/"
for item in "$PRESERVE"/*; do
  [[ -e "$item" ]] || continue
  cp -a "$item" "$REPO_DIR/"
done

PKG_SHA="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
printf '%s  %s\n' "$PKG_SHA" "$(basename "$ARCHIVE")" > "$REPO_DIR/FULL-SOURCE-SHA256.txt"

cat >> "$REPO_DIR/README.md" <<'README_APPEND'

---

## Publicación en GitHub

Este repositorio contiene el árbol fuente completo de **Creador Personalizado 3.0.0-alpha.4**. La licencia del proyecto es **GPL-3.0-or-later**; consulte `LICENSE` y `LICENSING-NOTICE.md`. Las dependencias de terceros conservan sus propias licencias.

El archivo `Etapa7-overlay-GPLv3.tar.gz` se conserva como parche histórico para instalaciones que parten de alpha.3 / Etapa 6. Para una instalación nueva, utilice el código fuente completo de este repositorio.
README_APPEND

for required in main.py pyproject.toml requirements.txt core/projects/manager.py gui/custom_distro.py profiles/terminal-atencion.json LICENSE LICENSING-NOTICE.md; do
  [[ -f "$REPO_DIR/$required" ]] || { echo "Falta archivo esperado: $required" >&2; exit 1; }
done

git -C "$REPO_DIR" add -A
git -C "$REPO_DIR" commit -m "release: publish complete Creador Personalizado alpha.4 source"
git -C "$REPO_DIR" push origin main

echo "Publicación completada. Repositorio: $REMOTE"
echo "Commit: $(git -C "$REPO_DIR" rev-parse HEAD)"
