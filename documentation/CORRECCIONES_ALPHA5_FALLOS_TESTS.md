# Correcciones de pruebas — Creador Personalizado 3.0.0-alpha.5

## Fallo 1: identidad y versión

La prueba `tests/test_branding_3.py::test_pyproject_uses_new_product_identity_and_keeps_legacy_cli` esperaba `3.0.0a4`, aunque `pyproject.toml` declara `3.0.0a5`. Se actualizó la expectativa a `3.0.0a5`. No se modificó la versión del producto.

## Fallo 2: resolución del motor en la GUI

`KioskBuilderGUI._selected_build_engine()` pasaba el valor auxiliar `_build_engine` junto con `_project_type` a `resolve_build_engine()`. El resolvedor genérico da prioridad al motor explícito. Por eso un `_build_engine` residual igual a `kiosk` podía imponerse a un perfil `office`, cuyo motor declarado es `desktop`.

La GUI ahora obtiene el motor del catálogo del perfil activo (`get_project_template(project_type)`) y utiliza ese valor para resolver el constructor. Se conserva el resolvedor genérico sin cambios para configuraciones persistidas y consumidores externos. Se mantiene una salida defensiva para tipos de proyecto antiguos o desconocidos.

Se agregó `test_collect_config_prioriza_perfil_si_motor_auxiliar_quedo_desactualizado` para cubrir el caso de regresión.

## Verificación realizada en el entorno de preparación

- `python3 -m py_compile main.py tests/test_gui_smoke.py tests/test_branding_3.py`: correcto.
- `python3 -m pytest -q tests/test_branding_3.py`: 3 passed.
- La ejecución de pruebas que requieren PySide6 no pudo completarse en este entorno porque el intérprete Python 3.13 disponible no tiene instalado PySide6.
- Por la misma limitación, el resultado previo de 242 passed / 2 failed comunicado desde el Fedora del usuario todavía debe repetirse allí con estos cambios.

## Validación pendiente en Fedora

Desde la raíz del proyecto:

```bash
python3 -m pytest -q tests/test_branding_3.py tests/test_gui_smoke.py
python3 -m pytest -q
```

Resultado esperado: que desaparezcan los dos fallos originales y que la nueva prueba de regresión también pase. Registrar el resultado real antes de declarar cerrada esta corrección.
