# Auditoría de interfaz y línea base — Etapa 0

**Producto:** Creador Personalizado 3.0.0-alpha.2  
**Base auditada:** `Creador-Personalizado-3.0.0-alpha.2/`  
**Fecha:** 2026-11-16  
**Estado:** diagnóstico para revisión y aprobación. **No se modificó código de la aplicación.**

> Este documento corresponde al primer encargo del Skill: Etapa 0.  
> Se agregaron únicamente este informe y capturas de referencia en `documentation/auditoria-etapa0/`.
> No se rediseñó ninguna pantalla, no se cambiaron señales, servicios ni motores.

---

## 0. Resumen ejecutivo

La aplicación tiene una base funcional sólida (225 de 226 pruebas pasan) y una separación correcta entre motores Kiosco y Desktop. La deuda principal está en la capa visual y en algunos ciclos de vida de hilos:

| ID | Severidad | Hallazgo | Evidencia breve |
|---|---|---|---|
| F-01 | **P0** | Cerrar la ventana con una consulta DNF activa aborta el proceso | Reproducido: `worker running at close: True` → salida 134 (SIGABRT) |
| F-02 | **P1** | El Panel principal tiene scroll horizontal en el tamaño mínimo declarado (1080×720) | página 826 px vs viewport 749 px → 77 px de scroll |
| F-03 | **P1** | El Gestor de software se recorta y tiene scroll horizontal a 1080 y 1280 | página 1055 px vs 749/949 px → 306/106 px |
| F-04 | **P1** | En tema oscuro, las filas alternas de las tablas son ilegibles | texto `#e6edf6` sobre fondo `#f7f7f7` = contraste 1.10:1 |
| F-05 | **P1** | El selector "Tipo de distribución" del Paso 1 está vacío: el combo fue movido al Gestor | captura 03; el combo pertenece al `QGroupBox` del Gestor |
| F-06 | **P1** | El tema pinta fondo en todos los `QWidget`/`QLabel`: etiquetas parecen campos y encabezados parecen botones | captura 06 y barras de sección del sidebar |
| F-07 | **P1** | La marca del sidebar se corta a 270 px fijos | "Creador Persona…" en todas las capturas |
| F-08 | **P2** | Consultas de servicios del host son síncronas y pueden congelar la UI | `service_states()` con `timeout=4` por servicio, llamado 2 veces por refresco |
| F-09 | **P2** | El resumen del Paso 6 queda vacío o desactualizado | "Sin resumen disponible." en captura 06 |
| F-10 | **P2** | La modalidad Kiosco se elige por defecto, no de forma explícita | `main.py:171`, `main.py:802`, `registry.py:14` |
| F-11 | **P2** | La validación previa no contempla dependencias de RPM local | UI puede decir "válida" y el build falla después |
| F-12 | **P2** | El estado global del pie es sobrescrito por mensajes DNF en segundo plano | En Paso 1 se lee "Catálogo actualizado: 500 paquetes…" |
| F-13 | **P2** | El Gestor no tiene entrada en la navegación y no marca ítem activo | `NAV_ITEMS` no lo incluye; ninguna entrada queda resaltada |
| F-14 | **P2** | Modo Simple descarta paquetes/grupos/banner sin confirmar en ciertos casos | `_advanced_features_active()` solo mira 5 checkboxes |
| F-15 | **P2** | El Gestor no cubre varios requisitos del Skill (arquitectura, quitar/actualizar, simulación inline) | ver §7.3 |
| F-16 | **P3** | Contraste de texto atenuado en tema claro por debajo de 4.5:1 | `#66758a` sobre `#f3f6fb` = 4.33:1 |
| F-17 | **P3** | Inconsistencias de marca, tipografía y estilos globales | "Fedora Image Studio", "Solapa 6", `#c00`, fuentes Segoe UI |
| F-18 | **P3** | Deuda técnica que afecta la evolución de la UI | combo compartido, código muerto, listas ocultas, dependencia duplicada |
| F-19 | **P3** | Suite de pruebas lenta y dependiente de DNF real; solo GUI offscreen | 108.8 s; cada ventana dispara una consulta real |

**Conclusión:** no conviene empezar por un rediseño cosmético. Primero hay que estabilizar el ciclo de vida de hilos y corregir los mínimos de layout que ya fallan en el tamaño declarado. Después, el sistema visual y la estructura pueden renovarse sin tocar motores ni validaciones.

---

## 1. Método y alcance

### 1.1 Qué se inspeccionó

- `main.py` completo (ventana, shell, navegación, panel, configuración, hilos).
- `gui/layouts.py`, `gui/theme.py`, `gui/components.py`, `gui/status.py`, `gui/images.py`, `gui/validation.py`.
- Todas las páginas: `custom_distro.py`, `tab_meta.py`, `tab_aesthetic.py`, `tab_software.py`, `tab_installer.py`, `tab_security.py`, `tab_build.py`, `tab_usb.py`.
- Dependencias usadas por la UI: `core/builders/`, `core/desktops/`, `core/projects/`, `core/repositories/dnf_query.py`, `core/software/policy.py`, `core/usb.py`, `core/builder.py`, `core/validation/diagnostics.py`, `core/history/manager.py`.
- Pruebas de `tests/` y configuración de `pyproject.toml`.

### 1.2 Qué se ejecutó

| Acción | Resultado |
|---|---|
| `QT_QPA_PLATFORM=offscreen python3 -m pytest -q` | **225 passed, 1 failed**, 1 warning, **108.80 s** |
| Instanciar `KioskBuilderGUI` y medir layout en 1080×720, 1280×800, 1440×900, 1920×1080 | ver §7.1 y §7.2 |
| Simular mínimo 900×640/1024×700 sin tocar código | el contenido no cabe: dashboard 826 px mín., gestor 1055 px mín. |
| Consulta DNF5 real desde el Gestor (carga automática) | completada; **500 paquetes** (límite de la alpha) en **3.53 s** |
| Capturas offscreen en tamaños conocidos | `documentation/auditoria-etapa0/` |
| Cierre de ventana con consulta DNF en curso | **proceso abortado, salida 134 (SIGABRT)** |
| Build de ISO | **no ejecutado** |
| Escritura USB | **no ejecutada** |
| Prueba manual en pantalla real | **no ejecutada**; las capturas y pruebas GUI son con plataforma `offscreen` |

### 1.3 Entorno

- Python 3.14.8, PySide6 6.11.2.
- Fedora con `dnf5`, `livecd-creator`, `openssl`, `mkefiboot`, `xorrisofs`, `qemu-system-x86_64`, `pkexec` y activos de syslinux presentes.
- Sesión Wayland disponible, pero no se abrió una ventana real para no interrumpir la sesión del usuario.
- No se encontró el módulo Python `dnf5`; el proyecto usa el ejecutable `dnf5`/`dnf` mediante subprocess, que sí funciona.

### 1.4 Falla preexistente de la línea base

`tests/test_gui_smoke.py::test_wizard_blocks_progress_with_invalid_step` falla:

```
assert shown
E   assert []
```

Motivo: el test deja la contraseña vacía y espera que el Paso 1 sea inválido, pero el proyecto arranca con `project_type="kiosk"` y `validate_identity()` solo exige contraseña para motores que no son Kiosco (`gui/validation.py:104-108`). Es una discrepancia entre el supuesto del test y el valor por defecto actual; no es una regresión visual. **No se modificó el test.**

---

## 2. Mapa de navegación actual

### 2.1 Entradas del sidebar

| Orden | Clave | Etiqueta visible | Paso |
|---|---|---|---|
| 1 | `dashboard` | Panel principal | — |
| 2 | `step1` | 1 Identidad del sistema | 1 |
| 3 | `step2` | 2 Apariencia y personalización | 2 |
| 4 | `step3` | 3 Selección de software | 3 |
| 5 | `step4` | 4 Configuración del instalador | 4 |
| 6 | `step5` | 5 Seguridad y servicios | 5 |
| 7 | `step6` | 6 Compilación y validación | 6 |
| — | separador | HERRAMIENTAS | — |
| 8 | `usb` | Unidad USB | — |

`custom_distro` (Gestor de software) **no está en el sidebar**. Se llega desde el Panel principal con el botón “＋ Nuevo proyecto · Fedora a medida” (`main.py:423-425`) y se vuelve con “Volver al panel” dentro de la página (`gui/custom_distro.py:243-245`). Al estar allí, ninguna entrada del sidebar queda activa (`main.py:482-484` solo recorre las claves existentes).

### 2.2 Reglas de avance

- `Siguiente` valida el paso actual (`main.py:526-532`); si hay errores, no avanza.
- `Validar paso` valida sin navegar (`main.py:534-550`).
- `Anterior` navega sin validar (`main.py:552-559`).
- Clic en el sidebar o salto a un paso: valida todos los pasos anteriores; si hay errores, salta al primero que falla (`main.py:460-476`).
- Los indicadores `✓` del sidebar se recalculan con `validate_step()` para los seis pasos (`main.py:714-727`).
- El pie muestra “Paso N de 6” o el estado de la página; el encabezado muestra breadcrumb (`main.py:485-497`).
- La ayuda contextual se abre con `Ayuda` y usa el texto de la página (`main.py:248-250`, `572-586`).

### 2.3 Flujo real de creación

```
Panel principal
  ├─ Continuar asistente ──────────────> Paso 1 … Paso 6
  ├─ Ir a compilar ────────────────────> Paso 6
  └─ Nuevo proyecto · Fedora a medida ─> Gestor de software
                                           └─ Aplicar selección al proyecto
                                                └─ Paso 1 (sin selector de tipo visible)
```

El flujo del Gestor es funcional, pero la vuelta al asistente deja el Paso 1 sin el selector de modalidad (F-05).

---

## 3. Inventario de pantallas

| Clave | Archivo | Propósito | Datos / servicios que consume |
|---|---|---|---|
| `dashboard` | `main.py:354-450` | Estado del entorno, última ISO, dependencias, servicios, configuración activa, pendientes y errores | `gui.status.disk_info`, `check_dependencies`, `service_states`, `HashWorker`; `QSettings` |
| `step1` | `gui/tab_meta.py` | Identidad, tipo de distribución, base, arranque, usuario y contraseña Desktop | `core.projects.catalog.list_project_types`, `get_project_template` |
| `step2` | `gui/tab_aesthetic.py` | Splash de Plymouth y resolución | `core.builder.MAX_PLYMOUTH_BYTES`, `gui.images.ImageField` |
| `step3` | `gui/tab_software.py` | App Kiosco, multiventana, paquetes/grupos extra, escritorio Desktop | `core.desktops.environments` |
| `step4` | `gui/tab_installer.py` | Anaconda, banner y texto de bienvenida | `core.builder.MAX_PLYMOUTH_BYTES`, `gui.images.ImageField` |
| `step5` | `gui/tab_security.py` | Firewall, SSH, sudo, consolas, estado del host | `gui.status.service_states` |
| `step6` | `gui/tab_build.py` | Salida, resumen, validación, progreso, logs y cancelación | `main.BuilderWorker` → `core.builders` → `KioskISOBuilder` / `DesktopISOBuilder` |
| `usb` | `gui/tab_usb.py` | Escritura de ISO a USB | `core.usb.list_usb_disks`, `USBWriterWorker`, `core.privileges` |
| `custom_distro` | `gui/custom_distro.py` | Catálogo DNF, grupos Comps, repositorios, cambios pendientes y simulación | `core.repositories.dnf_query.DnfQuery`, `core.software.policy`, `core.projects.catalog` |

### 3.1 Componentes compartidos

| Componente | Archivo | Uso | Observación |
|---|---|---|---|
| `PageHeader` | `gui/components.py:14-33` | Título/subtítulo de cada página | Correcto; tipografía definida en QSS |
| `StatusCard` | `gui/components.py:36-85` | 8 tarjetas del Panel principal + errores | No es adaptable por sí solo; depende del grid fijo |
| `HelpPanel` | `gui/components.py:88-112` | Ayuda contextual plegable | Altura máxima fija (150 px); scroll interno |
| `Card` | `gui/components.py:115-123` | Contenedor genérico | Poco usado actualmente |
| `add_page` | `gui/layouts.py:16-45` | Registra página, header, scroll y ancho máximo | `content_width=1180`; centra el contenido |
| `_polish_nested_layouts` | `gui/layouts.py:48-72` | Uniforma márgenes/espaciados | Afecta también formularios y grupos |
| Tema | `gui/theme.py` | Tokens de color + QSS | No cubre tablas, headers, splitter ni diálogos |
| Imágenes | `gui/images.py` | Selección, conversión y preview | Preview fijo en 360×200 / 360×160 |
| Validación | `gui/validation.py` | Reglas por paso y globales | Independiente de la UI; reutilizable |
| Estado del host | `gui/status.py` | Dependencias, disco, servicios, hash | Servicios síncronos; hash en hilo |

---

## 4. Dependencias UI → servicios → motores

```
main.KioskBuilderGUI
├── shell: sidebar, topbar, footer, ayuda
├── páginas (mixins)
│   ├── tab_meta ──────────────> core.projects.catalog
│   ├── tab_aesthetic ────────> core.builder (MAX_PLYMOUTH_BYTES) + gui.images
│   ├── tab_software ─────────> core.desktops.environments
│   ├── tab_installer ────────> core.builder + gui.images
│   ├── tab_security ─────────> gui.status.service_states
│   ├── tab_build ────────────> main.BuilderWorker
│   ├── tab_usb ──────────────> core.usb.USBWriterWorker + core.privileges
│   └── custom_distro ────────> core.repositories.dnf_query.DnfQuery
│                               core.software.policy
│                               core.projects.catalog
├── validación
│   └── gui.validation ───────> core.builder (constantes)
│                               core.builders (resolve_build_engine)
│                               core.desktops.*
│                               core.projects.catalog
│                               core.software.policy
│                               gui.status.check_dependencies
└── compilación
    └── BuilderWorker ────────> core.builders.resolve_builder_class
                                ├── KioskISOBuilder (core/builder.py:101)
                                └── DesktopISOBuilder (core/builders/desktop.py:20)
                                └── core.builder usa livecd-creator, Kickstart,
                                    historial SQLite, privilegios y RPM locales

Consulta DNF
  DnfWorker (QThread) ─> DnfQuery (subprocess dnf5/dnf, shell=False, timeout 180 s)
                         ├─ repolist --enabled --json
                         ├─ search --all -- <términos>
                         ├─ repoquery --available --latest-limit=1
                         ├─ group list --hidden / group info
                         └─ --assumeno install <paquetes/grupos>  (simulación)
```

### 4.1 Contratos que no deben romperse

- `resolve_build_engine()` y `resolve_builder_class()` (`core/builders/registry.py:26-59`).
- `collect_config()` y sus claves (`main.py:742-788`); los motores las consumen.
- Señales de `BuilderWorker` (`log_signal`, `progress_signal`, `iso_signal`, `finished_signal`).
- Señales de `USBWriterWorker`, `HashWorker` y `DnfWorker`.
- Reglas de `gui/validation.py` y sus `VALIDATORS` por paso.
- Persistencia `QSettings` (organización `CreadorKiosk`, app `Creador-kiosk`), incluida la decisión de no guardar contraseña.
- Resolución de motores independiente Kiosco/Desktop.
- DNF de solo lectura y `--assumeno`; nunca instalar en el host desde la UI.
- Mecanismo de privilegios para USB y build.

---

## 5. Línea base de comportamiento medido

### 5.1 Layout a tamaños conocidos

Medición real con Qt offscreen, tras `show()` y varios ciclos de eventos:

| Tamaño de ventana | Página | Viewport | Ancho de página | Scroll horizontal |
|---|---:|---:|---:|---:|
| 1080×720 | Dashboard | 749 | **826** | **sí, 77 px** |
| 1080×720 | Gestor | 749 | **1055** | **sí, 306 px** |
| 1080×720 | Pasos 1-6 / USB | 749 | 749 | no |
| 1280×800 | Dashboard | 949 | 949 | no |
| 1280×800 | Gestor | 949 | **1055** | **sí, 106 px** |
| 1440×900 | Dashboard | 1109 | 1109 | no |
| 1440×900 | Gestor | 1109 | 1109 | no |
| 1920×1080 | Todas | 1600 | 1180 (tope de `add_page`) | no |

En el Gestor, la tabla de paquetes mantiene **scroll horizontal interno incluso a 1920×1080** por el modo de columnas (`ResizeToContents` en 3 de 4 columnas).

### 5.2 Causa medida del scroll del Dashboard

El scroll horizontal no lo producen las tarjetas, sino la fila de cuatro botones del final (`main.py:422-440`):

| Botón | Ancho mínimo |
|---|---:|
| “＋ Nuevo proyecto · Fedora a medida” | 312 |
| “Actualizar estado” | 142 |
| “Continuar asistente” | 157 |
| “Ir a compilar” | 113 |
| **Suma + separaciones** | **778** |
| **+ márgenes de página (24+24)** | **826** |

A 1080×720 el viewport es 749: sobran 77 px. Los botones están además **debajo del pliegue**; el usuario debe hacer scroll vertical para llegar a la acción primaria.

### 5.3 Causa medida del scroll del Gestor

- El `QComboBox` de “Perfil de distribución” tiene **ancho mínimo 666 px** porque muestra `name — tagline` de perfiles largos (`gui/custom_distro.py:98-102`, textos de `core/projects/catalog.py`).
- La fila del perfil suma combo + descripción + botón, y la página termina con **mínimo 1055 px**.
- La descripción queda comprimida a **84 px** a 1280×800: se ve una letra por línea en la captura 04 y gran espacio vacío vertical.
- El botón “Cargar perfil sugerido” queda cortado por el borde derecho.
- La tabla de 4 columnas con `ResizeToContents` en Paquete, Versión y Repositorio (`gui/custom_distro.py:162-165`) fuerza scroll interno en el panel izquierdo del splitter (`gui/custom_distro.py:151-188`).

### 5.4 Arranque y operaciones de host

| Operación | Medición | Riesgo de bloqueo |
|---|---:|---|
| Construcción de ventana + show + eventos | 1.82 s | Arranque percibido |
| Consulta DNF automática al abrir el Gestor | 3.53 s | En hilo; no bloquea, pero retrasa y complica tests |
| `check_dependencies()` | 0.001 s | Bajo |
| `service_states()` (firewalld + sshd) | 0.126 s en esta máquina | **Hasta 8 s** por `timeout=4` × 2 servicios (`gui/status.py:77-91`) |
| `list_usb_disks()` | 0.048 s | Puede bloquear si `lsblk`/udev tarda |

`refresh_dashboard()` llama a `service_states()` en `main.py:1051` y otra vez en `main.py:1118` (vía `refresh_service_state`), duplicando el costo. Al arrancar, `init_tab_security()` también lo llama (`gui/tab_security.py:120`).

### 5.5 Contraste de tablas en tema oscuro

Paleta real después de `_apply_theme("dark")`:

| Rol | Color |
|---|---|
| Texto de tabla | `#e6edf6` |
| Base / fondo de viewport | `#0f1722` |
| **AlternateBase** | **`#f7f7f7`** |
| Header (Button/Text) | `#0f1722` / `#e6edf6` |

La fila alterna queda casi blanca (`#f7f7f7`) con texto casi blanco (`#e6edf6`): **contraste 1.10:1**. La captura `07_tabla_oscuro_filas_ilegibles.png` lo muestra. `gui/theme.py` no tiene reglas para `QTableWidget`, `QTableView`, `QHeaderView` ni `alternate-background-color`.

### 5.6 Texto atenuado en tema claro

| Combinación | Contraste |
|---|---:|
| `#66758a` sobre `#ffffff` | 4.69:1 |
| **`#66758a` sobre `#f3f6fb`** | **4.33:1** |
| **`#66758a` sobre `#f5f8fc`** | **4.40:1** |

El token `MUTED` del tema claro (`gui/theme.py:14`) queda ligeramente por debajo de 4.5:1 en fondos `BG`/`SURFACE_ALT`, usados en textos de 8–9 pt.

---

## 6. Hallazgos detallados

### 6.1 P0 — Estabilidad

#### F-01. Cierre con consulta DNF activa aborta el proceso

- **Dónde:** `main.py:1276-1298` (`closeEvent`) solo espera/cancela `usb_worker`, `worker` (build) y `hash_worker`.
- El Gestor crea `DnfWorker` sin padre y lo guarda en `_custom_pkg_worker` (`gui/custom_distro.py:344-353`). La consulta automática arranca al abrir la app (`gui/custom_distro.py:266-274`).
- **Reproducción:** abrir la ventana, cerrarla mientras el worker corre, salir del intérprete.
- **Resultado real:** `worker running at close: True`; salida **134 (SIGABRT)**, mensaje de core dump. Un `QThread` destruido mientras corre aborta el proceso.
- **Impacto:** el usuario puede cerrar la app en los primeros segundos tras abrirla (la consulta real tardó 3.53 s) o durante cualquier búsqueda DNF y perder el cierre limpio. También afecta scripts y pruebas.
- **Propuesta:** en `closeEvent`, si `_custom_pkg_worker` corre: cancelar (nuevo `cancel_event`), esperar con límite y no destruir el hilo; idealmente `worker.setParent(self)` y `deleteLater()`. Añadir prueba de cierre con worker simulado.
- **Etapa:** corrección previa a la Etapa 1 o dentro de la Etapa 1, con aprobación explícita.

### 6.2 P1 — Adaptación y contraste

#### F-02. Scroll horizontal del Panel principal a 1080×720

- **Dónde:** `main.py:422-440` (fila de 4 acciones), `gui/layouts.py:16-45` (scroll y ancho máximo).
- **Evidencia:** 826 px mínimos vs 749 de viewport; scroll 77 px. Captura `01_dashboard_1080x720_claro.png`: se cortan el badge “HOST” y “PENDIENTE”, y la barra horizontal aparece al pie de la página.
- **Impacto:** incumple el criterio “sin scroll horizontal accidental” ya en el tamaño mínimo declarado. La acción primaria “Nuevo proyecto” queda bajo el pliegue.
- **Propuesta:** reemplazar la fila por un layout que reflowe (2×2, `QGridLayout` con puntos de corte) o jerarquizar: acción primaria + menú “Más acciones”; acortar etiquetas; mover el bloque de acciones arriba, junto al subtítulo. No tocar las rutas ni los slots.

#### F-03. Recorte y scroll del Gestor de software

- **Dónde:** `gui/custom_distro.py:96-111` (fila de perfil), `151-188` (splitter), `154-165` (tabla), `205-234` (fila inferior de grupos/repos).
- **Evidencia:** página mínima 1055 px; scroll 306 px a 1080 y 106 px a 1280; descripción con una letra por línea; botón “Cargar perfil sugerido” cortado. Capturas 04 y 05.
- **Causa principal:** combo de perfil con ancho mínimo 666 px por etiquetas largas `name — tagline`.
- **Propuesta:** etiquetas cortas (`name`) con `tooltip` para la tagline; descripción en una fila propia o debajo del combo; `QSplitter` con mínimos razonables y colapso del panel de detalles; tabla con modelo y modos de columna adaptativos; en anchos chicos, ocultar/mover la descripción en lugar de comprimirla.

#### F-04. Filas alternas ilegibles en tema oscuro

- **Dónde:** `gui/theme.py:51-117`; no hay reglas de tabla. `gui/custom_distro.py:160` activa `setAlternatingRowColors(True)`.
- **Evidencia:** `AlternateBase=#f7f7f7` con texto `#e6edf6`, 1.10:1; captura 07.
- **Propuesta (Etapa 1):** definir tokens de tabla (`TABLE_BG`, `TABLE_ALT_BG`, `TABLE_HEADER_BG`, `TABLE_SELECTED_BG`, `TABLE_BORDER`) y QSS para `QTableView`, `QHeaderView::section`, `QTableCornerButton`; o desactivar filas alternas en oscuro hasta tener tokens. Verificar contraste ≥ 4.5:1 en ambos temas.

#### F-05. Paso 1 sin selector de tipo de distribución

- **Dónde:** `gui/tab_meta.py:42-50` crea `combo_project_type` y `tab_meta.py:89` lo agrega al formulario. `gui/custom_distro.py:98-102` toma el mismo widget y lo agrega a otro layout.
- **Evidencia:** `combo.parentWidget()` es el `QGroupBox` del Gestor; `combo` no es visible en Paso 1; el formulario conserva la etiqueta “Tipo de distribución:” sin campo. Captura `03_paso1_1280x800_claro_selector_vacio.png`.
- **Impacto funcional:** la modalidad solo se puede cambiar desde el Gestor; cambiar el combo allí altera `_project_type` inmediatamente, aunque el usuario no pulse “Aplicar selección”. El Paso 1 no cumple su propósito y la modalidad no es explícita.
- **Propuesta (Etapa 2):** separar el estado de proyecto de los widgets (modelo compartido) y crear un selector propio en Paso 1 y otro en el Gestor, sincronizados por señal. Restaurar la fila del Paso 1 y mostrar un badge de modalidad (“Kiosco” / “Fedora Desktop · GNOME”) en el encabezado de página. No cambiar `collect_config()` ni la resolución de motor.

#### F-06. Fondo global en todos los widgets; etiquetas y secciones con aspecto de campo/botón

- **Dónde:** `gui/theme.py:52` aplica `background: @BG@` a `QMainWindow, QWidget`.
- **Evidencia:** en la captura 06, etiquetas como “Carpeta de salida de la ISO:” ocupan toda la fila como barras celestes; en el sidebar, “ASISTENTE” y “HERRAMIENTAS” parecen botones/selected rows; las tarjetas mezclan `BG` y `SURFACE_ALT`.
- **Propuesta (Etapa 1):** limitar fondos a contenedores con `objectName` (shell, páginas, tarjetas, paneles), declarar `QLabel { background: transparent; }`, y crear estilos específicos para `QLabel#sectionTitle`, `QLabel#fieldLabel`, `QLabel#hint` y `QLabel#statusBar`. Revisar contraste de cada token.

#### F-07. Marca del sidebar cortada

- **Dónde:** `main.py:200` (`setFixedWidth(270)`), `main.py:293-299` (título 18 pt), `gui/theme.py:54`.
- **Evidencia:** “Creador Persona…” cortado en todas las capturas; el subtítulo entra completo.
- **Propuesta (Etapa 2):** `QSplitter` con sidebar ajustable/colapsable, ancho mínimo/máximo, o título con `wordWrap`/elisión y tipografía adaptativa. No usar `setFixedWidth` para el panel principal.

### 6.3 P2 — Comportamiento y flujo

#### F-08. Consultas de servicios síncronas en el hilo GUI

- **Dónde:** `gui/status.py:77-91` (`subprocess.run ... timeout=4` por servicio); llamadas en `gui/tab_security.py:120`, `main.py:511-518`, `main.py:1051` y `main.py:1118`.
- **Riesgo:** 8 s por llamada en el peor caso; dos llamadas por refresco del panel. En esta máquina tardó 0.126 s, pero el código permite el bloqueo.
- **Propuesta (Etapa 3/5):** mover a `QThreadPool`/`QRunnable`, mostrar estado “consultando…” y cachear con TTL; una sola consulta por refresco.

#### F-09. Resumen del Paso 6 vacío o desactualizado

- **Dónde:** `gui/tab_build.py:113-145`; solo se llama desde `main.py:1199` (`start_build_process`). `validate_configuration` (`main.py:697-701`) y la navegación a `step6` (`main.py:510-518`) no lo refrescan.
- **Evidencia:** captura 06 muestra “Sin resumen disponible.”; el HELP de la página promete que se refresca “cada vez que se revisa o se inicia una compilación” (`gui/tab_build.py:23-25`).
- **Propuesta (Etapa 5):** refrescar al entrar al Paso 6 y al validar, con debounce ante cambios de configuración.

#### F-10. Kiosco por defecto vs modalidad explícita

- **Dónde:** `main.py:171` (`_project_type = "kiosk"`), `main.py:802` (`settings.value("project_type", "kiosk")`), `core/builders/registry.py:14` (`DEFAULT_BUILD_ENGINE = "kiosk"`).
- **Contexto:** el README explica que es compatibilidad con configuraciones 2.x; es una decisión deliberada, no un descuido.
- **Conflicto:** el Skill pide que la modalidad sea explícita y que no se seleccione Kiosco por defecto si el proyecto no lo define.
- **Propuesta:** conservar el fallback de motor para configuraciones antiguas, pero en la UI de proyecto nuevo exigir una elección explícita (Kiosco / Fedora Desktop) antes de continuar; mostrar la modalidad en el encabezado y en el resumen. No cambiar `resolve_build_engine()` sin migración documentada.

#### F-11. Dependencias de RPM local no validadas en la UI

- **Dónde:** `gui/validation.py:221-230` usa `gui.status.check_dependencies()`, que solo mira las 4 herramientas base + 3 activos syslinux (`gui/status.py:28-52`).
- **Contraste:** `core/builder.py:283-308` y `868-873` exigen `rpm` y `createrepo_c` si hay RPM local; `core/validation/diagnostics.py:20-23,74+` ya tiene esa lógica.
- **Impacto:** “Validar configuración” puede declarar todo válido y el build falla después por `createrepo_c`.
- **Propuesta (Etapa 5):** reutilizar `core.validation.diagnostics.preflight(uses_local_rpm=...)` en la validación de UI y mostrar los faltantes; no duplicar reglas.

#### F-12. Estado del pie sobrescrito por DNF en segundo plano

- **Dónde:** `gui/custom_distro.py:342` y `474-478` escriben en `lbl_wizard_status`; la consulta automática arranca en `266-274`.
- **Evidencia:** estando en Paso 1, el pie dice “Catálogo actualizado: 500 paquetes disponibles…”. Captura 03.
- **Propuesta (Etapa 2/3):** separar el estado del asistente de las notificaciones de segundo plano (bandeja/toast o barra de actividad); no reutilizar `lbl_wizard_status` para mensajes de herramientas.

#### F-13. Gestor fuera de la navegación y sin estado activo

- **Dónde:** `main.py:62-70` (NAV_ITEMS no incluye `custom_distro`), `main.py:482-484`.
- **Evidencia:** en el Gestor ninguna entrada del sidebar aparece seleccionada; el breadcrumb dice “Nuevo proyecto · Fedora a medida” mientras el título es “Gestor de software”.
- **Propuesta (Etapa 2):** agregar “Gestor de software” bajo HERRAMIENTAS o como subsección; unificar breadcrumb/título; mantener la ruta actual.

#### F-14. Modo Simple puede descartar datos sin confirmar

- **Dónde:** `main.py:592-607` decide si pedir confirmación con `_advanced_features_active()`; `main.py:628-637` solo revisa 5 checkboxes. Luego `_reset_advanced_features()` (`main.py:639-649`) limpia `txt_extra_packages`, `txt_extra_groups` y `banner_field`.
- **Escenario:** usuario cargó paquetes extra o un banner, sin tocar checkboxes; al pasar a Simple no hay advertencia y se borran.
- **Propuesta:** incluir campos de texto, banner y grupos en la detección de “features activas”, o no borrar valores al ocultarlos (conservarlos y restaurarlos al volver a Avanzado). Decidir con el usuario.

#### F-15. Brechas del Gestor frente al objetivo del Skill

| Requisito del Skill | Estado actual | Evidencia |
|---|---|---|
| Nombre, resumen, versión, arquitectura, repositorio y tipo | nombre, resumen, versión y repo; **sin arquitectura ni tipo real** | `DnfPackage` no tiene arch (`core/repositories/dnf_query.py:78-85`); `_strip_arch` la descarta (`129-134`) |
| Panel de detalles del seleccionado | solo 4 datos en un `QLabel` | `gui/custom_distro.py:511-524` |
| Instalar / quitar / actualizar / mantener | solo “Instalar” y “Grupo” | `gui/custom_distro.py:526-534` |
| Simulación inline de dependencias/conflictos | `QMessageBox` con salida cruda de DNF | `gui/custom_distro.py:536-566` |
| Ordenar/filtrar catálogo | filtros locales; sin ordenamiento por columna | no hay `setSortingEnabled` |
| Tipo de paquete real | heurística por nombre | `gui/custom_distro.py:495-499`; el CHANGELOG lo admite |
| No instalar en el host | correcto: `--assumeno` | `core/repositories/dnf_query.py:374-397` |

**Propuesta:** no inventar arquitectura, tipo ni estados de actualización. En Etapa 4, decidir entre:
1. ampliar `DnfPackage`/consulta para obtener `arch` y tipo real (cambio de backend con pruebas), o
2. mantener el alcance actual y rotularlo con honestidad (“instalación de paquetes y grupos; sin comparación con el sistema instalado”).
Para “quitar/actualizar/mantener” se necesita consultar el estado instalado y parsear la transacción; es un cambio funcional, no solo visual.

### 6.4 P3 — Calidad visual y deuda

#### F-16. Contraste y tipografía

- `MUTED` claro por debajo de 4.5:1 en `BG`/`SURFACE_ALT` (§5.6).
- Etiquetas de sección a 7.5 pt (`gui/theme.py:56`) y textos de 8–9 pt; poco legibles en HiDPI.
- `font-family: "Segoe UI", "Noto Sans"` (`gui/theme.py:52`): Segoe UI no está en Fedora; el resultado depende del fallback.
- `#c00` fijo en `gui/tab_usb.py:73`, fuera de tokens.
- Previews con `setFixedSize(360, 200)` y `(360, 160)` (`gui/tab_aesthetic.py:45`, `gui/tab_installer.py:42`); no se adaptan a HiDPI ni a ventanas angostas.

#### F-17. Inconsistencias de marca y textos

- Título de ventana: “Creador Personalizado 3.0.0-alpha.2 | **Fedora Image Studio**” (`main.py:157`), mientras la identidad es “Constructor de distribuciones Fedora”.
- Docstring del tema: “Creador-kiosk 2.0” (`gui/theme.py:1`).
- `gui/tab_usb.py:1`: “Solapa 6”, aunque USB no es el paso 6.
- `custom_distro`: breadcrumb “Nuevo proyecto · Fedora a medida” vs título “Gestor de software”.
- Duplicación de pie: botones “Volver al panel / Aplicar selección” dentro de la página (`gui/custom_distro.py:243-252`) y pie global “Guardar / Ayuda” (`main.py:252-288`).
- Uso de emojis y flechas Unicode en botones/logs; verificar que la fuente elegida los renderice en Fedora.

#### F-18. Deuda técnica con impacto en UI

- `gui/custom_distro.py:98`: `getattr(self, "combo_project_type")` sin valor por defecto; falla si cambia el orden de inicialización.
- `gui/custom_distro.py:632-636`: `_remove_custom_groups()` sin conexión visible; remoción de grupos solo vía tabla de pendientes.
- `gui/custom_distro.py:236-241`: listas ocultas conservadas por compatibilidad con pruebas/integraciones 2.x.
- Duplicación de `check_dependencies` (`gui/status.py` vs `core/validation/diagnostics.py`).
- Dos fuentes de etiquetas de navegación: `NAV_ITEMS` (`main.py:62-70`) y `STEP_LABELS` (`main.py:54-61`).
- `build/` contiene copias antiguas (`build/lib/main.py`, etc.); excluir de búsquedas y del ZIP final.
- `__pycache__`, `.pytest_cache`, `.egg-info` presentes; excluir en la entrega (Skill §11.6).

#### F-19. Pruebas lentas y poco aisladas

- 226 pruebas, 108.8 s; cada fixture de GUI crea `KioskBuilderGUI` (`tests/test_gui_smoke.py:20-27`), lo que dispara una consulta DNF real de ~3.5 s.
- No hay prueba de layout, contraste, HiDPI ni cierre con hilos activos.
- Las pruebas GUI usan `offscreen`; no reemplazan una verificación visual real.
- **Propuesta (Etapa 6):** inyectar un `DnfQuery` falso en pruebas, permitir desactivar la carga automática, separar unitarias de GUI, agregar regresiones de tamaño/contraste/cierre y una pasada manual en Wayland.

---

## 7. Funcionalidades que no deben cambiar

1. Las 9 rutas/páginas y los 8 botones del sidebar, salvo agregado aprobado del Gestor.
2. Las claves y semántica de `collect_config()` (`main.py:742-788`).
3. Las claves de `QSettings` y la regla de no persistir la contraseña.
4. Las reglas de validación por paso y el bloqueo de avance.
5. La resolución de motor y la independencia Kiosco/Desktop.
6. Las consultas DNF de solo lectura, `--assumeno` y la validación de entradas.
7. El build en segundo plano, su cancelación y las señales del worker.
8. La escritura USB: snapshot de identidad, confirmación, privilegios y verificación de lectura.
9. El hash SHA-256 en segundo plano y la invalidación por tamaño/fecha.
10. Las preferencias de tema y modo Simple/Avanzado (aunque se corrija la confirmación de datos).
11. La ayuda contextual y su asociación a cada página.
12. El requisito de que la interfaz no corra como root.

---

## 8. Qué se puede renovar sin tocar lógica

- **Tema y tokens:** `gui/theme.py` completo; agregar estilos de tabla, header, splitter, diálogos, listas, botones secundarios, estados vacío/carga/error; corregir fondos globales y contraste.
- **Componentes:** `gui/components.py`; nuevos `SectionCard`, `StatusPill`, `EmptyState`, `InlineMessage`, `DetailPanel`, `Toolbar`, `FormSection`, `ConfirmDialog`.
- **Layouts de página:** `gui/layouts.py`; ancho máximo configurable, alineación, scrollbars, contenedores adaptables.
- **Shell:** sidebar ajustable/colapsable, brand, topbar, footer adaptable, breadcrumbs, notificaciones (sin cambiar rutas ni slots).
- **Panel principal:** grilla de tarjetas que reflowe; mover acciones; usar datos reales ya disponibles; opcionalmente `BuildHistory` en modo lectura para “últimas compilaciones”.
- **Gestor:** presentación de catálogo/tabla/detalles/pendientes; estilos y adaptación; sin cambiar el backend ni inventar datos.
- **Páginas 1–6 y USB:** reorganización visual, grupos, jerarquía, textos, previews adaptables, estados; conservar señales y validaciones.
- **Accesibilidad:** tamaños, contraste, foco visible, nombres accesibles, atajos; sin cambiar comportamiento.

---

## 9. Qué requiere cambio funcional o de backend (aprobación explícita)

| Cambio | Por qué no es solo visual | Etapa propuesta |
|---|---|---|
| Esperar/cancelar `_custom_pkg_worker` al cerrar | ciclo de vida de hilos y cierre limpio | 1 (hotfix) |
| Selector de modalidad propio en Paso 1 y Gestor | estado compartido y sincronización | 2 |
| Consultas de servicios/discos en hilo | concurrencia y estados de carga | 3/5 |
| Refrescar resumen del Paso 6 | conectar navegación/validación | 5 |
| Dependencias de RPM local en validación | reutilizar preflight del core | 5 |
| Arquitectura/tipo real de paquete | ampliar `DnfPackage` y parseo DNF | 4 |
| Quitar/actualizar/mantener | consultar estado instalado y parsear transacción | 4 |
| Historial de compilaciones en el panel | leer `BuildHistory` y definir “proyecto reciente” | 2 |
| Default de modalidad | decisión de producto y compatibilidad | 2 |
| Corregir/actualizar el test que falla | expectativa del test vs default actual | 6 |

---

## 10. Propuesta de migración incremental

### Etapa 1A — Estabilización (pequeña, primero)

- Corregir cierre con DNF activo (F-01).
- Añadir prueba de cierre con worker simulado.
- Sin cambios visuales.
- **Riesgo:** bajo; solo ciclo de vida.

### Etapa 1 — Sistema visual

- Tokens completos: color, tipografía, espaciado, radios, bordes, estados.
- QSS para tablas, headers, splitter, diálogos, listas, tooltips, scrollbars, foco.
- Corregir `QWidget`/`QLabel` backgrounds; contraste; `MUTED` claro.
- Unificar componentes base y previews adaptables; eliminar colores fijos.
- **Archivos:** `gui/theme.py`, `gui/components.py`, `gui/layouts.py`, `gui/images.py`, `gui/tab_*.py` (solo estilos/estructura).
- **No tocar:** señales, validaciones, servicios.
- **Aceptación:** contraste ≥ 4.5:1; tabla oscura legible; sin barras de etiqueta; capturas claro/oscuro.

### Etapa 2 — Estructura principal

- Shell: sidebar ajustable/colapsable, brand sin recorte, topbar y footer adaptables.
- Restaurar selector de modalidad en Paso 1; sincronizar con Gestor; badge de modalidad.
- Panel principal: grilla adaptable, acciones arriba, datos reales; “últimas compilaciones” desde `BuildHistory` si se aprueba.
- Agregar Gestor a la navegación y estado activo.
- **Aceptación:** sin scroll horizontal en Dashboard a 1080×720; Gestor sin recorte a 1280×800; sidebar usable a 1080.

### Etapa 3 — Componentes adaptables

- Tablas con modelo (`QAbstractTableModel` + proxy) en lugar de `QTableWidget`; ordenamiento y filtros.
- Formularios por secciones; estados vacío/carga/error/éxito inline; diálogos homogéneos.
- Consultas de host en segundo plano con estados de carga y caché.
- **Aceptación:** tablas legibles y adaptables; operaciones largas no congelan; mensajes consistentes.

### Etapa 4 — Gestor de software

- Rediseño de catálogo/detalles/pendientes con splitter de 3 paneles y mínimos razonables.
- DNF asíncrono con cancelación, progreso y errores inline; sin carga automática invasiva o con caché.
- Simulación inline; decisiones sobre arquitectura/tipo y quitar/actualizar/mantener.
- Pruebas con `DnfQuery` inyectado; sin mocks en producción.
- **Aceptación:** datos reales, estados honestos, sin recortes a 1280×800, sin crash al cerrar.

### Etapa 5 — Resto de módulos

- Paso 1: modalidad, campos condicionales (usuario Desktop vs kiosco), textos.
- Pasos 2 y 4: previews adaptables, grupos, ayuda.
- Paso 5: servicios asíncronos y etiquetado host vs ISO.
- Paso 6: resumen siempre fresco, tarjetas de estado, consola y cancelación; preflight con RPM local.
- USB: layout adaptable, advertencia con token, estados.
- **Aceptación:** cada página usa componentes comunes; no se rompen flujos.

### Etapa 6 — Pruebas y entrega

- Pruebas de layout (1080/1280/1440), contraste, HiDPI, cierre con hilos.
- Pruebas GUI con `DnfQuery` falso y sin red.
- Pasada manual en pantalla real Wayland; capturas antes/después.
- Corregir el test preexistente o documentar su cambio.
- ZIP limpio, changelog, instrucciones, SHA-256.

---

## 11. Criterios de aceptación para la próxima entrega

- [ ] Cerrar la ventana durante una consulta DNF no aborta el proceso.
- [ ] Panel principal sin scroll horizontal a 1080×720 y 1280×800.
- [ ] Gestor sin recorte ni scroll horizontal de página a 1280×800; a 1080×720 con reflow aceptable.
- [ ] Tablas legibles en claro y oscuro; filas alternas con contraste ≥ 4.5:1.
- [ ] Etiquetas no parecen campos; encabezados de sección no parecen botones.
- [ ] “Tipo de distribución” visible y funcional en Paso 1; modalidad explícita en el encabezado.
- [ ] Marca del sidebar sin recorte a 1080.
- [ ] Acciones primarias del Panel principal visibles sin scroll a 1280×800.
- [ ] Resumen del Paso 6 completo al entrar a la página.
- [ ] Consultas de servicios no bloquean el hilo GUI.
- [ ] Se reportan igual las funcionalidades que no se probaron (ISO, USB, pantalla real).

---

## 12. Decisiones necesarias antes de la Etapa 1

1. **Modalidad por defecto:** ¿exigimos elección explícita en proyecto nuevo y conservamos Kiosco solo como fallback de configuraciones antiguas?
2. **Tamaño mínimo:** ¿mantenemos 1080×720 como piso durante la Etapa 1 y evaluamos 1024×700 después del reflow, o apuntamos ya a 1024×700?
3. **Gestor en navegación:** ¿lo agregamos al sidebar como herramienta o lo dejamos accesible solo desde el Panel principal?
4. **Alcance del Gestor:** ¿solo instalación de paquetes/grupos con etiquetado honesto, o ampliamos backend para arquitectura/tipo y quitar/actualizar/mantener en la Etapa 4?
5. **Panel principal:** ¿“proyectos recientes” o solo “últimas compilaciones” reales desde `BuildHistory`? No hay hoy un concepto persistente de proyecto más allá de `QSettings`.
6. **Paleta:** ¿conservamos el azul actual (`#0a66c2`) como acento y evolucionamos hacia azul petróleo, o adoptamos una paleta nueva completa?

---

## Anexo A — Capturas de referencia

Todas en `documentation/auditoria-etapa0/` (Qt offscreen):

| Archivo | Qué muestra |
|---|---|
| `01_dashboard_1080x720_claro.png` | scroll horizontal, badges cortados, acciones bajo el pliegue |
| `02_dashboard_1280x800_oscuro.png` | panel en oscuro, sidebar con marca cortada, jerarquía de tarjetas |
| `03_paso1_1280x800_claro_selector_vacio.png` | fila “Tipo de distribución” sin combo; pie con mensaje DNF |
| `04_gestor_1280x800_oscuro_recorte.png` | descripción comprimida, botón cortado, scroll horizontal |
| `05_gestor_1080x720_oscuro_scroll.png` | recorte severo a 1080; combo de perfil dominante |
| `06_paso6_1280x800_claro.png` | resumen vacío; etiquetas con fondo de barra |
| `07_tabla_oscuro_filas_ilegibles.png` | fila alterna clara con texto claro (1.10:1) |
| `08_tabla_claro.png` | tabla en tema claro como referencia |

## Anexo B — Comandos de reproducción

```bash
cd Creador-Personalizado-3.0.0-alpha.2

# Línea base de pruebas (offscreen)
QT_QPA_PLATFORM=offscreen python3 -m pytest -q

# Prueba de cierre con DNF activo (aborta con 134)
PYTHONPATH=. QT_QPA_PLATFORM=offscreen python3 /tmp/opencode/audit_close.py

# Mediciones de layout y paletas usadas en este informe
PYTHONPATH=. QT_QPA_PLATFORM=offscreen python3 /tmp/opencode/audit_layout.py
PYTHONPATH=. QT_QPA_PLATFORM=offscreen python3 /tmp/opencode/audit_contrast.py
```

> Los scripts de medición se dejaron en `/tmp/opencode/` y no forman parte de la aplicación. Las capturas y este informe sí se guardaron en `documentation/`.
