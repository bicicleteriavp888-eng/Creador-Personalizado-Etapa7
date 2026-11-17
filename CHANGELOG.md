# Changelog

## 2.5.2 - Arranque Kiosco directo tipo Live, sin LightDM ni contrasena

- Se elimina LightDM + Elephant Greeter del motor Kiosco: no se instala el
  gestor de inicio, no se muestra pantalla de login y no se copia el greeter.
- `kiosk.service` queda como responsable del arranque en `multi-user.target`,
  ejecutando Cage/Sway directamente como `kioskuser` en TTY1. Se quita
  `PAMName=login`: systemd usa esa opción para abrir una sesión PAM e incluye
  la comprobación de cuenta, que puede rechazar una cuenta bloqueada.
- `kioskuser` se crea sin hash de contrasena y se bloquea con `usermod -L`;
  el bloqueo impide autenticacion por contrasena, pero no impide que systemd
  ejecute el servicio con `User=kioskuser`.
- Se elimina la caducidad `chage --lastday 0` y la validacion que exigia un
  hash SHA-512; la autoverificacion exige que la cuenta este bloqueada.
- La GUI ya no ofrece LightDM ni fondo de greeter. La contrasena se oculta y
  deja de ser obligatoria en el perfil Kiosco; sigue siendo obligatoria para
  los perfiles Fedora Desktop.
- El motor Fedora Desktop permanece independiente. Xfce puede seguir usando
  LightDM como gestor de sesiones propio; el cambio afecta solo al motor Kiosco.
- Las opciones antiguas `enable_lightdm` se ignoran para que preferencias
  guardadas de versiones anteriores no vuelvan a activar el login.
- No se genero una ISO ni se verifico el arranque en hardware/QEMU; esa prueba
  queda pendiente en Fedora con una ISO nueva.

## 2.5.1 - Correccion de escritura USB (revalidacion de identidad)

- Se corrigio el chequeo de identidad `MAJ:MIN` antes de ejecutar `dd`: el
  output de `lsblk -dn -o MAJ:MIN` traia espacios de padding y la comparacion
  de strings fallaba aunque el dispositivo fuera el correcto, abortando con
  `ERROR: identidad MAJ:MIN cambiada` (exit 20) sin que `dd` escribiera nada.
- El script generado ahora normaliza el output de `lsblk` con
  `tr -d '[:space:]'` y los mensajes de error incluyen el valor esperado y el
  valor actual.
- El armado del script de escritura se extrajo a
  `USBWriterWorker._build_write_script` para poder testearlo.
- Se completo el mensaje final de exito de la escritura verificada.

## 2.5.0 — Asistente guiado y módulos de hardware (etapas 4 y 5)

- Etapa 4: flujo guiado con selección de tipo de distribución en el paso 1;
  escritorio GNOME/KDE/Xfce en el paso 3 según el motor resuelto;
  validación del tipo de distribución en el paso 1; resumen de configuración
  en el paso 6 antes de compilar.
- El tipo de distribución (`kiosk`, `oficina`, `web`, `gaming`, `security_lab`
  o `custom`) define el motor: `KioskISOBuilder` o `DesktopISOBuilder`.
- El usuario de escritorio se configura en el paso 1 y se aplica al motor
  Desktop; el motor Kiosco conserva `kioskuser`.
- El resumen del paso 6 se refresca desde la configuración recolectada antes de
  validar y compilar.
- Etapa 5: módulos de compatibilidad de hardware en `core/desktops/hardware.py`
  para gráficos, Wi-Fi, touchpad y asistente de conexión Wi-Fi en Live;
  integrados en la resolución de paquetes del motor Desktop solo cuando se
  solicitan.
- No se generó una ISO ni se ejecutó QEMU/hardware físico; las etapas 4 y 5 se
  cierran con pruebas automatizadas.
- Se generó el artefacto de distribución `Creador-kiosk-2.5.0.zip` con el
  contenido del proyecto sin cachés ni archivos temporales.

## 2.4.0 — Motor Fedora Desktop (etapas 1, 2 y 3)

- Nuevo motor independiente en `core/desktops/` con catálogo GNOME/GDM,
  KDE Plasma/SDDM y Xfce/LightDM.
- Generación de Kickstart propia, sin `cage`, `sway`, `seatd`, `kioskuser` ni
  `kiosk.service`; incluye cuenta de escritorio, `graphical.target`, gestor de
  sesión, firewall y SSH opcionales.
- Políticas separadas para nombres de paquetes y grupos comps, con rechazo de
  entradas inválidas, bloqueadas o exclusivas de Kiosco.
- Escritura atómica del Kickstart con permisos `0600` y validación del hash
  SHA-512 antes de insertarlo.
- Etapa 2: consulta de repositorios DNF habilitados, búsqueda de paquetes y
  listado/detalle de grupos comps con `core.repositories.dnf_query`.
- Validación compartida de paquetes, grupos y búsquedas en
  `core.software.policy`, reutilizada por el motor Desktop y la GUI.
- Pantalla Nuevo proyecto con consulta DNF en segundo plano y selección de
  grupos; `extra_groups` se guarda en configuración y perfiles.
- Compatibilidad con DNF5 de Fedora 44: `repoquery --search` fue reemplazado
  por `dnf search --all -- <términos>`.
- Etapa 3: `core/builders/` resuelve `kiosk`/`desktop` y `BuilderWorker` elige
  la clase correspondiente. Si `engine` falta, se conserva Kiosco.
- `DesktopISOBuilder` reutiliza el ciclo de compilación, pero escribe
  `desktop.ks` y `desktop-build.log`, valida el escritorio antes de compilar y
  reemplaza la receta, los paquetes y los mensajes de usuario.
- El perfil del proyecto define el motor: kiosco usa Kiosco; oficina, web,
  gaming, seguridad y personalizado usan Desktop. La elección guiada de
  escritorio y usuario queda para la etapa 4.
- Pruebas nuevas en `tests/test_build_engines.py`, además de las pruebas de
  GUI/validación; el motor Kiosco conserva su comportamiento y sigue
  incluyendo `cage` y `seatd`.
- Se corrigió una aserción obsoleta de la prueba de humo de la GUI que no
  contaba la página `custom_distro` de 2.3.
- No se generó una ISO Desktop ni se ejecutó QEMU o una prueba de hardware
  físico. La compilación real en laboratorio sigue pendiente.

## 2.3.0 — Reestructuración inicial

- Nuevo catálogo de perfiles: kiosco, oficina, web, gaming, laboratorio de
  ciberseguridad y distribución personalizada.
- Nuevo proyecto presenta primero el objetivo y permite cargar paquetes
  sugeridos antes de explorar DNF.
- Validación y deduplicación de paquetes en un módulo independiente.
- Se documentó la arquitectura objetivo y los límites del motor ISO actual.

- Se agregó una casilla opcional para aceptar RPM locales sin firma digital, desactivada por defecto y con confirmación explícita de responsabilidad.
- La excepción solo aplica a RPM realmente sin firma y con digests íntegros.
- Las firmas inválidas, claves desconocidas y paquetes con digests incorrectos continúan bloqueados.
- La preferencia se guarda en la configuración y queda registrada en el historial de compilación (sin guardar secretos).

# Changelog

## 2.1 — 2026-11-13

- Se permite una contraseña inicial corta para `kioskuser` (no vacía, máximo 128 caracteres y sin caracteres de control).
- La contraseña se almacena únicamente como hash SHA-512.
- Se fuerza el cambio en el primer inicio de sesión interactivo mediante `chage --lastday 0`, tanto para el sistema Live como para la instalación derivada; pendiente de validar en Fedora real.
- Se añade `shadow-utils` como dependencia de la imagen.
- Se actualizan los textos de la GUI, validaciones, pruebas y Prompt Maestro.
- El Builder delega ejecución, validación y cancelación de procesos al módulo `core.processes.runner`, manteniendo su API interna compatible.
- Se incorpora historial SQLite automático de compilaciones con configuración redactada y hash SHA-256 de la ISO.
- Se agregan respaldos TAR.GZ con manifiesto, verificación de integridad y restauración segura a destinos vacíos.
- Se refuerza el gestor de perfiles con claves permitidas, escritura atómica e importación/exportación.
- Se exige firma RPM local verificable con una clave de confianza y se bloquean paquetes inseguros de la allowlist.
- Se mejora la inspección ISO con xorriso/isoinfo y se añade laboratorio CLI con reportes y pruebas QEMU BIOS/UEFI opcionales.
- Se agregan metadatos de paquete, lanzador, acceso de escritorio e instalador/desinstalador para Fedora.
- Se amplía el Prompt Maestro con criterios de aceptación y reglas explícitas para no simular pruebas no ejecutadas.
- Se añade `scripts/run_acceptance.sh` para ejecutar la matriz reproducible en Fedora y guardar logs.
- Se documentan límites de validación: sin PySide6 real, ISO de prueba y QEMU no se declara cierre de release.
