# Creador Personalizado

**Constructor de distribuciones Fedora · Tu distribución, tus reglas.**

Creador Personalizado permite diseñar imágenes Fedora de escritorio y sistemas
Kiosco desde una interfaz gráfica. El nombre nuevo amplía la identidad del
producto; los nombres internos históricos se conservan durante la transición
3.0 para mantener compatibilidad con proyectos, rutas y herramientas previas.

**Versión actual:** 3.0.0-alpha.4. Esta entrega agrega gestión de proyectos
independientes y precargas editables para los perfiles nominales Terminal de Atención, Kiosco
Navegador, Kiosco Multiventana, Equipo de Oficina y Estación de Trabajo, además
de plantillas generales para Kiosco, Oficina, Web, Gaming, Laboratorio y Personalizado. Cada proyecto guarda
su configuración y recursos en su propia carpeta; la contraseña nunca se persiste.

**Creador Personalizado 2.5.5 (motor Desktop y Kiosco)** es una aplicación de escritorio en Python/PySide6 para
configurar y construir imágenes ISO basadas en Fedora 44. La versión 2.5
incorpora un motor Fedora Desktop independiente en `core/desktops/` con GNOME,
KDE Plasma y Xfce, conectado al constructor mediante `core/builders/`, la
selección de software con repositorios, paquetes y grupos DNF, el flujo guiado
en la interfaz y los módulos de compatibilidad de hardware. El motor Kiosco
sigue disponible con Wayland (Cage o Sway), `seatd`, `kioskuser` y
`kiosk.service`, y las configuraciones 2.x sin motor explícito todavía se interpretan como Kiosco por compatibilidad. Los proyectos nuevos deben elegir modalidad; esta regla se endurecerá con el migrador 3.0.

La interfaz 2.0 incorpora un panel principal con datos reales del entorno,
navegación lateral, un asistente de seis pasos con validación y ayuda
contextual, modos Simple/Avanzado y temas claro/oscuro. El asistente permite
elegir el tipo de distribución, el escritorio (GNOME/KDE/Xfce), el software,
el hardware, la identidad, el resumen y la construcción de la ISO.

## Funciones

- Panel principal con última compilación, ruta, tamaño, fecha, SHA-256,
  espacio libre, dependencias, servicios del host, configuración activa,
  tareas pendientes y últimos errores.
- Asistente de seis pasos: identidad, apariencia, software, instalador,
  seguridad y compilación/validación. Incluye resumen de configuración antes
  de compilar.
- Validación por etapa y validación completa antes de compilar. El botón
  `Validar paso` informa los errores críticos sin avanzar y `Siguiente`
  bloquea el avance mientras existan.
- Proyectos independientes: crear, abrir y guardar; cada uno conserva su modalidad, paquetes, opciones, recursos y destino de compilación en su propia carpeta.
- Precargas nominales: Terminal de Atención, Kiosco Navegador, Kiosco Multiventana, Equipo de Oficina y Estación de Trabajo; también hay seis plantillas generales.
- Guardado y restauración de la configuración; la contraseña nunca se guarda.
- Modo Simple con las opciones esenciales y modo Avanzado con parámetros
  técnicos, multiventana, privilegios e imágenes.
- Temas claro y oscuro con preferencia persistente.
- Kiosco con Chromium, Firefox, Firefox es-AR o una aplicación local
  (binario, script, carpeta o RPM).
- Modo multiventana con Sway y dos aplicaciones.
- Personalización de marca, resolución y Plymouth; la imagen elegida se muestra también en los menús BIOS/Legacy y UEFI. El motor Kiosco arranca
  directamente en modo Live, sin LightDM, pantalla de login ni contraseña.
- Gestor inicial de software: búsqueda de paquetes, selección de grupos Comps, consulta del contenido obligatorio/predeterminado/opcional y simulación DNF5 con `--assumeno` para revisar dependencias y conflictos sin modificar el anfitrión. Los metapaquetes RPM se seleccionan como paquetes normales; DNF5 resuelve sus dependencias. La compilación vuelve a resolver dentro del entorno destino.
- Instalador Anaconda opcional.
- Generación de ISO con progreso, registros y cancelación en segundo plano.
- Escritura de ISO a USB desde la aplicación, con detección de dispositivos,
  confirmación explícita y verificación de lectura posterior.
- Historial SQLite de compilaciones con estado, configuración redactada,
  ubicación de ISO, SHA-256, log y error final.
- Respaldo de proyecto en TAR.GZ con manifiesto SHA-256, verificación previa
  a restaurar y restauración únicamente a un destino vacío.
- Importación/exportación segura de perfiles JSON y protección contra rutas
  manipuladas.
- Validador de ISO CLI con informes JSON/TXT e intento opcional de arranque
  QEMU BIOS/UEFI (requiere QEMU y firmware OVMF).

## Perfiles de Nuevo proyecto (2.3)

La pantalla Nuevo proyecto permite iniciar una selección para kiosco, oficina,
web/servicios, gaming, laboratorio de ciberseguridad o una distribución libre.
Los paquetes sugeridos se consultan/resuelven contra los repositorios DNF
configurados. También permite consultar repositorios habilitados, buscar
paquetes por nombre o descripción y elegir grupos comps.

Desde la etapa 3, el perfil define el motor de imagen:

- kiosco → `KioskISOBuilder` con Cage/Sway;
- oficina, web, gaming, seguridad y distribución personalizada →
  `DesktopISOBuilder`.

Mientras no se elija un perfil Desktop, la aplicación conserva el motor Kiosco.
Con el asistente guiado (etapa 4) el usuario puede elegir el tipo de
distribución y, con el motor Desktop, el escritorio GNOME, KDE Plasma o Xfce.

## Motor Fedora Desktop (2.5, etapas 1, 2, 3, 4 y 5)

El paquete `core/desktops/` contiene un motor independiente que ya genera el
Kickstart de GNOME/GDM, KDE Plasma/SDDM y Xfce/LightDM:

```python
from core.desktops import DesktopKickstartGenerator

generator = DesktopKickstartGenerator({
    "desktop_environment": "gnome",
    "desktop_user": "tester",
    "password": "clave-inicial",
    "release": "44",
})
generator.write("desktop.ks")
```

La receta no incluye `cage`, `sway`, `seatd`, `kioskuser` ni `kiosk.service`.
Valida por separado paquetes y grupos, rechaza entradas bloqueadas o inválidas y
escribe el archivo con permisos `0600` porque contiene el hash SHA-512.

La etapa 2 agrega consultas DNF de solo lectura, sin shell y con validación de
entradas:

```python
from core.repositories.dnf_query import DnfQuery

dnf = DnfQuery()
repositorios = dnf.list_enabled_repositories()
paquetes = dnf.search_packages("editor de imágenes", limit=20)
grupos = dnf.list_groups()
```

Fedora 44 usa DNF5, donde `repoquery` ya no acepta `--search`; la búsqueda se
hace con `dnf search --all -- <términos>`. Los grupos elegidos se guardan en
`extra_groups`: el motor Desktop los instala y el motor Kiosco informa que no
los aplica.

La etapa 3 conecta los motores al constructor:

```python
from core.builders import resolve_builder_class

builder_class = resolve_builder_class({"engine": "desktop"})
builder = builder_class(config)
resultado = builder.build()
```

`resolve_build_engine()` usa `engine`, luego el `engine` del `project_type` y,
si no hay información, `kiosk`. `DesktopISOBuilder` reutiliza el ciclo de
`KioskISOBuilder` pero escribe `desktop.ks` y `desktop-build.log`, valida la
configuración de escritorio y no incluye componentes de kiosco.

Con la etapa 4, el asistente permite elegir el tipo de distribución, el
escritorio y el usuario de escritorio; el paso 6 muestra el resumen antes de
compilar.

Con la etapa 5, los módulos de hardware (gráficos, Wi-Fi, touchpad y asistente
de conexión Wi-Fi en Live) se resuelven en `core/desktops/hardware.py` y se
incorporan a la selección de paquetes del motor Desktop solo cuando se
solicitan.

**Límite de la etapa:** no se generó una ISO Desktop ni se ejecutó QEMU o una
prueba de hardware. La arquitectura, las pruebas y el plan de integración están
en [`documentation/MOTOR_DESKTOP_2.4.md`](documentation/MOTOR_DESKTOP_2.4.md);
la selección de software se detalla en
[`documentation/SELECCION_SOFTWARE_2.4.md`](documentation/SELECCION_SOFTWARE_2.4.md).

## Seguridad predeterminada

- SELinux configurado en modo `enforcing`.
- Firewall habilitado por defecto.
- SSH deshabilitado por defecto; se instala y habilita únicamente si se
  selecciona administración remota.
- Si SSH se habilita, la autenticación por contraseña permanece desactivada
  por defecto. Se recomienda configurar claves públicas antes del despliegue.
- El motor Kiosco no asigna contraseña a `kioskuser`: la cuenta queda bloqueada para autenticación por contraseña y `kiosk.service` inicia la aplicación directamente. No se muestra una pantalla de login. Los perfiles Fedora Desktop conservan contraseña para el usuario de escritorio.
- `sudo` solicita contraseña por defecto; `NOPASSWD` es una opción explícita.
- Chromium conserva su sandbox por defecto.
- El Kickstart del motor Desktop contiene un hash SHA-512, no la contraseña en texto plano. El Kickstart Kiosco no contiene hash de contraseña.
- Los RPM locales requieren firma válida y clave de confianza por defecto. En modo Avanzado se puede aceptar explícitamente un RPM sin firma, bajo responsabilidad del usuario y solo si sus digests son correctos; las firmas inválidas, claves desconocidas y paquetes corruptos siguen rechazándose. Los paquetes bloqueados por política (telnet, rsh, NIS/TFTP, etc.) se rechazan siempre.
- Antes de escribir un USB se revalida la identidad MAJ:MIN, tamaño, modelo y
  número de serie disponibles; la escritura se compara byte a byte con la ISO.

> La seguridad final también depende de las opciones elegidas al configurar
> la imagen y de la validación del hardware donde se despliegue.

## Requisitos del host

Fedora 44 (o una versión compatible que disponga de las mismas herramientas):

```bash
sudo dnf install livecd-tools openssl createrepo_c util-linux
sudo dnf install syslinux xorriso lorax
sudo dnf install python3-pyside6 python3-pytest
```

- `syslinux` aporta `isolinux.bin`, `isohdpfx.bin` y `vesamenu.c32`.
- `xorriso` aporta `xorrisofs` para la ISO híbrida.
- `lorax` aporta `mkefiboot` para la imagen EFI.

Antes de compilar, la aplicación comprueba estas herramientas y los activos de
syslinux, además de `livecd-creator`, `openssl`, `rpm` y `createrepo_c` cuando
corresponda. Si falta algo, detiene el build y muestra el paquete sugerido en
lugar de fallar a mitad del proceso.

Alternativamente, en un entorno Python apropiado:

```bash
python -m pip install -r requirements.txt
```

La compilación requiere al menos 12 GiB libres en el volumen de trabajo; el
proceso se detiene si el espacio es insuficiente o el destino está en `tmpfs`.
También requiere conectividad con los repositorios Fedora. Los RPM locales requieren `rpm` y
`createrepo_c`.

## Inicio

Desde la carpeta del proyecto:

```bash
python main.py
```

La aplicación intenta usar `sudo -n` cuando ya hay autorización disponible y,
si corresponde, `pkexec` para solicitar autorización mediante Polkit. No
requiere ejecutar toda la interfaz como root.

## Pruebas

```bash
python -m compileall -q .
python -m pytest -q
```

La suite incluye pruebas del backend, de la validación por etapas y de humo
de la interfaz con Qt `offscreen`. Para probar la generación real de ISO se
necesita un host Fedora preparado, privilegios administrativos, repositorios
disponibles y espacio suficiente. Las pruebas unitarias no sustituyen una
compilación y un arranque de prueba (BIOS/UEFI) en hardware o máquinas
virtuales.

## Historial y respaldos

El backend registra automáticamente cada compilación en
`~/.local/share/creador-personalizado/history.sqlite3`. Las claves sensibles se
redactan antes de persistir la configuración. El registro distingue
`RUNNING`, `GENERATED`, `FAILED` y `CANCELLED`; una ISO generada no se marca
como validada ni probada automáticamente. Consultar el historial:

```bash
python scripts/build_history.py list --limit 50
python scripts/build_history.py show ID_DE_COMPILACION
```

Crear, verificar y restaurar un respaldo (la restauración exige un destino
vacío):

```bash
python scripts/backup_project.py create . --backup-dir ./backups --label pre-cambios
python scripts/backup_project.py verify ./backups/ARCHIVO.tar.gz
python scripts/backup_project.py restore ./backups/ARCHIVO.tar.gz /ruta/destino-vacio
```

## Laboratorio ISO

```bash
python scripts/validate_iso.py /ruta/imagen.iso --report-dir ./laboratory-reports
python scripts/validate_iso.py /ruta/imagen.iso --qemu --timeout 90
```

El modo QEMU usa `-snapshot`, `-nic none`, una copia temporal de OVMF_VARS y no conecta discos físicos del host. En Fedora, instala opcionalmente `qemu-system-x86-core` y `edk2-ovmf` para las pruebas BIOS/UEFI. Un QEMU que
permanece activo hasta el timeout solo demuestra que el proceso pudo arrancar;
la detección de marcadores de consola y la inspección visual siguen siendo
necesarias para certificar el inicio del sistema. UEFI requiere OVMF instalado.

## Instalación en Fedora

Desde el directorio del proyecto:

```bash
sudo bash packaging/install-fedora.sh "$PWD"
```

El instalador instala dependencias de Fedora, copia el proyecto a
`/opt/creador-personalizado` y registra el lanzador de escritorio. La compilación de
ISOs sigue requiriendo red, privilegios y al menos 12 GiB libres.

## Variables de entorno

| Variable | Descripción | Predeterminado |
|---|---|---|
| `KIOSK_MIRROR` | Mirror fijo con layout Fedora (`releases/` y `updates/`). | Sin definir |
| `KIOSK_MIRRORLIST` | URL del mirrorlist Fedora. | Mirrorlist oficial |
| `KIOSK_BUILD_ROOT` | Raíz del árbol temporal de compilación. | `/var/tmp/creador-personalizado` |
| `KIOSK_CACHE_DIR` | Caché RPM entre compilaciones. | `/var/cache/creador-personalizado` |

## Estructura

```text
main.py             Ventana principal, panel, asistente, workers y preferencias
gui/                Páginas del asistente y componentes de interfaz
  components.py     Tarjetas de estado, encabezados y ayuda contextual
  layouts.py        Registro de páginas con scroll uniforme
  status.py         Estado real del host, servicios y hash en segundo plano
  validation.py     Validación independiente de las seis etapas
  theme.py          Temas claro y oscuro
  tab_security.py   Paso 5: seguridad y servicios
core/builder.py     Kickstart y ejecución de livecd-creator
core/desktops/      Motor Fedora Desktop independiente (GNOME/KDE/Xfce)
core/software/      Políticas compartidas de selección de software
core/repositories/  Repositorios Fedora, consultas DNF y paquetes
core/usb.py         Detección y escritura segura de USB
core/history/       Historial de builds y respaldos verificables
scripts/            Laboratorio ISO y herramientas de backup
packaging/          Instalador Fedora y entrada de escritorio
core/privileges.py  Integración sudo / pkexec
tests/              Pruebas unitarias, de validación y de humo de GUI
documentation/      Auditoría técnica y documentos de la versión 2.0
mi_sitio/           Plantilla de sitio estático independiente
```

## Documentación de cambios

Consultar [`INFORME_ACTUALIZACION.md`](INFORME_ACTUALIZACION.md) para el
resumen de cambios, decisiones de seguridad, validaciones realizadas y
limitaciones pendientes.

La auditoría técnica de la versión 2.0, con los hallazgos, correcciones
aplicadas y resultados reales de cada etapa, está en
[`documentation/AUDITORIA_2.0.md`](documentation/AUDITORIA_2.0.md).

## Desarrollo y seguimiento 2.1

- Prompt de trabajo: `Prompt_Maestro_Creador Personalizado_2.1.txt`
- Tablero de etapas y registro de sesiones: `documentation/SEGUIMIENTO_ETAPAS_2.1.md`
- Auditoría técnica de base: `documentation/AUDITORIA_2.0.md`

Los estados del tablero distinguen implementación de validación. No se debe
marcar una etapa como validada sin pruebas ejecutadas y evidencia registrada.

**Inicio del motor Kiosco:** el usuario técnico `kioskuser` no tiene una
contraseña utilizable. El servicio `kiosk.service` inicia Cage/Sway directamente
en TTY1 desde `multi-user.target`; LightDM y el greeter no forman parte de la
ISO Kiosco. El motor Fedora Desktop conserva sus gestores de sesión propios.

## Prueba de aceptación en Fedora

Después de instalar dependencias y desde el proyecto:

```bash
bash scripts/run_acceptance.sh
```

Para validar una ISO y probar arranque QEMU BIOS/UEFI:

```bash
bash scripts/run_acceptance.sh /ruta/a/creador-personalizado.iso --boot-mode dual --qemu --timeout 90
```

Los logs se guardan en `test-reports/` para compartir el resultado de la prueba.

## Gestión de proyectos (alpha.4)

Los proyectos se guardan por defecto en `~/.local/share/creador-personalizado/projects/`. Cada proyecto tiene `project.json`, `assets/`, `builds/` y `logs/`. Desde el panel principal se puede crear un proyecto indicando su nombre y plantilla, abrir uno existente o guardar el activo. Las imágenes y aplicaciones locales seleccionadas se copian a los recursos del proyecto.

Ver `documentation/ETAPA7_GESTION_PROYECTOS.md` para el detalle de las precargas y sus límites.

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
