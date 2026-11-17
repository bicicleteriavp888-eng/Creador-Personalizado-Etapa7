# Creador Personalizado 3.0.0-alpha.1

## Nueva identidad
- Nombre de producto: Creador Personalizado.
- Subtítulo: Constructor de distribuciones Fedora.
- Lema: Tu distribución, tus reglas.
- Ventana y cabecera lateral actualizadas.
- Nuevo icono SVG y entrada de escritorio.

## Empaquetado y compatibilidad
- Nombre de paquete Python: `creador-personalizado`.
- Nuevos comandos: `creador-personalizado` y `creador-personalizado-validate-iso`.
- Se conservan alias `creador-kiosk*` durante la migración.
- Se conservan rutas internas históricas y QSettings para no perder preferencias ni datos existentes.
- Instalación Fedora usa `/opt/creador-personalizado`.

## Arquitectura
- Se incorpora `documentation/ARQUITECTURA_3.0.md` con estado comprobado, arquitectura objetivo, principios, etapas y criterios de aceptación.
- No se declara completada la independencia del ciclo de construcción: Desktop todavía hereda de `KioskISOBuilder` en esta base.

## Pruebas y límites
- Esta entrega no acredita generación ni arranque de ISO.
- Ejecutar `python -m compileall -q .` y `python -m pytest -q` en Fedora 44 con PySide6 y dependencias disponibles.
