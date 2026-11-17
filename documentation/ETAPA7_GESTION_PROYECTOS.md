# Etapa 7 — Gestión y precarga de proyectos

## Objetivo

Cada proyecto tiene identidad, modalidad, configuración y recursos propios. La plantilla elegida durante su creación precarga valores editables; no comparte estado con otros proyectos.

## Perfiles de precarga

La creación permite elegir los cinco perfiles nominales que ya estaban versionados en `profiles/*.json`. Sus URL, modo de arranque, modalidad multiventana y opciones de firewall/SSH se toman de esos archivos. También se pueden elegir las plantillas generales del catálogo.

| Perfil nominal | Proyecto / motor | Precarga específica |
|---|---|---|---|
| `terminal-atencion` | Terminal de Atención / Kiosco | Chromium, `https://atencion.tallerarg.org`, firewall activo, SSH desactivado y una sola ventana |
| `kiosco-navegador` | Kiosco Navegador / Kiosco | Chromium, `https://www.tallerarg.org`, firewall activo y una sola ventana |
| `kiosco-multiventana` | Kiosco Multiventana / Kiosco | Chromium, `https://www.tallerarg.org`, Sway con segunda aplicación y firewall activo |
| `oficina` | Equipo de Oficina / Fedora Desktop | Firefox, `https://www.libreoffice.org`, GNOME y firewall activo; el perfil original activa SSH |
| `estacion-trabajo` | Estación de Trabajo / Fedora Desktop | Firefox, `https://developer.fedoraproject.org`, Xfce, perfil de desarrollo y operaciones; el perfil original activa SSH y multiventana |
| `kiosk` | Plantilla general Kiosco | Chromium, conectividad Wi-Fi, firewall activo, SSH desactivado y consola virtual bloqueada |
| `office` | Plantilla general Oficina | GNOME, LibreOffice, Firefox y visor PDF |
| `web` | Plantilla general Web | Xfce, Git, Python/pip, Node.js/npm, Nginx, SQLite y curl; SSH desactivado |
| `gaming` | Plantilla general Gaming | KDE Plasma, Mesa/Vulkan, GameMode, PipeWire y SuperTuxKart |
| `security_lab` | Plantilla general Laboratorio | Xfce, Nmap, Wireshark, tcpdump, OpenSCAP y Lynis; uso defensivo y autorizado |
| `custom` | Plantilla general Personalizada | Selección de paquetes vacía y escritorio GNOME |

El nombre que ingresa el usuario se aplica a la identidad del proyecto, nombre ISO, producto y bienvenida. Los valores funcionales del perfil nominal se precargan desde su JSON original. Los paquetes son una selección sugerida. DNF debe resolver disponibilidad y dependencias en los repositorios configurados al construir. Revisar SSH antes de compilar los perfiles Oficina y Estación de Trabajo, ya que sus archivos originales lo dejan habilitado.

## Persistencia

- Directorio predeterminado: `~/.local/share/creador-personalizado/projects/`.
- Cada carpeta contiene `project.json`, `assets/`, `builds/` y `logs/`.
- `project.json` guarda identidad, modalidad, motor, campos del asistente, paquetes/grupos seleccionados y fechas.
- Los recursos locales (imágenes, ejecutables, RPM o carpetas de aplicaciones) se copian a `assets/` para que el proyecto no dependa de la ruta original.
- El guardado del manifiesto es atómico mediante archivo temporal y `os.replace`.
- No se guardan contraseñas, tokens ni secretos. La contraseña inicial Desktop debe ingresarse al momento de compilar.
- La última ruta de proyecto abierto se guarda como preferencia de la aplicación; el resto de la configuración de distribución se guarda en el proyecto activo.

## Uso

1. En el panel principal, pulsar **Nuevo proyecto**.
2. Ingresar un nombre identificador.
3. Elegir una plantilla inicial.
4. Revisar y modificar las opciones precargadas en las seis etapas.
5. Guardar el proyecto. El directorio de salida inicial queda dentro de `builds/`.
6. Para continuar otro día, usar **Abrir proyecto**. Para persistir manualmente, usar **Guardar proyecto**.

La configuración activa se guarda también antes de una compilación y al cerrar la aplicación.

## Compatibilidad y límites

- Las preferencias globales de interfaz (tema y modo de visualización) siguen en QSettings.
- QSettings conserva los campos heredados para facilitar compatibilidad; cuando hay un proyecto activo, su `project.json` es la fuente de verdad.
- Los proyectos anteriores a esta etapa no se convierten automáticamente en proyectos independientes; se mantienen sus preferencias heredadas hasta crear un proyecto nuevo. La migración explícita de proyectos históricos queda pendiente.
- Los perfiles no habilitan servicios de red de forma automática. El perfil Web incluye Nginx como paquete, pero SSH permanece desactivado.
- No se declara probada una compilación ISO ni una GUI real en esta etapa del entorno de desarrollo.
