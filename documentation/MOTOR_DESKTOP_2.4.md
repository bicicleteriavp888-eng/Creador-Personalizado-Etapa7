# Motor Fedora Desktop — etapas 1, 2, 3, 4 y 5 (2.5)

## Estado de esta entrega

El **motor Desktop** está implementado y conectado al constructor. La
aplicación elige entre el motor Kiosco y el motor Desktop según el campo
`engine`; si el campo falta, se conserva **Kiosco** como valor predeterminado
para no romper configuraciones anteriores.

- `kiosk`: usa `KioskISOBuilder`, Cage/Sway, `seatd`, `kioskuser` y
  `kiosk.service` sin cambios.
- `desktop`: usa `DesktopISOBuilder`, el Kickstart de `core/desktops/`, una
  cuenta de escritorio convencional y GNOME, KDE Plasma o Xfce.

La etapa 2 agregó la consulta de repositorios, paquetes y grupos DNF. La etapa
3 conecta esa selección con el motor correcto. La etapa 4 incorpora el flujo
guiado en la interfaz: tipo de distribución, escritorio, software, hardware,
identidad, resumen y construcción. La etapa 5 incorpora los módulos de
compatibilidad de hardware para el motor Desktop.

**No se construyó ninguna ISO y no se probó QEMU ni hardware físico.**

## Estructura

```
core/desktops/
├── __init__.py       API pública del motor
├── environments.py   catálogo GNOME/GDM, KDE Plasma/SDDM y Xfce/LightDM
├── hardware.py       módulos de compatibilidad: gráficos, Wi-Fi, touchpad y asistente Live
├── packages.py       paquetes base y políticas separadas de paquetes/grupos
└── kickstart.py      generación y escritura segura del Kickstart

core/builders/
├── __init__.py       API pública de los constructores
├── registry.py       resolución kiosk/desktop y clase del constructor
└── desktop.py        DesktopISOBuilder (ciclo compartido, receta Desktop)

core/software/policy.py            validación compartida de software
core/repositories/dnf_query.py     consultas DNF de solo lectura (etapa 2)
```

## Entornos disponibles

| Clave | Escritorio | Gestor de sesión | Grupo comps | Sesión |
|---|---|---|---|---|
| `gnome` | GNOME | GDM | `@gnome-desktop` | Wayland |
| `kde` | KDE Plasma | SDDM | `@kde-desktop` | Wayland |
| `xfce` | Xfce | LightDM | `@xfce-desktop` | X11 |

Cada entorno declara sus paquetes, su gestor de sesión y su unidad de systemd.
La unidad se habilita tanto con `services --enabled=` como con
`systemctl enable` dentro de `%post`.

## Etapa 3: selección explícita del motor

`core.builders.registry.resolve_build_engine()` aplica este orden:

1. `engine` explícito en la configuración (`kiosk` o `desktop`);
2. `engine` del perfil indicado por `project_type` en
   `core.projects.catalog`;
3. `kiosk` cuando no hay información de motor ni de proyecto.

Los valores desconocidos se rechazan con `BuildEngineError`; no se convierten
en silencio en otro motor. `resolve_builder_class()` devuelve la clase
correspondiente y `BuilderWorker` la usa para construir la ISO.

`gui.collect_config()` envía:

- `engine`, resuelto desde el perfil activo;
- `project_type`, para trazabilidad e historial;
- `desktop_environment`, con `gnome` como valor inicial de esta etapa;
- `desktop_user`, con `fedora` como valor inicial de esta etapa.

El flujo guiado para elegir escritorio, usuario, idioma y teclado es la
**etapa 4**. Mientras tanto, un perfil de oficina, web, gaming, seguridad o
distribución personalizada compila con el motor Desktop y GNOME.

## Etapa 4: flujo guiado en la interfaz

Con la etapa 4 la interfaz incorpora la selección guiada completa:

- **Tipo de distribución** (paso 1): `kiosk`, `oficina`, `web`, `gaming`,
  `security_lab` o `custom`. El tipo define el motor (`kiosk` o `desktop`).
- **Escritorio** (paso 3): GNOME, KDE Plasma o Xfce, con gestor de sesión y tipo
  de sesión; se muestra según el motor resuelto.
- **Software** (paso 3): aplicaciones, paquetes adicionales y grupos comps.
- **Hardware** (paso 2 y opciones avanzadas): resolución, modo de arranque y
  servicios; los módulos de compatibilidad se gestionan en el motor.
- **Identidad** (paso 1): ISO, producto, versión, creador, usuario de escritorio
  y contraseña inicial.
- **Resumen y construcción** (paso 6): resumen de la configuración que se
  refresca antes de validar y compilar.

La validación de tipo de distribución vive en el paso 1; un tipo desconocido se
reporta como error crítico. El usuario de escritorio debe cumplir el patrón de
cuenta del motor Desktop.

## Etapa 5: módulos de hardware

`core/desktops/hardware.py` expone los módulos de compatibilidad:

| Módulo | Contenido |
|---|---|
| `graphics` | Controladores DRI/EGL/OpenGL (`mesa-dri-drivers`, `mesa-libEGL`, `libglvnd-egl`). |
| `wifi` | Red Wi-Fi (`NetworkManager`, `NetworkManager-wifi`, `wpa_supplicant`, `iw`, `linux-firmware`). |
| `touchpad` | Touchpad (`libinput`). |
| `wifi_live_assistant` | Asistente de conexión Wi-Fi en la sesión Live. |

`resolve_desktop_packages()` acepta `hardware_modules` y `wifi_live_assistant`
para incorporar los módulos seleccionados. Ningún módulo de hardware aporta
componentes exclusivos del motor Kiosco.

## Contenido del Kickstart Desktop

### `DesktopISOBuilder`

Reutiliza el ciclo probado de `KioskISOBuilder`:

- preflight de herramientas del host y repositorios;
- preparación de directorios, limpieza de restos y control de espacio;
- hash SHA-512 de la contraseña;
- ejecución y cancelación de `livecd-creator`;
- publicación de la ISO e historial de compilación.

Reemplaza por completo:

- la receta: `desktop.ks` mediante `DesktopKickstartGenerator`;
- el log: `desktop-build.log`;
- la validación previa: `DesktopKickstartGenerator.validate()`;
- los mensajes de cierre: usuario y escritorio reales, sin `kioskuser`;
- la detección de RPM locales del kiosco: el motor Desktop no copia
  aplicaciones locales.

`kiosk.ks` y los métodos de Cage, Sway, LightDM y `kioskuser` no se modifican.
El único cambio compartido es un pequeño gancho de mensajes de cierre que
conserva exactamente los textos anteriores del motor Kiosco.

## Políticas de selección

- **Paquetes:** solo nombres RPM (`[A-Za-z0-9][A-Za-z0-9._+-]*`). Se reutiliza
  la lista de bloqueados de `core.security.allowlist`.
- **Grupos:** política separada. Deben empezar con `@` y, opcionalmente, con
  `@^` para grupos de entorno. Un nombre de grupo no se acepta como paquete y
  un paquete no se acepta como grupo.
- **Componentes de Kiosco:** `cage`, `sway`, `seatd`, `kioskuser`,
  `kiosk.service`, `kiosk-app` y `lightdm-elephant-greeter` se rechazan de
  forma explícita si llegan a la selección del motor Desktop.
- Las entradas inválidas o bloqueadas producen un error; no se descartan en
  silencio.
- Los paquetes adicionales y los grupos adicionales se validan tanto en la GUI
  como antes de escribir el Kickstart.

`DesktopISOBuilder.validate_configuration()` comprueba antes de compilar:

- entorno de escritorio conocido;
- usuario válido según el patrón de cuenta;
- contraseña presente o hash SHA-512 válido;
- nombre de producto, release, arquitectura, idioma, teclado y zona horaria;
- paquetes y grupos adicionales aceptados por la política.

## Etapa 2: selección de software

La etapa 2 se documenta en detalle en
[`SELECCION_SOFTWARE_2.4.md`](SELECCION_SOFTWARE_2.4.md). En resumen:

- `core/software/policy.py` centraliza la validación de paquetes, grupos y
  textos de búsqueda. `core/desktops/packages.py` reutiliza esa política.
- `core/repositories/dnf_query.py` consulta repositorios habilitados, busca
  paquetes, lista grupos comps y obtiene el detalle de un grupo.
- Fedora 44 usa DNF5, donde `repoquery` ya no acepta `--search`; la búsqueda se
  hace con `dnf search --all -- <términos>`.
- Todos los comandos usan listas de argumentos, `shell=False`, `--` antes de la
  búsqueda, tiempo de espera y límites de resultados.
- La GUI ejecuta DNF en un hilo y guarda los grupos elegidos en `extra_groups`.
  El paso 3 valida paquetes inválidos, bloqueados y grupos inválidos.
- Con el motor Desktop, `extra_groups` se aplica en el Kickstart. Con el motor
  Kiosco, la interfaz informa que los grupos no se instalan.

## Contenido del Kickstart Desktop

A diferencia de la receta Kiosco:

- no instala `cage`, `sway` ni `seatd`;
- no crea `kioskuser` ni `kiosk.service`;
- no configura Cage, Sway, Elephant Greeter ni bloqueo de VT;
- crea una cuenta de escritorio convencional en el grupo `wheel`;
- configura `graphical.target`;
- habilita GDM, SDDM o LightDM según el entorno;
- conserva SELinux `enforcing`, firewall y SSH deshabilitado por defecto;
- usa `authselect select local --force`, un perfil presente en Fedora 44;
- permite desactivar el instalador Anaconda;
- escribe el archivo de forma atómica con permisos `0600` porque contiene el
  hash SHA-512.

El hash se valida contra el formato SHA-512 crypt (`$6$...`) antes de
insertarlo. Los nombres de usuario, idioma, teclado, zona horaria, release y
arquitectura también se validan con patrones estrictos.

## Pruebas ejecutadas

Host: Fedora Linux 44, Python 3.14.8, PySide6 6.11.2.

```bash
python -m compileall -q main.py gui core tests
python -m pytest -q
```

Resultado: **213 pruebas aprobadas**, 1 advertencia de pytest
(`PytestRemovedIn10Warning`, no bloqueante). Incluye las 10 pruebas de
`tests/test_build_engines.py`, las 28 de `tests/test_desktops.py`, las 10 de
`tests/test_hardware_modules.py`, las 16 de `tests/test_dnf_query.py`, las 9
de `tests/test_software_policy.py` y las pruebas de GUI/validación de las
etapas 2.4 y 2.5:

- motor Kiosco por defecto cuando `engine` y `project_type` faltan;
- `engine` explícito y resolución desde el perfil;
- rechazo de motores y perfiles desconocidos;
- `BuilderWorker` usa la clase devuelta por el registro;
- `DesktopISOBuilder` usa `desktop.ks` y `desktop-build.log`;
- Kickstart Desktop con GNOME/KDE/Xfce, grupos, paquetes y sin componentes de
  kiosco;
- validación previa de entorno, usuario, contraseña y paquetes;
- mensajes de cierre distintos para Kiosco y Desktop;
- validación del paso 3 según el motor, sin exigir una app de kiosco a Desktop;
- regresión del motor Kiosco: sigue incluyendo `cage` y `seatd`;
- consultas DNF, políticas compartidas, GUI, perfiles e historial existentes.

## Límites explícitos

- **No se generó una ISO Kiosco ni Desktop.** Solo se validaron Kickstarts y
  unidades con pruebas automatizadas.
- **No se ejecutó QEMU ni una prueba BIOS/UEFI.**
- **No se probó hardware físico**, incluida la Dell Vostro 1510.
- No se ejecutó `livecd-creator` en esta etapa. La integración usa el mismo
  ciclo del motor Kiosco, pero la compilación real sigue pendiente de
  laboratorio.
- La disponibilidad de paquetes y grupos depende de los repositorios del host;
  DNF resuelve las dependencias finales al compilar.
- El flujo guiado de selección de escritorio, usuario y hardware es la etapa 4.
  En esta entrega el asistente permite elegir tipo de distribución, escritorio y
  usuario; los módulos de hardware se resuelven en el motor desde la etapa 5.
- La compatibilidad ampliada (gráficos, Wi-Fi, touchpad y asistente Wi-Fi Live)
  está cubierta por módulos del motor desde la etapa 5.

## Próximos pasos

1. Etapa 4 completada en la versión 2.5: flujo guiado con tipo de distribución,
   escritorio, software, hardware, identidad, resumen y construcción.
2. Etapa 5 completada en la versión 2.5: módulos de gráficos, Wi-Fi, touchpad y
   asistente Wi-Fi Live.
3. Laboratorio: compilar una ISO Desktop en Fedora 44 y probar BIOS/UEFI en
   QEMU antes de declarar compatibilidad con hardware físico.
