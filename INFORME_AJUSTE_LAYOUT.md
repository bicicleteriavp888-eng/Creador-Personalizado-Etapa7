# Informe de ajuste visual y distribución de pestañas

**Proyecto:** Creador-kiosk  
**Base:** paquete Profesional Fedora 44  
**Fecha:** 12 de noviembre de 2026  
**Tipo de cambio:** corrección de interfaz y distribución; no modifica el backend de generación de ISO.

## Problema observado

La interfaz tenía un tema visual coherente, pero varias pestañas concentraban demasiados controles con márgenes y separaciones insuficientes. Además, no todas las páginas tenían desplazamiento vertical uniforme, por lo que en ventanas pequeñas algunos controles podían quedar fuera del área visible.

## Cambios aplicados

1. Se agregó `gui/layouts.py` para centralizar la composición de las pestañas.
2. Las seis pestañas ahora se alojan en áreas desplazables verticalmente.
3. Se aplicaron márgenes exteriores consistentes y mayor separación entre controles.
4. Los formularios ahora alinean las etiquetas, expanden los campos y mantienen una separación horizontal y vertical uniforme.
5. Los grupos (`QGroupBox`) reciben márgenes interiores y espaciado propio para separar visualmente sus controles.
6. Se limitó el ancho máximo del contenido y se centra dentro de la pestaña para evitar líneas excesivamente largas en pantallas grandes.
7. Se mejoraron las barras de desplazamiento y el espaciado de los elementos del tema.
8. La barra de pestañas permite desplazamiento horizontal cuando no entran todas las solapas.
9. Se actualizó la referencia interna de la pestaña USB para que el refresco automático siga funcionando al estar envuelta en un `QScrollArea`.

## Archivos modificados

- `gui/layouts.py` (nuevo)
- `gui/theme.py`
- `gui/tab_meta.py`
- `gui/tab_aesthetic.py`
- `gui/tab_software.py`
- `gui/tab_installer.py`
- `gui/tab_build.py`
- `gui/tab_usb.py`
- `main.py`

## Validación

- `python -m compileall -q .`: correcto.
- Ejecución de `pytest`: no pudo completar la recolección porque el entorno de auditoría no tiene instalado PySide6 (`ModuleNotFoundError`). No se presenta como una falla de los tests del proyecto.
- No se pudo abrir la GUI en este entorno, por lo tanto el ajuste visual requiere una comprobación final en Fedora 44 con PySide6 instalado.

## Prueba recomendada en Fedora 44

Desde el directorio del proyecto:

```bash
python -m pip install -r requirements.txt
python main.py
```

Comprobar las seis pestañas, reducir el tamaño de la ventana, desplazarse hasta el final de cada página y confirmar que los botones, campos, previsualizaciones, registros y acciones USB siguen accesibles. En particular, entrar en la pestaña USB y verificar que la lista de dispositivos se actualiza al abrirla.

## Alcance y cautelas

Este ajuste se concentra en el orden visual, el espaciado y el desplazamiento. No cambia las opciones de construcción, los comandos del sistema, la configuración Kickstart ni la escritura USB. La apariencia final puede variar ligeramente según el tema Qt y las fuentes instaladas en Fedora.
