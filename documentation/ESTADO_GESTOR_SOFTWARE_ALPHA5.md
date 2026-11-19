# Estado de unificación del gestor de software — alpha.5

Fecha: 2026-11-17  
Base: `Creador-Personalizado-3.0.0-alpha.4-Full-GPLv3.zip`

## Objetivo

Eliminar la duplicación funcional entre el paso 3 del asistente y la herramienta
«Gestor de software», usando el gestor Fedora existente como interfaz única de
consulta y selección. La selección debe alimentar el proyecto, no instalar RPM
en el sistema anfitrión.

## Cambios realizados en esta entrega

- El paso 3 incorpora el botón **Abrir gestor de software Fedora**.
- Los campos de paquetes y grupos del paso 3 pasan a ser resúmenes de solo
  lectura; dejan de presentarse como un segundo selector manual.
- El gestor conserva la responsabilidad de consultar DNF, mostrar repositorios,
  buscar paquetes, listar grupos Comps y mantener los cambios pendientes.
- «Aplicar selección al proyecto» devuelve al usuario al paso 3, no al paso 1.
- Se mantiene la distinción entre paquetes RPM, grupos Comps y perfiles de
  proyecto. Los perfiles siguen definiendo el motor de destino.

## Estado de los seis pasos acordados

| Paso | Estado | Evidencia / alcance |
|---|---|---|
| 1. Unificar el modelo de selección | Parcial | El gestor mantiene una única cesta (`_custom_pkg_names`, `_custom_groups`) y los campos del asistente reciben su resumen. Falta extraer la cesta a un servicio de dominio independiente y persistirla como objeto de proyecto. |
| 2. Integrar el paso 3 | Parcial implementado | El paso 3 abre el gestor único y ya no permite editar paquetes/grupos manualmente. Falta integrar el catálogo dentro de la propia página del paso 3; actualmente se abre como página de gestor. |
| 3. Reorganizar Herramientas | Parcial | Se conserva la página de gestor existente como destino único. No se duplicó el catálogo. Falta revisar y probar todos los puntos de entrada de menú y navegación en ejecución gráfica. |
| 4. Resolver dependencias | Existente, no instalación | `DnfQuery.preview_installation()` usa `--assumeno`; permite al solver calcular la transacción sin modificar el anfitrión. No se habilita instalación directa desde el gestor. |
| 5. Integrar con constructores | Parcial / requiere verificación | El proyecto transfiere paquetes y grupos a los campos de configuración; el motor Desktop contempla `extra_packages` y `extra_groups`. El motor Kiosco no aplica grupos Comps. Falta una prueba de extremo a extremo para ambos motores con una selección creada desde la GUI. |
| 6. Pruebas y aceptación | Pendiente de entorno | La ejecución completa de pytest no pudo recolectarse en este entorno porque falta PySide6 y la importación de paquetes requiere configurar el entorno del proyecto. No se declara aceptación funcional. |

## Comportamiento y límites importantes

- El gestor **no instala software en el Fedora anfitrión**.
- La simulación DNF usa el estado y los repositorios del anfitrión como orientación;
  la construcción debe volver a resolver dependencias dentro del entorno destino.
- Los metapaquetes RPM se seleccionan como paquetes ordinarios; DNF resuelve sus
  dependencias declaradas.
- Los grupos Comps no son metapaquetes RPM. Su aplicación está contemplada para
  Fedora Desktop; el motor Kiosco no los instala.
- No se usa `--skip-broken` ni `--allowerasing` en la simulación, para no ocultar
  conflictos ni permitir eliminaciones automáticas.

## Validaciones realizadas

- Inspección del código fuente de `gui/tab_software.py`, `gui/custom_distro.py`,
  `core/repositories/dnf_query.py`, `core/software/policy.py`,
  `core/projects/catalog.py` y los resolutores de paquetes Desktop.
- Se comprobó que `preview_installation()` invoca DNF con `--assumeno install`.
- Se comprobó que el paso 3 está registrado con la clave `step3`.
- La suite completa no pudo ejecutarse: el entorno no dispone de PySide6 y la
  invocación inicial tampoco tenía la raíz del proyecto en `PYTHONPATH`.

## Pendientes antes de declarar terminado

1. Extraer un `SoftwareSelection`/`SoftwareSelectionService` compartido y
   persistible, con operaciones instalar/quitar paquete y agregar/quitar grupo.
2. Montar el mismo componente visual del catálogo dentro del paso 3 y reutilizarlo
   desde Herramientas, en lugar de navegar a una página separada.
3. Sincronizar perfiles sugeridos, cambios manuales y proyecto sin sobrescrituras
   silenciosas.
4. Añadir pruebas unitarias del servicio y pruebas GUI de ida y vuelta.
5. Ejecutar pruebas en Fedora con PySide6 y DNF5 disponibles.
6. Construir una ISO Desktop y una ISO Kiosco de prueba, verificando que cada
   motor recibe solo las selecciones que soporta.

## Veredicto

Esta entrega corrige la duplicidad de edición manual en el paso 3 y establece una
ruta clara hacia el gestor único. **No representa todavía la finalización de los
seis pasos**: quedan pendientes la extracción del modelo de dominio, el montaje
embebido del componente, persistencia y pruebas de extremo a extremo.
