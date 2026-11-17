#!/usr/bin/env bash
set -euo pipefail
if [[ "${EUID}" -ne 0 ]]; then echo "Ejecutá con sudo: $0" >&2; exit 1; fi
rm -f /usr/bin/creador-personalizado /usr/share/applications/creador-personalizado.desktop /usr/share/icons/hicolor/scalable/apps/creador-personalizado.svg
rm -f /usr/bin/creador-kiosk /usr/share/applications/creador-kiosk.desktop
rm -rf /opt/creador-personalizado /opt/creador-kiosk /usr/share/doc/creador-personalizado /usr/share/doc/creador-kiosk
printf 'Creador Personalizado fue desinstalado. Se conservaron los datos del usuario.\n'
