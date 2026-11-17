#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Ejecutá: sudo $0 /ruta/al/proyecto" >&2
  exit 1
fi
SOURCE_DIR="$(realpath "${1:-$(dirname "$(dirname "$0")")}" )"
[[ -f "$SOURCE_DIR/main.py" ]] || { echo "No se encuentra main.py en $SOURCE_DIR" >&2; exit 2; }
if ! command -v dnf >/dev/null 2>&1; then
  echo "Este instalador está preparado para Fedora con DNF." >&2; exit 3
fi

dnf install -y python3 python3-pyside6 python3-pytest rsync openssl livecd-tools lorax xorriso syslinux util-linux rpm createrepo_c
install -d -m 0755 /opt/creador-personalizado
# No se copian caches, respaldos ni ISOs previas.
rsync -a --delete --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.venv' \
  --exclude='backups' --exclude='*.iso' "$SOURCE_DIR/" /opt/creador-personalizado/
install -m 0755 /opt/creador-personalizado/scripts/creador-personalizado /usr/bin/creador-personalizado
ln -sfn /usr/bin/creador-personalizado /usr/bin/creador-kiosk  # Alias temporal 2.x
install -m 0644 /opt/creador-personalizado/packaging/creador-personalizado.desktop /usr/share/applications/creador-personalizado.desktop
install -D -m 0644 /opt/creador-personalizado/packaging/creador-personalizado.svg /usr/share/icons/hicolor/scalable/apps/creador-personalizado.svg
install -d -m 0755 /usr/share/doc/creador-personalizado
cp -f /opt/creador-personalizado/README.md /usr/share/doc/creador-personalizado/README.md
cp -rf /opt/creador-personalizado/documentation /usr/share/doc/creador-personalizado/
chmod -R a+rX /opt/creador-personalizado
printf '\nInstalación completada. Iniciá desde el menú o ejecutá: creador-personalizado\n'
printf 'La compilación ISO requiere privilegios y espacio libre suficiente.\n'
