# Creador Personalizado 3.0.0-alpha.7

## Aislamiento del motor Kiosco

- La configuración de aplicación principal y multiventana se trasladó a una página independiente `Configuración Kiosco`.
- La página aparece solo con perfiles del motor Kiosco; no se puede abrir desde un perfil Fedora Desktop.
- El paso 3 conserva el acceso principal al gestor de software Fedora y las opciones de escritorio Wayland/X11 para Desktop.
- La cuenta de escritorio se oculta para Kiosco.
- El bloqueo de consolas virtuales se separa como protección propia de Kiosco.
- La resolución wlr-randr se oculta en perfiles Desktop.
- Los privilegios sudo se mantienen compartidos porque ambos motores los implementan.

## Personalización independiente del instalador

- El banner y el texto de bienvenida permanecen visibles en modo Simple y ya no se borran al cambiar desde Avanzado.
- Cada proyecto conserva su propio `installer_banner` y `installer_text`.
- Al abrir proyectos antiguos sin texto de bienvenida, se crea un mensaje predeterminado con el nombre del proyecto abierto, evitando arrastrar el texto de otra distribución.
- Se conserva correctamente el identificador de los perfiles nombrados al crear proyectos.
- Fedora Desktop incorpora el banner en los recursos de Anaconda y el texto en su directorio de ayuda y en una copia propia del proyecto.
- La personalización del instalador solo se incluye cuando Anaconda está habilitado; se valida la existencia y el tamaño máximo de 4 MiB del banner.
- Kiosco conserva su implementación de personalización Anaconda.

## Pruebas añadidas

- Aislamiento de banner y bienvenida entre proyectos Kiosco y Desktop.
- Generación de Kickstart Desktop con banner y texto personalizados.
- Omisión del branding con Anaconda deshabilitado.
- Rechazo de imagen inexistente.
- Pruebas GUI para visibilidad de la página Kiosco según el motor y conservación del banner en modo Simple.

## Validación

En el entorno de edición: 46 pruebas aprobadas en identidad, proyectos y motor Desktop; una prueba se excluyó porque importa `core.builder`, que requiere PySide6 y no está instalado en este entorno. Compilación sintáctica de todos los módulos Python: correcta.

La suite GUI y la suite completa deben ejecutarse en Fedora con PySide6. La generación y prueba de ISO Kiosco y Desktop también queda pendiente.
