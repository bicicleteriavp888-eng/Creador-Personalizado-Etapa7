# Informe de entrega — Etapa 5

**Producto:** Creador Personalizado 3.0.0-alpha.3  
**Base:** 3.0.0-alpha.2 adjunta  
**Plataforma objetivo:** Fedora 44  
**Alcance:** identidad, apariencia, instalador, seguridad, USB y compilación/validación.

## 1. Objetivo

Completar la renovación visual de los módulos restantes con una jerarquía homogénea, distribución por propósito y controles adaptables, preservando la lógica y los contratos de la aplicación.

## 2. Cambios realizados

| Módulo | Cambios | Lógica preservada |
|---|---|---|
| Identidad | Secciones separadas para identidad, plataforma/arranque y cuenta | `combo_project_type`, `combo_base`, `combo_boot`, campos y callbacks existentes |
| Apariencia | Panel Plymouth y panel de resolución; vista previa adaptable | `ImageField`, conversión y límite de imagen, `combo_res` |
| Instalador | Activación Anaconda, banner y bienvenida en secciones | `check_enable_installer`, `banner_field`, `txt_installer_text` |
| Seguridad | Agrupación de red/SSH y privilegios/consolas | Checkboxes, señales y consulta de servicios del host |
| USB | Jerarquía ISO → destino → advertencia/confirmación → progreso/log | `list_usb_disks`, `USBWriterWorker`, snapshot de dispositivo y confirmación |
| Compilación | Destino, resumen, validación y salida en paneles | `validate_configuration`, `start_build_process`, `cancel_build`, `build_finished` |

## 3. Archivos modificados

- `gui/tab_meta.py`
- `gui/tab_aesthetic.py`
- `gui/tab_installer.py`
- `gui/tab_security.py`
- `gui/tab_usb.py`
- `gui/tab_build.py`
- `gui/components.py`
- `main.py` (título de versión)
- `pyproject.toml` (versión 3.0.0a3)
- `README.md` (versión)
- `tests/test_branding_3.py` (versión esperada)

Se agregan `CHANGELOG-3.0.0-alpha.3.md` e `INFORME_ETAPA5.md`.

## 4. Seguridad y compatibilidad

- No se modificaron los motores de construcción Desktop ni Kiosco.
- No se cambió el backend de escritura USB ni su procedimiento de validación del dispositivo.
- No se cambió la semántica de los valores enviados a `collect_config()`.
- No se persiste la contraseña del usuario.
- Las operaciones largas siguen delegadas en los workers existentes.
- Se eliminan las vistas previas de tamaño fijo; se usa una política de tamaño mínimo/máximo adaptable.

## 5. Pruebas y limitaciones

| Comprobación | Resultado |
|---|---|
| `python -m compileall -q main.py gui core scripts` | Correcto |
| Parseo AST de módulos modificados | Correcto |
| `pytest -q` | Bloqueado al recolectar: falta PySide6 en el entorno (`ModuleNotFoundError`) |
| GUI Qt offscreen / redimensionado real | No ejecutado |
| Fedora 44 / DNF / compilación ISO | No ejecutado |
| Escritura física USB | No ejecutada |

La prueba `pytest` se intentó y falló por una dependencia ausente, no por un fallo demostrado en la aplicación. Es necesario repetirla en el Fedora 44 del usuario con las dependencias del proyecto instaladas.

## 6. Próxima validación recomendada

1. Instalar las dependencias de `requirements.txt` en el entorno de Fedora 44.
2. Ejecutar `pytest -q`.
3. Abrir la GUI y revisar cada módulo en 1080×720, 1280×800 y 1600×900, en tema claro y oscuro.
4. Cambiar entre modo Simple/Avanzado y comprobar la visibilidad de opciones.
5. Verificar la selección y limpieza de imágenes sin compilar una ISO.
6. Enumerar USB y comprobar la selección; no iniciar escritura salvo con un dispositivo de prueba prescindible.
7. Ejecutar una compilación de prueba solo cuando las dependencias Fedora estén disponibles.

## 7. Resultado

La Etapa 5 queda implementada a nivel de estructura y código de interfaz. La aceptación visual definitiva queda pendiente de la ejecución Qt real y de las pruebas en Fedora 44; no se declara validación funcional completa hasta realizar esas comprobaciones.
