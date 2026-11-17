# Nuevo proyecto: Fedora a medida

Se incorpora al panel principal el acceso **Nuevo proyecto · Fedora a medida**.
La página consulta los repositorios DNF habilitados en el equipo mediante
`dnf repoquery`, permite buscar por nombre o descripción, seleccionar varios
paquetes, agregarlos/quitarles de la selección y transferir la lista al campo
`Paquetes adicionales` del asistente existente.

La consulta de repositorios se ejecuta en un QThread para no bloquear la GUI.
La compilación vuelve a resolver los paquetes contra los repositorios Fedora;
la selección local no sustituye la resolución de dependencias de DNF.

## Alcance de esta entrega

Esta primera integración añade el explorador de paquetes y conecta la selección
con el flujo de compilación existente de Creador-kiosk. El motor de imagen
conectado a la interfaz sigue generando la base Live/kiosco que ya tenía el
proyecto; todavía no es un perfil Fedora genérico independiente de Cage/Sway,
usuario kiosco y servicios de kiosco. La versión 2.5 incorpora un motor Fedora
Desktop independiente en `core/desktops/`, su integración con el constructor y
la interfaz (etapas 1 a 5) y un flujo guiado de tipo de distribución, escritorio,
software, hardware, identidad, resumen y construcción. Ver
[`MOTOR_DESKTOP_2.4.md`](MOTOR_DESKTOP_2.4.md).

## Requisitos y límites

- Fedora con `dnf` y repositorios configurados.
- La búsqueda consulta los repositorios habilitados en el host.
- Los paquetes elegidos se guardan en la configuración existente como paquetes
  adicionales y pasan por las validaciones de seguridad previas a compilar.
- No se instala ningún paquete en el host durante la búsqueda.
