# Cambios — Etapa 7

## Añadido
- Gestor de proyectos local con creación, listado, apertura y guardado independiente.
- Manifiesto `project.json` por proyecto con escritura atómica y UUID.
- Carpetas propias `assets/`, `builds/` y `logs/`.
- Copia de imágenes y recursos locales de aplicaciones al directorio del proyecto.
- Precargas nominales integradas desde `profiles/*.json`: Terminal de Atención, Kiosco Navegador, Kiosco Multiventana, Equipo de Oficina y Estación de Trabajo.
- Se mantienen también seis plantillas generales: Kiosco, Oficina, Web, Gaming, Laboratorio de ciberseguridad y Personalizado.
- Restauración del último proyecto abierto y guardado al compilar/cerrar.
- Limpieza de contraseña en memoria al cambiar de proyecto; no se persisten contraseñas ni secretos.
- Seis pruebas unitarias nuevas para aislamiento, recursos, validación de nombre, perfiles nominales y rutas de compilación portables.

## Compatibilidad
- Se mantienen los motores Fedora Desktop y Kiosco separados.
- Se mantienen QSettings para preferencias de interfaz y compatibilidad con configuraciones heredadas.
- Versión del paquete: `3.0.0a4`.

## Validación realizada en el entorno de preparación
- `compileall`: correcto.
- `tests/test_project_store.py`: 4 aprobadas.
- Suite completa: no ejecutable en este entorno porque no está instalado PySide6; la revalidación integral debe hacerse en Fedora 44.
- GUI Qt real, redimensionado/HiDPI y compilación ISO: no ejecutados aquí.
