# Etapa 6 — Pruebas y entrega

Base: Creador Personalizado 3.0.0-alpha.3.

## Agregado

- `INFORME_ETAPA6.md`: informe de validación automatizada, resultados y limitaciones.
- `documentation/GUIA_VALIDACION_FEDORA44_ETAPA6.md`: procedimiento reproducible de aceptación manual y GUI en Fedora 44.

## Validaciones ejecutadas

- 111 pruebas pytest pasaron en el subconjunto compatible con el entorno.
- `compileall` completado correctamente.
- Sintaxis de scripts shell comprobada con `bash -n`.
- Wheel Python construido correctamente.

## Limitaciones

PySide6 no estaba instalado en el entorno de ejecución. Las pruebas Qt, la inspección visual real, redimensionado/HiDPI y las compilaciones ISO deben completarse en Fedora 44. No se afirma que se haya generado o probado una ISO.

## Compatibilidad

No se modificaron los motores Desktop/Kiosco ni los contratos de configuración para esta etapa de pruebas y documentación.
