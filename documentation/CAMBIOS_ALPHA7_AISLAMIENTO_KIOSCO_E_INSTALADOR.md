# Creador Personalizado 3.0.0-alpha.7

## Objetivo

Separar la configuración propia del motor Kiosco de las opciones Fedora Desktop y recuperar la personalización de Anaconda por proyecto/distribución.

## Cambios de interfaz

- El paso 3 permanece dedicado al gestor de software Fedora y a la elección de escritorio Wayland/X11 para Desktop.
- La configuración de aplicación principal y multiventana de Kiosco se movió a una página independiente `Configuración Kiosco`, visible únicamente cuando el perfil activo usa el motor Kiosco.
- La página `Configuración Kiosco` no forma parte de la secuencia numerada de seis pasos; se abre desde la navegación lateral.
- Los controles de cuenta de escritorio se ocultan en Kiosco.
- Las opciones de terminal Kiosco (bloqueo de consolas virtuales) se separan de los privilegios Desktop.
- La resolución wlr-randr se oculta en perfiles Desktop.
- El banner y el texto de bienvenida del instalador permanecen visibles también en modo Simple; no se borran al cambiar de modo.

## Personalización por proyecto

- `installer_banner` se copia dentro de `assets/installer_banner/` en el proyecto y se restaura al abrirlo.
- `installer_text` se guarda en `project.json` como parte de la configuración del proyecto.
- Al abrir un manifiesto antiguo sin `installer_text`, se genera un mensaje predeterminado con el nombre de ese proyecto, evitando reutilizar el texto del proyecto abierto anteriormente.
- Se corrigió la conservación de `profile_id` al aplicar una plantilla nombrada.

## Integración en motores

- Kiosco conserva su implementación de banner y bienvenida en `KioskISOBuilder`.
- Fedora Desktop incorpora banner en `/usr/share/anaconda/pixmaps/` y texto en `/usr/share/anaconda/help/welcome.txt`, además de una copia de referencia en `/etc/creador-personalizado/installer-message.txt`.
- La personalización se omite cuando Anaconda está deshabilitado.
- Se valida que el banner exista y no supere 4 MiB.

## Pruebas añadidas

- Aislamiento de los activos y textos de instalador entre dos proyectos.
- Generación de Kickstart Desktop con banner y bienvenida personalizados.
- Omisión del branding cuando Anaconda está deshabilitado.
- Rechazo de un banner inexistente.
- Pruebas GUI para visibilidad del panel Kiosco según el motor y persistencia de la personalización en modo Simple.

## Validación pendiente en Fedora del usuario

Este entorno de edición no dispone de PySide6, por lo que las pruebas GUI y la suite completa no se ejecutaron aquí. En Fedora ejecutar:

```bash
python3 -m pytest -q
```

Después verificar manualmente:

1. Crear un proyecto Kiosco: debe aparecer `Configuración Kiosco` y no deben aparecer las opciones de cuenta/escritorio Desktop.
2. Crear un proyecto Desktop (oficina): debe desaparecer `Configuración Kiosco`, mostrar escritorio y servidor gráfico, y no mostrar controles de aplicación Kiosco.
3. Personalizar banner y bienvenida en ambos proyectos, guardar, abrir el otro proyecto y volver al primero: cada uno debe recuperar sus propios valores.
4. Cambiar a modo Simple: banner y texto del instalador deben seguir visibles y conservarse.
5. Generar Kickstart Desktop y comprobar que incluye el banner y el mensaje propios de ese proyecto.
6. Generar ISO Kiosco y Desktop por separado para validar el resultado real de Anaconda.

No se declara validada la generación física de ISO en esta entrega.
