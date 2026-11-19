# Cambios de interfaz — alpha.6

## Paso 3: Software

Se quitó de la interfaz visible el grupo «Aplicación en Kiosco». El paso muestra el bloque «Software de la distribución» con el resumen de paquetes y grupos, más el botón «Abrir gestor de software Fedora». Los campos históricos de aplicación se mantienen ocultos en el árbol de widgets para preservar la lectura de proyectos Kiosco anteriores; no son un segundo selector visible.

El bloque de multiventana se mantiene para el motor Kiosco. En modo Fedora Desktop se ocultan los controles específicos de Kiosco y se muestra el bloque «Escritorio de la distribución».

## Wayland y X11

El selector muestra ambas opciones y deshabilita las que no están disponibles para el entorno elegido según el catálogo Fedora 44 consultado el 17-11-2026:

- GNOME: Wayland. Fedora eliminó el soporte de sesión GNOME X11 desde Fedora 43.
- KDE Plasma: Wayland. La variante X11 `plasma-workspace-x11` dejó de estar disponible como opción mantenida para la actualización actual de Fedora 44 (fue obsoletada en la serie 6.8.1).
- Xfce: X11.

La selección `display_server` se persiste en el proyecto y se entrega al validador y al generador Kickstart. Una combinación no admitida se rechaza antes de compilar.

## Validación local

- `python3 -m compileall -q main.py gui core tests`: correcto.
- `PYTHONPATH=. python3 -m pytest -q tests/test_desktops.py tests/test_software_policy.py -k 'not test_el_perfil_kiosco_conserva_sus_componentes'`: 41 aprobadas, 1 omitida.
- La prueba omitida y las pruebas GUI necesitan PySide6; esta sesión de trabajo no tiene ese paquete. Ejecutar la suite completa en Fedora antes de dar por validada la alpha.6.
