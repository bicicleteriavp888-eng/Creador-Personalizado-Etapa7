# Mejoras alpha.8 — diagnóstico, compilación y reproducibilidad

## Validación Kickstart
Antes de invocar `livecd-creator`, cada motor valida el archivo ya escrito. Si `ksvalidator` está disponible, ejecuta la versión Fedora seleccionada. Si falta, se ejecuta un análisis estructural interno y la GUI/registro lo identifica como tal; nunca se afirma que la validación oficial fue exitosa.

## Hardware y perfiles
El escáner es de solo lectura y usa `lspci -nnk` y `lsusb`. Las sugerencias se limitan a paquetes base conocidos. Los controladores propietarios o dependientes de repositorios externos quedan marcados para revisión. Los perfiles JSON incluyen resolución, paquetes seleccionados y diagnóstico detectado.

## Caché y modo sin conexión
`livecd-creator` ya utilizaba caché persistente; ahora la GUI permite desactivarla y consultar ruta/tamaño, y el backend permite elegir `cache_dir`. Se admite `CREADOR_CACHE_DIR` y se conserva `KIOSK_CACHE_DIR` como compatibilidad. **No se declara un modo offline completo**: que exista caché no garantiza que estén presentes todos los metadatos, RPM y dependencias requeridos por DNF. Forzar aislamiento de red podría producir una compilación aparentemente iniciada que luego falle por dependencias faltantes.

## Instalación desatendida
No se agrega una entrada Kickstart automatizada a la Live ISO: Anaconda documenta que las instalaciones Kickstart no están soportadas desde Live OS. Para despliegues desatendidos se debe preparar un medio Netinstall, estándar o `boot.iso` y validar allí la receta. Creador-Personalizado rechaza esta opción en el perfil Live para evitar una falsa sensación de automatización.

## QEMU
`--qemu-smoke` ejecuta una prueba acotada. Un marcador serial permite reportar `BOOT_MARKER_FOUND`; una captura con actividad de vídeo se reporta como `DISPLAY_ACTIVITY_DETECTED`, sin afirmar que el escritorio/Anaconda completó el arranque. Si no hay evidencia se reporta `NO_BOOT_EVIDENCE`. UEFI requiere OVMF (`edk2-ovmf`).

## CLI y modelo de datos
`BuildConfig` modela los campos de configuración principales y conserva las claves heredadas. La GUI mantiene temporalmente el contrato de diccionario para compatibilidad. La compilación headless lee `project.json` y usa el mismo registro de motores.

## Refactorización GUI
La conversión total de mixins a componentes QWidget independientes no se fuerza en esta alpha: la GUI contiene callbacks y estado compartido entre páginas. Se incorpora el modelo tipado y se conserva el comportamiento hasta poder migrar cada página con pruebas de regresión específicas.
