# Auditoría técnica — Creador-kiosk 2.0

**Proyecto:** TallerArg · Creador-kiosk  
**Fecha:** 13 de noviembre de 2026  
**Alcance:** auditoría del código fuente real en `/home/sergio/Descargas/Creador-kiosk`  
**Copia de seguridad previa:** `backups/pre-2.0-20261113-120424.tar.gz`  
**Objetivo:** establecer el estado real antes de reorganizar el proyecto, conforme a la ETAPA 1 del prompt maestro.

---

## 0. Método y entorno verificado

La auditoría no se limitó a leer archivos. Se ejecutaron comprobaciones sobre el host:

| Comprobación | Resultado real |
|---|---|
| Sistema anfitrión | Fedora Linux 44 (KDE Plasma Desktop) |
| Python | 3.14.8 |
| PySide6 | 6.11.2 |
| `livecd-creator` | `/usr/bin/livecd-creator` (livecd-tools 31.0-20.fc44) |
| `lorax` / `livemedia-creator` | presentes (`/usr/bin/lorax`, `/usr/bin/livemedia-creator`) |
| `xorriso` / `isoinfo` | presentes |
| `qemu-system-x86_64` | presente |
| `mkefiboot` | `/usr/bin/mkefiboot` (lorax) |
| `syslinux` | 6.04 instalado (`isolinux.bin`, `isohdpfx.bin`, `vesamenu.c32`) |
| `sudo -n` | **no disponible** (pide contraseña) |
| Espacio libre | 88 GiB en `/`, 77 GiB en `/home` |
| Memoria | 3 GiB (suficiente para pruebas, limitada para compilaciones largas) |
| `python -m compileall -q .` | correcto |
| `python -m pytest -q` | **53 pruebas aprobadas** |
| Apertura de la GUI con `QT_QPA_PLATFORM=offscreen` | correcta; 6 pestañas legibles |
| Generación de Kickstart (dual + Chromium + multiventana) | 13 754 bytes; 2 secciones `%post`; `sh -n` correcto |
| Permisos del Kickstart generado | `0600` (correcto) |
| Existencia de los 59 paquetes referenciados en repos Fedora 44 | verificada con `dnf` (incluye `noarch`) |

**Lo que NO se ejecutó:** no se compiló una ISO completa ni se arrancó BIOS/UEFI. Por lo tanto, esta auditoría no afirma que la ISO funcione; solo describe y valida el código y las herramientas.

---

## 1. Diagnóstico de la arquitectura

### 1.1 Estructura actual

```text
Creador-kiosk/
├── main.py                (525 líneas) Ventana, worker, QSettings, validación y orquestación
├── core/
│   ├── builder.py         (2291 líneas) Backend completo: Kickstart, procesos, ISO
│   ├── privileges.py      (47 líneas) sudo -n / pkexec
│   └── usb.py             (356 líneas) lsblk + dd + verificación
├── gui/
│   ├── theme.py           Tema claro único
│   ├── layouts.py         Scroll y márgenes de pestañas
│   ├── images.py          Selección/conversión de imágenes
│   └── tab_*.py           6 pestañas (meta, estética, software, instalador, build, USB)
├── tests/                 53 pruebas de `builder.py` y `usb.py`
├── vendor/                LightDM Elephant Greeter (MIT)
├── mi_sitio/              Sitio estático NO relacionado con la aplicación
├── builder_parte2.txt     Volcado de código fuente (duplicado)
├── codigo_completo.txt    Volcado de código fuente (270 KB, duplicado)
├── INFORME.txt            Documentación histórica (previo a la versión actual)
├── INFORME_ACTUALIZACION.md
├── INFORME_AJUSTE_LAYOUT.md
└── README.md
```

### 1.2 Métricas

| Módulo | Líneas | Métodos/funciones | Observación |
|---|---:|---:|---|
| `core/builder.py` | 2291 | 50 | Monolito: 10 responsabilidades distintas |
| `main.py` | 525 | 14 | Ventana + worker + persistencia + validación |
| `core/usb.py` | 356 | 9 | Correcto en seguridad, acoplado a `sh -c` |
| GUI (`gui/`) | 1057 | — | 6 pestañas planas, sin navegación lateral |
| Pruebas | 1000 | 53 | Solo backend y USB |

### 1.3 Problemas estructurales

1. **`core/builder.py` es un monolito.** Contiene, sin separación:
   detección de privilegios, preparación de directorios, inspección de RPM,
   resolución de aplicaciones, generación completa de Kickstart (particionado,
   paquetes, `%post`, systemd, Sway, Cage, LightDM, Plymouth, Anaconda),
   ejecución de procesos, cancelación, localización y publicación de la ISO.
   Esto impide validar Kickstart de forma aislada, reutilizar el motor en una CLI
   o probar etapas sin instanciar todo el constructor.

2. **El núcleo depende de PySide6.** `core/builder.py` importa
   `QObject`/`Signal`. La lógica de negocio no puede ejecutarse sin Qt ni
   publicar eventos a otro consumidor (CLI, servidor, pruebas de integración).

3. **Validación duplicada y divergente.** `main.py` valida el nombre del
   producto permitiendo `$`, comillas y barras invertidas; `builder.py` los
   rechaza después. El usuario puede completar el asistente y recibir el error
   recién al compilar. No existe una capa única de validación compartida.

4. **No hay modelo de configuración versionado.** La configuración es un
   `dict` sin esquema, versión ni migración. No hay perfiles ni import/export.

5. **Progreso por heurística de texto.** `_track_phase()` asigna 45 %, 75 % y
   88 % al detectar cadenas en el log. No hay etapas formales, porcentaje real,
   tiempo por etapa ni estado recuperable. El prompt prohíbe simular avances.

6. **Registro no estructurado.** Los logs se emiten como texto por señal y se
   escriben en `kiosk-build.log`, que se borra en cada compilación. No hay
   historial, niveles, `traceback` ni correlación con un ID de build.

7. **Sin separación entre generación y verificación.** No existe laboratorio de
   ISO, verificación estructural, SHA-256, informe ni historial. El único
   resultado verificable es el `returncode` de `livecd-creator`.

8. **Errores silenciosos en `%post`.** `livecd-creator` ignora los fallos de los
   scripts `%post` salvo que se use `--erroronfail`. El Kickstart generado no lo
   usa; una ISO puede "terminar bien" aunque `useradd`, systemd o el entorno
   gráfico no se hayan configurado.

9. **El árbol de trabajo se reutiliza.** `KIOSK_BUILD_ROOT` es fijo
   (`/var/tmp/creador-kiosk/build`). Dos compilaciones simultáneas o un cierre
   abrupto pueden mezclar restos. No hay bloqueo (lockfile) ni ID de build.

10. **Documentación insuficiente.** Solo existe `README.md` y tres informes
    históricos. Faltan `INSTALL`, `USER_GUIDE`, `ARCHITECTURE`, `SECURITY`,
    `BUILD_PROCESS`, `ISO_LAB` y `CHANGELOG`.

---

## 2. Inventario de funcionalidades existentes

| # | Funcionalidad | Estado | Evidencia / módulo |
|---|---|---|---|
| 1 | Generación de Kickstart dinámico | **Funcional** | `_generate_kickstart()`, probado |
| 2 | Kiosco Chromium / Firefox / Firefox es-AR | **Funcional** | `_resolve_app()` |
| 3 | Aplicación local (binario, script, carpeta, RPM) | **Funcional con limitaciones** | `_resolve_app()`, `_resolve_rpm_app()` |
| 4 | Multiventana Sway con dos apps | **Funcional** | `_sway_service_section()` |
| 5 | Kiosco Cage de una app | **Funcional** | `_cage_service_section()` |
| 6 | Plymouth personalizado y sincronización de initramfs | **Funcional** | `_plymouth_section()`, `_plymouth_sync_section()` |
| 7 | LightDM + Elephant Greeter | **Funcional (no probado en ISO)** | `_greeter_section()`, `vendor/` |
| 8 | Instalador Anaconda + entrada de arranque | **Funcional con riesgo EFI** | `_installer_section()`, `_installer_boot_section()` |
| 9 | Firewall, SSH, sudo, SELinux enforcing | **Funcional** | `_post_base()` |
| 10 | Bloqueo de consolas virtuales | **Funcional** | `_vt_section()` |
| 11 | Contraseña como hash SHA-512, archivo KS `0600` | **Funcional** | `_password_hash()` |
| 12 | Compilación en segundo plano (QThread) | **Funcional** | `main.py: BuilderWorker` |
| 13 | Cancelación con señales al grupo de procesos | **Funcional** | `_terminate_process_tree()` |
| 14 | Limpieza de restos de compilaciones previas | **Parcial** | `_cleanup_stale_builds()` |
| 15 | Detección de USB y escritura con `dd` | **Funcional** | `core/usb.py` |
| 16 | Confirmación y revalidación del USB (MAJ:MIN, tamaño, serie) | **Funcional y destacable** | `_validate_device_snapshot()` |
| 17 | Verificación byte a byte tras `dd` (`cmp`) | **Funcional** | `usb.py:_write()` |
| 18 | Persistencia de preferencias (QSettings) | **Funcional** | `main.py:_load/_save_settings` |
| 19 | Validación de paquetes adicionales | **Parcial** | Solo sintaxis, no existencia en repos |
| 20 | Diagnóstico del entorno | **Inexistente** | Solo `_preflight()` mínimo |
| 21 | Perfiles reutilizables | **Inexistente** | — |
| 22 | Catálogo de aplicaciones | **Inexistente** | — |
| 23 | Módulo Kickstart independiente + validador | **Inexistente** | Todo embebido en `builder.py` |
| 24 | Laboratorio de ISO / estados GENERADA-VALIDADA-PROBADA | **Inexistente** | — |
| 25 | SHA-256 de la ISO y verificación de integridad | **Inexistente** | — |
| 26 | Historial de compilaciones | **Inexistente** | — |
| 27 | Copias de seguridad / exportación | **Inexistente** | — |
| 28 | Informes TXT/HTML/PDF | **Inexistente** | — |
| 29 | Pruebas QEMU BIOS/UEFI | **Inexistente** | — |
| 30 | Modo Simple / Avanzado | **Inexistente** | — |
| 31 | Asistente de 6 etapas con navegación lateral | **Inexistente** | Solo pestañas planas |
| 32 | Tema claro/oscuro | **Parcial** | Solo tema claro |
| 33 | Panel principal con estado real | **Inexistente** | — |
| 34 | Empaquetado / instalador | **Inexistente** | Sin `pyproject.toml` ni `.spec` |
| 35 | Registro estructurado y trazabilidad | **Inexistente** | — |

---

## 3. Errores detectados

### 3.1 Críticos (afectan el resultado o la seguridad)

| ID | Error | Archivo / línea | Impacto | Evidencia |
|---|---|---|---|---|
| C-01 | Falta el paquete `nm-connection-editor` en el modo multiventana | `core/builder.py:1045-1058` | `Alt+9` intenta ejecutar `/usr/bin/nm-connection-editor`, que no existe en la ISO; el atajo de red WiFi falla | `dnf provides /usr/bin/nm-connection-editor` → paquete **separado** `nm-connection-editor`; el generador solo instala `network-manager-applet` |
| C-02 | La entrada de instalador agregada a `EFI/BOOT/grub.cfg` usa `linux`/`initrd` aunque el archivo original usa `linuxefi`/`initrdefi` | `core/builder.py:1419-1435` | En UEFI (especialmente con Secure Boot) la entrada "Instalar en disco" puede no arrancar | `imgcreate/live.py:767-770` genera `linuxefi`/`initrdefi`; el script extrae el comando pero vuelve a escribir `linux`/`initrd` |
| C-03 | Los `%post` no usan `--erroronfail` y no verifican el resultado | `core/builder.py:981-983` | Una ISO puede marcarse como exitosa aunque falle `useradd`, `systemctl enable`, el entorno gráfico o el instalador | `imgcreate/creator.py:769-771` solo registra un warning si `errorOnFail` es falso; `pykickstart` confirma que el flag existe |
| C-04 | El `preflight` no comprueba `mkefiboot`, `xorrisofs` ni los archivos de `syslinux` | `core/builder.py:216-229` | En un host con solo `livecd-tools` el build puede fallar tarde o generar una ISO sin arranque EFI | `rpm -qR livecd-tools` y `python3-imgcreate` no los exigen; el código de `imgcreate` los invoca en tiempo de ejecución |
| C-05 | Validación del nombre de producto divergente entre GUI y backend | `main.py:188-199` vs `core/builder.py:1286-1292` | El asistente acepta valores que el backend rechaza minutos después, al compilar | La GUI solo rechaza caracteres de control; el backend además rechaza `"`, `\` y `$` |

### 3.2 Altos (fiabilidad, mantenibilidad o requisitos incumplidos)

| ID | Error | Archivo | Impacto |
|---|---|---|---|
| A-01 | Progreso simulado por coincidencias de texto | `core/builder.py:2027-2034` | No representa etapas reales ni permite recuperación; incumple el punto 4 del prompt |
| A-02 | Sin SHA-256, informe ni historial tras la compilación | `core/builder.py:2206-2240` | No se puede demostrar integridad ni comparar builds |
| A-03 | Sin verificación de la ISO (estructura, BIOS/UEFI, Kickstart, paquetes) | — | No existe el estado VALIDADA y no se distingue de GENERADA |
| A-04 | Sin pruebas virtuales QEMU | — | No existe el estado PROBADA |
| A-05 | Sin perfiles ni catálogo de aplicaciones | — | No se cumplen los puntos 5 y 6 del prompt |
| A-06 | Sin diagnóstico independiente del entorno | `_preflight()` mínimo | No se clasifican resultados en correcto/advertencia/error/no disponible |
| A-07 | Sin validación de paquetes contra repositorios antes de compilar | `_package_lines()` | Un nombre inexistente falla tras descargar metadatos, no antes |
| A-08 | Sin bloqueo de compilación ni ID de build | `KIOSK_BUILD_ROOT` fijo | Riesgo de colisión entre builds y de restos mezclados |
| A-09 | `core/` acoplado a PySide6 | `core/builder.py:20`, `core/usb.py:12` | Impide CLI, pruebas sin Qt y separación UI/lógica |
| A-10 | Sin verificación de firmas de RPM ni lista de permitidos/bloqueados | `_resolve_rpm_app()` | Se instala cualquier RPM local sin validar procedencia |
| A-11 | Sin cancelación de escritura USB | `core/usb.py` | `dd`/`cmp` no se pueden abortar desde la GUI |
| A-12 | Uso de `sh -c` para la operación privilegiada de USB | `core/usb.py:240-288` | Contradice la regla de preferir `subprocess` con argumentos separados; el riesgo se mitiga con `shlex.quote`, pero no es la arquitectura pedida |
| A-13 | No hay modo "solo BIOS"; "Solo UEFI" no es exclusivo | `core/builder.py:872`, `main.py:34-40` | BIOS y UEFI no se evalúan ni generan de forma independiente |

### 3.3 Medios y bajos

| ID | Error | Archivo | Impacto |
|---|---|---|---|
| M-01 | `_locate_iso()` usa `pkexec test -f` como sonda privilegiada | `core/builder.py:2250-2257` | Puede abrir un diálogo polkit innecesario o fallar |
| M-02 | `closeEvent` impide cerrar durante un build pero no ofrece cancelarlo | `main.py:499-518` | Mala experiencia; el usuario debe ir a la pestaña y cancelar |
| M-03 | Los logs se pierden/sobrescriben en cada build | `core/builder.py:167`, `2090-2098` | No hay diagnóstico posterior |
| M-04 | `_cleanup_stale_builds()` no se ejecuta tras un éxito | `core/builder.py` | Restos de `install_root` pueden quedar montados |
| M-05 | El banner del instalador comparte el límite de 4 MiB de Plymouth | `main.py:246` | Mensaje correcto, pero el límite no es configurable ni específico |
| M-06 | `release` no se guarda/restaura en QSettings | `main.py` | Menor; hoy solo existe Fedora 44 |
| M-07 | `mi_sitio/` y los volcados `.txt` conviven con el código | raíz | Confusión, riesgo de divergencia y paquete de distribución sucio |
| M-08 | `INFORME.txt` describe el estado anterior | raíz | Riesgo de documentación engañosa (ya advertido en su cabecera) |
| M-09 | Sin `pyproject.toml`, entrada CLI ni `.spec` | raíz | No hay instalación reproducible |
| M-10 | Sin pruebas de GUI, perfiles, diagnóstico ni ISO | `tests/` | Cobertura limitada al backend actual |

---

## 4. Archivos que necesitan modificaciones

| Archivo | Motivo |
|---|---|
| `main.py` | Reducir responsabilidades, unificar validación, navegación/panel, cierre seguro, carga de perfiles |
| `core/builder.py` | Separar en módulos; corregir C-01…C-05; eventos de etapa reales; hooks de hash/informe |
| `core/privileges.py` | Resultado estructurado, detección previa y mensajes claros; evitar sondas innecesarias |
| `core/usb.py` | Mover a `core/usb/`, eliminar `sh -c`, añadir cancelación y verificación SHA-256 |
| `gui/theme.py` | Tokens de color, tema claro/oscuro, tarjetas, navegación lateral |
| `gui/layouts.py` | Componentes de panel, tarjetas y páginas con encabezado |
| `gui/tab_meta.py` | Integrar en el asistente; validación compartida; selección de perfil/base |
| `gui/tab_aesthetic.py` | Integrar en el asistente; estado de validación |
| `gui/tab_software.py` | Reemplazar texto libre por catálogo; validar contra repos |
| `gui/tab_installer.py` | Integrar en el asistente; opciones de arranque |
| `gui/tab_build.py` | Panel de compilación con etapas, tiempo, estado, informe y hash |
| `gui/tab_usb.py` | Mover a página USB; cancelación, detección y verificación |
| `README.md` | Requisitos reales (syslinux, xorriso, lorax, qemu), estado y limitaciones |
| `requirements.txt` | Dependencias de pruebas/DI opcionales; fijar versión mínima |
| `tests/test_builder.py` | Adaptar imports si `core.builder` pasa a fachada compatible |
| `tests/test_usb.py` | Adaptar a `core.usb` como paquete |
| `.gitignore` | Excluir cachés, builds, informes generados y volcados |

**Compatibilidad obligatoria:** `core.builder.KioskISOBuilder` y
`core.builder.invalid_package_names` deben seguir existiendo como fachada para
no romper pruebas ni consumidores actuales.

---

## 5. Archivos nuevos necesarios

### 5.1 Núcleo

```text
core/config/            settings.py, paths.py, schema.py, validators.py
core/build/             build_manager.py, build_process.py, build_events.py,
                        build_result.py, build_lock.py
core/kickstart/         generator.py, parser.py, validator.py, sections.py
core/repositories/      manager.py, package_checker.py, mirror_probe.py
core/security/          permissions.py, rpm_verifier.py, security_checker.py,
                        allowlist.py
core/validation/        diagnostics.py, config_validator.py, iso_validator.py,
                        report_generator.py
core/iso/               iso_inspector.py, iso_metadata.py, iso_hash.py
core/usb/               device_detector.py, usb_writer.py, verify.py
core/profiles/          manager.py, model.py, migrations.py
core/catalog/           catalog.py, models.py
core/history/           store.py, models.py
core/backup/            manager.py
core/logging/           setup.py, events.py
```

### 5.2 Interfaz

```text
gui/app.py              ventana principal y navegación
gui/pages/              dashboard.py, identity.py, appearance.py, software.py,
                        installer.py, security.py, build.py, laboratory.py,
                        history.py, profiles.py, diagnostics.py, usb.py
gui/components/         cards.py, status_pill.py, log_view.py, stage_progress.py,
                        empty_state.py, banner.py
gui/dialogs/            confirm_destructive.py, error_details.py, about.py
gui/wizard/             wizard.py, state.py, steps/step_*.py
gui/theme/              tokens.py, light.qss, dark.qss
```

### 5.3 Datos, pruebas y documentación

```text
profiles/               kiosco-navegador.json, kiosco-multiventana.json,
                        oficina.json, terminal-atencion.json,
                        estacion-trabajo.json, schema.json
catalog/                applications.json (+ validación de esquema)
configuration/          defaults.json
tests/                  test_profiles.py, test_diagnostics.py,
                        test_kickstart_validator.py, test_iso_inspector.py,
                        test_reports.py, test_history.py, test_backup.py,
                        test_gui_smoke.py, test_integration_build.py
documentation/          INSTALL.md, USER_GUIDE.md, ARCHITECTURE.md,
                        SECURITY.md, BUILD_PROCESS.md, ISO_LAB.md,
                        CHANGELOG.md
packaging/              creador-kiosk.spec, creador-kiosk.desktop,
                        creador-kiosk.svg
pyproject.toml
```

---

## 6. Riesgos de compatibilidad

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Romper imports actuales al dividir `core/builder.py` | Alta | Alto | Mantener fachada `core/builder.py` con reexportaciones y pruebas de contrato |
| Cambiar claves de QSettings y perder configuración del usuario | Media | Medio | Leer claves antiguas, migrar a `configuration/` con versión y conservar fallback |
| Alterar el Kickstart y romper ISOs que hoy funcionan | Media | Alto | Congelar "Kickstart de referencia" y comparar por pruebas golden; no cambiar secciones sin prueba |
| `livecd-creator` no soporta UEFI exclusivo | Alta | Medio | Documentar; evaluar `livemedia-creator`/`lorax` como backend alternativo en etapa posterior |
| Diferencias de paquetes entre Fedora 44 y futuras releases | Alta | Alto | Parametrizar release/arquitectura; validar paquetes con `dnf` antes de compilar |
| Python 3.14 + `livecd-tools`/`urlgrabber` (API `pkg_resources`) | Media | Alto | Detectar y degradar; evaluar backend lorax; registrar advertencia |
| Dependencia de `syslinux`, `xorriso`, `lorax`, `mkefiboot` no declarada | Alta | Alto | Preflight explícito + documentación + empaquetado con Requires |
| `sudo -n` no disponible (caso de este host) | Alta | Medio | Ya se usa `pkexec`; añadir diagnóstico y mensaje claro antes de compilar |
| Operaciones USB destructivas | Baja (con controles actuales) | Crítico | Conservar y ampliar validaciones; nunca autoseleccionar; confirmación final |
| Pruebas QEMU con hardware/permisos insuficientes | Media | Medio | Estado "no disponible", nunca "aprobada" |
| Anaconda/LightDM/greeter cambian entre releases | Media | Alto | Fijar release, probar en QEMU, documentar limitaciones |
| `mi_sitio/` y volcados `.txt` contaminan la distribución | Alta | Bajo | Separar en `legacy/` o excluir del paquete (con confirmación del usuario) |

---

## 7. Plan de implementación por etapas

> Cada etapa debe terminar con `compileall`, `pytest`, prueba de humo de GUI y
> actualización de documentación. Ninguna etapa se marca como terminada sin
> evidencia ejecutada.

### ETAPA 2 — Estabilización (inmediata)

- Corregir C-01 (paquete `nm-connection-editor`).
- Corregir C-02 (`linuxefi`/`initrdefi` en la entrada de instalador UEFI).
- Corregir C-03 (`%post --erroronfail` + autoverificación final).
- Corregir C-04 (preflight de `mkefiboot`, `xorrisofs`, `syslinux`).
- Corregir C-05 (validación única del nombre de producto).
- Registrar `traceback` en fallos y no perder el log.
- Añadir pruebas de regresión para cada corrección.
- **Puerta:** 53 pruebas actuales + nuevas en verde; Kickstart generado válido;
  GUI abre; sin cambios de comportamiento no justificados.

### ETAPA 3 — Interfaz profesional

- Ventana con navegación lateral, panel principal y tarjetas de estado reales.
- Asistente de 6 etapas con guardado, validación por etapa y ayuda contextual.
- Modo Simple / Avanzado.
- Tema claro/oscuro y componentes reutilizables.
- **Puerta:** recorrido completo del asistente sin errores; estados reales del
  sistema (última ISO, espacio, dependencias, servicios).

### ETAPA 4 — Motor modular

- Extraer `core/kickstart`, `core/build`, `core/repositories`, `core/security`,
  `core/validation`, `core/usb` conservando la fachada pública.
- Eventos de build con etapas reales; lockfile e ID de build.
- **Puerta:** pruebas de contrato + Kickstart golden sin diferencias.

### ETAPA 5 — Perfiles y catálogo

- Esquema JSON versionado, 5 perfiles iniciales, CRUD, import/export, validación.
- Catálogo por categorías con comprobación real en repos.
- **Puerta:** crear/duplicar/exportar/importar/eliminar con confirmación;
  paquetes inexistentes detectados antes del build.

### ETAPA 6 — Seguridad

- Diagnóstico de permisos, verificación de firmas RPM, listas permitidas,
  validación de repositorios, registro de operaciones privilegiadas.
- **Puerta:** build con RPM no firmado rechazado; operaciones privilegiadas
  auditadas; sin root para la GUI.

### ETAPA 7 — Laboratorio

- `iso_inspector` (ISO9660, El Torito, EFI, kernel, initramfs, hashes).
- Validación Kickstart, paquetes y estructura.
- QEMU BIOS/UEFI con discos virtuales aislados.
- Informe TXT/HTML (+PDF opcional).
- **Puerta:** una ISO de prueba pasa GENERADA → VALIDADA; las pruebas virtuales
  se registran como reales, pendientes o no disponibles (nunca falsas).

### ETAPA 8 — Historial y respaldos

- Historial con configuración, herramientas, resultado, hash, logs e informe.
- Comparación de builds, repetición, exportación/importación de respaldos.
- **Puerta:** build anterior consultable y reproducible; respaldo verificado.

### ETAPA 9 — Pruebas

- Unitarias e integración de todos los módulos; GUI smoke con Qt offscreen.
- **Puerta:** suite completa en verde y límites documentados.

### ETAPA 10 — Distribución

- `pyproject.toml`, `.spec`, `.desktop`, icono, CHANGELOG, documentación final.
- **Puerta:** instalación limpia en Fedora 44 y arranque de la aplicación.

---

## Anexo A — Correcciones aplicadas en la ETAPA 2

Fecha de cierre: 2026-11-13. Respaldo previo:
`backups/pre-2.0-20261113-120424.tar.gz`
(SHA-256 `8c5f7159073827c85a1493b2213abefee34e5bb42926b1d2f0373f1678a22236`).

### C-01 — `nm-connection-editor` faltaba en modo multiventana

- **Archivo:** `core/builder.py` (lista de paquetes de `_package_lines` y
  referencias del atajo Alt+9 en Sway).
- **Problema:** el atajo Alt+9 ejecutaba `/usr/bin/nm-connection-editor`, pero
  el paquete no se instalaba. El binario pertenece al paquete separado
  `nm-connection-editor`, no a `network-manager-applet`.
- **Corrección:** se añadió `nm-connection-editor` a los paquetes del modo
  multiventana, junto con la justificación en comentarios.
- **Prueba:** `test_multiventana_instala_nm_connection_editor`
  (`tests/test_builder.py`).

### C-02 — Entrada UEFI del instalador reescribía el cargador

- **Archivo:** `core/builder.py` (`_installer_boot_section`).
- **Problema:** la entrada de arranque del instalador generaba líneas fijas
  `linux`/`initrd`, perdiendo `linuxefi`/`initrdefi` del `grub.cfg` original;
  en UEFI la entrada podía no arrancar.
- **Corrección:** se extraen `$linux_line` e `$initrd_line` del `grub.cfg` con
  `awk` y se reutilizan tal cual, añadiendo solo `kiosk.mode=installer`.
- **Prueba:** `test_installer_boot_preserves_efi_loader_commands`
  (`tests/test_builder.py`).

### C-03 — Fallos de `%post` ignorados y sin autoverificación

- **Archivo:** `core/builder.py` (`%post` chroot y
  `_final_check_section`).
- **Problema:** `livecd-creator` ignora los fallos de `%post` salvo que se use
  `--erroronfail`; además no había comprobación final de artefactos críticos.
- **Corrección:** el script chroot usa `%post --erroronfail`; se añadió una
  sección de autoverificación que falla explícitamente si faltan kioskuser o
  su hash, la unidad systemd, el compositor, los archivos `.cmd` de las
  aplicaciones, el greeter, el instalador o los binarios requeridos.
- **Pruebas:** `test_kickstart_post_uses_erroronfail_and_self_check`,
  `test_generated_post_scripts_are_valid_shell`,
  `test_final_check_covers_installer_greeter_and_apps`
  (`tests/test_builder.py`).

### C-04 — Preflight incompleto

- **Archivo:** `core/builder.py` (`_preflight`).
- **Problema:** no se comprobaban herramientas necesarias para ISO híbrida
  (`mkefiboot`, `xorrisofs`), activos syslinux (`isolinux.bin`,
  `isohdpfx.bin`, `vesamenu.c32`) ni el soporte de RPM locales
  (`rpm`, `createrepo_c`).
- **Corrección:** el preflight verifica todas esas dependencias y devuelve un
  mensaje único con el comando `dnf install` sugerido.
- **Pruebas:** `test_preflight_reports_all_missing_tools`,
  `test_preflight_requires_createrepo_for_local_rpm`
  (`tests/test_builder.py`).

### C-05 — Validación divergente del nombre de producto

- **Archivos:** `core/builder.py` (`validate_product_name` y uso en
  `_branding_section`), `main.py` (validación de la interfaz).
- **Problema:** la interfaz y el backend validaban el nombre con reglas
  distintas; un nombre aceptado en la GUI podía romper el Kickstart.
- **Corrección:** helper compartido `validate_product_name()` usado por ambos
  lados, con las mismas reglas (comillas, barras invertidas, `$`, caracteres
  de control y longitud máxima de 80).
- **Prueba:** `test_validate_product_name_matches_backend_rules`
  (`tests/test_builder.py`).

### Robustez adicional

- **Archivos:** `core/builder.py` (`build`, `_uses_local_rpm`,
  `_exec_binaries`, `_run_livecd`).
- **Cambios:** registro de `traceback` en fallos, cancelación limpia y
  extracción segura de binarios desde cadenas de comando (sin confundir URL o
  flags con ejecutables).
- **Prueba:** `test_exec_binaries_ignores_urls_and_flags`
  (`tests/test_builder.py`).

### Resultados reales de la etapa

- `python3 -m compileall -q .` → sin errores.
- `python3 -m pytest -q` → **62 passed** (53 previas + 9 nuevas) al cerrar la ETAPA 2; **84 passed** al cerrar la ETAPA 3.
- Kickstart generado parseado con pykickstart de Fedora 44 → **2 scripts
  `%post`**, el script chroot con `errorOnFail=True`.
- `sh -n` sobre cada `%post` generado → sin errores de sintaxis.
- GUI PySide6 6.11.2 abierta con `QT_QPA_PLATFORM=offscreen` → **6 pestañas**
  cargadas sin excepciones.

### Pendiente y no declarado como superado

- Compilación completa de ISO y arranque BIOS/UEFI reales: **no ejecutados**
  en este host (3 GiB de RAM, sin `sudo -n` y operación larga dependiente de
  red). Queda pendiente para la etapa de laboratorio, donde deberá registrarse
  como resultado real, no como aprobado.

---

## Anexo B — Cambios de la ETAPA 3 (interfaz profesional)

Fecha de cierre: 2026-11-13.

### Arquitectura de la interfaz

- `main.py` pasó de un `QTabWidget` a una ventana con:
  - navegación lateral (`Panel principal`, seis pasos y `Unidad USB`);
  - encabezado con breadcrumb, modo Simple/Avanzado, tema y estado global;
  - `QStackedWidget` para las páginas;
  - pie de asistente con `Anterior`, `Validar paso`, `Guardar`, `Ayuda` y
    `Siguiente`;
  - panel de ayuda contextual plegable.
- Se conservaron los mixins existentes y todos los atributos públicos que usa
  el backend (`txt_*`, `check_*`, `combo_*`, `*_field`, etc.).
- La recolección de configuración se centralizó en `collect_config()` y la
  validación en `gui/validation.py`.

### Nuevos módulos

- `gui/components.py`: `PageHeader`, `StatusCard`, `HelpPanel` y `Card`.
- `gui/layouts.py`: `add_page()` con encabezado fijo, scroll uniforme y registro
  de páginas.
- `gui/status.py`: dependencias reales, espacio en disco, servicios del host,
  formateo de fechas y `HashWorker` para SHA-256 en segundo plano.
- `gui/validation.py`: validadores independientes para las seis etapas y
  utilidades `validate_step`, `validate_all`, `validate_until`.
- `gui/tab_security.py`: paso 5, con firewall, SSH, sudo, consolas virtuales y
  estado real de servicios del host.
- `gui/theme.py`: paletas clara y oscura y `build_stylesheet()`.

### Panel principal

Muestra información real, no simulada:

- última compilación y estado (`GENERADA`, `ERROR`, `CANCELLED`);
- ruta, tamaño y fecha de modificación de la ISO;
- SHA-256 calculado por bloques en un hilo, con caché invalidada por tamaño y
  fecha;
- espacio libre del volumen de salida;
- dependencias y activos syslinux detectados con `shutil.which`/`isfile`;
- estado de `firewalld` y `sshd` mediante `systemctl is-active`;
- configuración activa y tareas pendientes;
- último error de compilación guardado en QSettings.

La ISO se etiqueta explícitamente como generada y pendiente de validar/probar.
No se infiere ni se declara un estado de validación o prueba que no se haya
ejecutado.

### Asistente y modos

- Seis pasos: identidad, apariencia, software, instalador, seguridad y
  compilación/validación.
- `Validar paso` comprueba el paso actual sin avanzar, muestra los errores
  críticos y deja el resultado en el pie del asistente.
- `Siguiente` valida el paso actual; la navegación lateral valida los pasos
  previos antes de avanzar. Los errores se muestran con el paso afectado.
- `Guardar` persiste la configuración; la contraseña nunca se guarda.
- La ayuda contextual cambia con la página activa.
- Modo Simple oculta y restablece las opciones avanzadas activas tras
  confirmación: multiventana, greeter, sudo sin contraseña, sandbox, paquetes
  extra, resolución manual y banner del instalador.
- Modo Avanzado vuelve a mostrar todos los controles sin perder la estructura
  del asistente.
- Tema claro/oscuro persistente y aplicado a toda la ventana, incluidas las
  previsualizaciones y consolas.

### Validaciones añadidas

- Identidad: nombre de ISO, versión, creador, producto y contraseña.
- Apariencia: existencia y tamaño de splash y fondo del greeter.
- Software: app local, URL, paquetes adicionales y segunda aplicación.
- Instalador: banner.
- Seguridad: coherencia entre SSH y autenticación por contraseña.
- Compilación: dependencias, carpeta de salida, permisos, espacio para la ISO y
  espacio del árbol de trabajo (12 GiB).

### Pruebas y resultados reales

- `python3 -m compileall -q .` → sin errores.
- `python3 -m pytest -q` → **84 passed** (62 previas + 22 nuevas).
- Pruebas nuevas:
  - `tests/test_gui_validation.py`: validación de las seis etapas, imágenes,
    paquetes, SSH, dependencias, espacio y rutas inválidas.
  - `tests/test_gui_smoke.py`: ventana con ocho páginas, temas, modo Simple,
    bloqueo de avance, visibilidad y resultado de `Validar paso`, indicadores,
    ayuda, panel con datos reales, persistencia sin contraseña, compatibilidad
    de `collect_config` y hash SHA-256 en segundo plano.
- GUI creada y recorrida con `QT_QPA_PLATFORM=offscreen` a 1320×900 y
  1080×720, sin scroll horizontal y sin excepciones.
- Se generaron capturas de control en `/tmp/opencode/` durante la verificación
  local (no forman parte del repositorio).

### Pendiente y no declarado como superado

- No se ejecutó una compilación real de ISO ni un arranque BIOS/UEFI en esta
  etapa. El panel muestra el estado real del host, pero la validación y las
  pruebas de arranque pertenecen a la ETAPA 7.
- Las notificaciones de éxito/error de compilación siguen dependiendo del
  retorno de `livecd-creator`; el detalle de etapas internas se abordará en la
  ETAPA 4.
