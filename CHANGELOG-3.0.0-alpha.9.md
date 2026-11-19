# Creador-Personalizado 3.0.0-alpha.9

## Auditoría rápida de imágenes ISO

- Nuevo módulo `core.iso.quick_audit` para inspeccionar el catálogo ISO con `xorriso`.
- Validación de los archivos `grub.cfg` con `grub2-script-check` o `grub-script-check`.
- Extracción temporal y listado de `squashfs.img` con `unsquashfs -ll`, sin modificar la ISO original.
- Acción **Auditoría rápida de ISO** en el paso 6, con ejecución en un hilo separado para mantener la interfaz receptiva.
- Nuevo comando: `python scripts/validate_iso.py imagen.iso --quick`.
- GitHub Actions: pruebas y comprobaciones estáticas en push/PR a `main`; prueba QEMU manual mediante URL HTTPS directa de ISO.

## Interpretación de resultados

- `PASS`: las comprobaciones disponibles se completaron correctamente.
- `WARN`: faltan herramientas o componentes opcionales; no equivale a certificación completa.
- `FAIL`: se detectaron errores estructurales o de sintaxis.
- `UNAVAILABLE`: no se pudo ejecutar la inspección principal.

La duración de la auditoría depende del tamaño y estructura de la ISO, especialmente del tamaño de `squashfs.img`. No certifica el arranque ni el funcionamiento del sistema en hardware real. La prueba QEMU es una comprobación separada y tampoco sustituye pruebas físicas.

## Seguridad

La auditoría es de solo lectura sobre la ISO original. Los archivos inspeccionados se extraen a un directorio temporal que se elimina al finalizar. No se ejecutan scripts de la ISO, no se escriben discos y no se cambia la política de verificación de RPM.
