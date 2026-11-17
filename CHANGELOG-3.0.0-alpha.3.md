# Creador Personalizado 3.0.0-alpha.3

## Etapa 5 — Renovación de los módulos restantes

### Identidad
- Reorganiza los campos en secciones de identidad, plataforma/arranque y cuenta de escritorio.
- Mantiene los mismos nombres de atributos, datos de combos y contratos usados por `collect_config()`.
- Conserva la visibilidad condicional de la contraseña según el motor Desktop/Kiosco y el modo Simple/Avanzado.

### Apariencia
- Agrupa la personalización de Plymouth y la resolución de pantalla.
- Sustituye las dimensiones fijas de la vista previa por límites adaptables.
- Conserva `ImageField`, la conversión de imágenes y el límite de tamaño existente.

### Instalador
- Separa la activación de Anaconda, el banner y el mensaje de bienvenida.
- Adapta la vista previa y el área de texto a la página.
- Mantiene los controles y datos existentes (`check_enable_installer`, `banner_field`, `txt_installer_text`).

### Seguridad
- Agrupa protección de red/acceso remoto y privilegios/acceso local.
- Mejora los textos de ayuda y el estado de servicios del host.
- Conserva los valores predeterminados y las conexiones de señales existentes.

### USB
- Mejora la jerarquía de selección de ISO, dispositivo, confirmación, progreso y registro.
- Limita el ancho mínimo del selector de dispositivo para evitar que rutas/modelos extensos fuercen scroll horizontal.
- No cambia la enumeración de discos, la confirmación destructiva ni `USBWriterWorker`.

### Compilación y validación
- Reorganiza destino, resumen, validación y ejecución en secciones diferenciadas.
- Conserva los métodos de validación, inicio, cancelación y finalización.
- Da más espacio útil al registro de compilación.

### Componentes comunes
- Añade `configure_image_preview()` para que las vistas previas no impongan dimensiones rígidas.
- Actualiza la versión de paquete y el título a `3.0.0-alpha.3`.

## Verificación
- `compileall` sobre `main.py`, `gui`, `core` y `scripts`: correcto.
- Parseo AST de los módulos modificados: correcto.
- Suite pytest: no pudo recolectarse en este entorno porque falta PySide6 (`ModuleNotFoundError`). No se afirma prueba gráfica ni ejecución real de Qt.
- No se ejecutó compilación ISO ni escritura USB.
