# Informe técnico — Etapa 7

## Resultado

Se incorporó la primera versión funcional del almacenamiento de proyectos independientes y la precarga de los cinco perfiles nominales existentes, además de seis plantillas generales.

## Arquitectura

`core/projects/manager.py` implementa `ProjectStore` sin dependencia de Qt. Cada proyecto se identifica con UUID y contiene un manifiesto JSON independiente. El manifiesto se escribe de forma atómica. Los recursos de imagen y las aplicaciones locales seleccionadas se copian a `assets/` y se referencian con rutas relativas dentro del archivo.

La GUI ofrece **Nuevo proyecto**, **Abrir proyecto** y **Guardar proyecto**. Al crear un proyecto, el nombre se usa para completar la identidad ISO/producto y el texto de bienvenida. La plantilla define motor, paquetes sugeridos, escritorio, cuenta, arranque y opciones iniciales de seguridad. Los cinco perfiles nominales se leen de sus JSON existentes y conservan URL, modo multiventana, arranque y opciones SSH/firewall originales. El directorio `builds/` del proyecto se usa como destino inicial de ISO.

Al guardar, abrir, compilar o cerrar, la configuración del proyecto activo se persiste en su propio `project.json`. El último proyecto abierto se recuerda en QSettings. Las contraseñas no se guardan y se limpian al cambiar de proyecto.

## Archivos principales
- `core/projects/manager.py` — nuevo almacenamiento.
- `core/projects/catalog.py` — defaults explícitos por perfil.
- `main.py` — flujo GUI de nuevo/abrir/guardar y aplicación de configuración.
- `tests/test_project_store.py` — pruebas nuevas.
- `documentation/ETAPA7_GESTION_PROYECTOS.md` — documentación de uso y límites.

## Pruebas
- `python -m compileall -q main.py core gui tests`: correcto.
- `python -m pytest -q tests/test_project_store.py`: 4 passed.
- Suite completa: no se pudo recolectar en este entorno por ausencia de PySide6. El usuario debe ejecutar `./scripts/run_acceptance.sh` en Fedora 44.
- No se ejecutó GUI real, HiDPI ni generación de ISO.

## Pendientes antes de declarar la etapa cerrada
- Ejecutar suite completa en Fedora 44.
- Probar manualmente creación de dos proyectos con perfiles diferentes, alternancia, reinicio y recuperación de ambos.
- Verificar que la compilación de cada proyecto consuma su propio `project.json` y recursos.
- Diseñar una migración explícita de preferencias heredadas a un proyecto inicial, sin sobrescribir información.
