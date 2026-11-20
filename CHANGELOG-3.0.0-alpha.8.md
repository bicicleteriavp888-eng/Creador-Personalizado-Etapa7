# Creador-Personalizado 3.0.0-alpha.8

## Nuevas capacidades

- Validación previa del Kickstart con `ksvalidator` cuando está instalado y comprobación estructural interna como fallback explícito.
- Vista previa del Kickstart desde el paso de compilación.
- Escáner PCI/USB no invasivo (`lspci -nnk`, `lsusb`) con sugerencias conservadoras para Fedora; los drivers propietarios/externos se marcan como manuales.
- Exportación e importación de perfiles de hardware JSON con resolución y paquetes seleccionados.
- Caché persistente configurable para `livecd-creator`; puede desactivarse y consultarse desde el paso de compilación. No se promete modo offline completo.
- Modo de compilación por consola: `python3 main.py --build /ruta/proyecto/project.json --headless`.
- Prueba QEMU opcional: `python3 main.py --qemu-smoke imagen.iso --firmware bios|uefi`.
- Modelo tipado `BuildConfig` para normalizar y validar configuración conservando claves de compatibilidad.

## Seguridad y límites

- El escáner no instala paquetes ni habilita repositorios.
- `akmod-nvidia`/`akmod-wl` se sugieren como acciones manuales que requieren RPM Fusion; no se agregan automáticamente.
- El modo Kickstart desatendido desde Live ISO se rechaza porque Anaconda no lo soporta en medios Live; requiere Netinstall, ISO estándar o `boot.iso`.
- QEMU distingue `BOOT_MARKER_FOUND`, `DISPLAY_ACTIVITY_DETECTED` y `NO_BOOT_EVIDENCE`; la actividad de vídeo no certifica que el escritorio o Anaconda hayan terminado de arrancar.
- La política de verificación RPM no se modificó.
- La caché se conserva entre builds; no se limpia automáticamente.
- La conversión completa de los ocho mixins heredados a widgets independientes queda pendiente: esta alpha incorpora el modelo tipado como primer paso sin arriesgar el flujo GUI existente.

## Actualización de laboratorio: auditoría rápida de ISO

- Nuevo módulo `core.iso.quick_audit`: inspección del catálogo con `xorriso`, validación sintáctica de `grub.cfg` con `grub2-script-check` y listado/verificación estructural de `squashfs.img` con `unsquashfs -ll`.
- Nueva acción **Auditoría rápida de ISO** en el paso 6, ejecutada en un hilo de trabajo para no congelar la GUI. Permite auditar la última ISO o seleccionar otra.
- Nuevo comando `python scripts/validate_iso.py imagen.iso --quick` con informe JSON.
- Nuevo workflow GitHub Actions para pruebas en cada push/PR a `main`; la prueba QEMU se puede lanzar manualmente aportando una URL HTTPS de ISO.
- Los estados PASS/WARN/FAIL/UNAVAILABLE distinguen validación completa, avisos por herramientas ausentes y errores. La auditoría rápida no afirma que la ISO haya arrancado.
