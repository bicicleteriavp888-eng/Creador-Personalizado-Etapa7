# Creador Personalizado 3.0.0-alpha.5

## Gestor de software

- Se agrega desde el paso 3 un acceso directo al gestor Fedora compartido.
- Los campos de paquetes y grupos del asistente quedan como resúmenes de solo lectura.
- Aplicar la selección desde el gestor devuelve al paso 3 para continuar el asistente.
- Se documenta el estado real de los seis pasos de unificación y sus pendientes.

## Validación

- `python -m compileall -q gui core`: correcto.
- `PYTHONPATH=. pytest -q tests/test_software_policy.py tests/test_dnf_query.py tests/test_project_templates.py`: 33 pruebas aprobadas.
- La suite completa y la GUI no se validaron en este entorno por ausencia de PySide6.
- No se declara completada la integración de extremo a extremo ni la instalación dentro de imágenes.
