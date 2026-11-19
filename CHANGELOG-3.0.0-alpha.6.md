# Creador Personalizado 3.0.0-alpha.6

## Paso 3 · Software y escritorio

- Se retira de la interfaz visible el grupo «Aplicación en Kiosco». Se conservan internamente los campos históricos para que los proyectos Kiosco existentes mantengan compatibilidad.
- El paso 3 presenta el acceso «Abrir gestor de software Fedora» y los resúmenes de paquetes y grupos seleccionados.
- El bloque de escritorio permite elegir el entorno y muestra las opciones Wayland/X11; las combinaciones no disponibles se deshabilitan.
- La selección del servidor gráfico se guarda en la configuración del proyecto, preferencias y resumen de compilación.
- El motor Fedora Desktop valida el servidor seleccionado y lo incorpora a la resolución de paquetes y a la receta Kickstart.
- En Fedora 44 actual, GNOME y KDE Plasma se ofrecen con Wayland; Xfce utiliza X11.

## Pruebas

- `compileall`: correcto.
- Pruebas de escritorio y política de software ejecutadas en este entorno: 41 aprobadas, 1 omitida porque requiere importar el constructor Kiosco y PySide6 no está instalado aquí.
- Las pruebas de interfaz Qt y la suite completa deben repetirse en Fedora con PySide6.
