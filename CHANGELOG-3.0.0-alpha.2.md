# Creador Personalizado 3.0.0-alpha.2

## Gestor de software: rediseño y corrección

- Reemplaza las dos listas básicas por un catálogo tabular y una cesta de cambios pendientes.
- Agrega filtros locales por repositorio y tipo de paquete, búsqueda por nombre/descripción y detalle del paquete seleccionado.
- Carga automáticamente el catálogo al abrir el gestor cuando DNF5 está disponible.
- Permite marcar y desmarcar paquetes y grupos Comps antes de aplicar la selección al proyecto.
- Agrega el control de contenido de grupos Comps que faltaba en la interfaz.
- Corrige el error que impedía iniciar las consultas: `btn_group_info` era referenciado por el control de estado DNF sin haber sido creado.
- Detecta tanto `dnf5` como `dnf` en el PATH.
- Conserva la simulación `--assumeno`: DNF5 resuelve dependencias y conflictos sin modificar el sistema anfitrión.

## Límites de esta alpha

- La carga inicial consulta hasta 500 paquetes; la búsqueda remota permite acotar resultados. No hay todavía paginación real.
- Los filtros de tipo son heurísticos y sirven para organizar visualmente, no representan metadatos oficiales de Fedora.
- La tabla muestra paquetes disponibles; la selección final de dependencias se calcula en la simulación DNF5 y se vuelve a validar en la construcción de la imagen.
- No se pudo ejecutar la prueba gráfica ni una consulta DNF real en el entorno de desarrollo porque no dispone de PySide6 ni de repositorios Fedora configurados.
