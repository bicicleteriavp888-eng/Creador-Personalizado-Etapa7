# Selección de software — etapa 2 (2.4)

## Alcance

La etapa 2 incorpora la consulta y validación del software que el usuario
quiere agregar a un proyecto:

- listado de repositorios DNF habilitados;
- búsqueda de paquetes por nombre, resumen o descripción;
- listado y detalle de grupos comps;
- selección de paquetes y grupos desde la pantalla **Nuevo proyecto**;
- validación compartida de paquetes, grupos y textos de búsqueda.

La consulta es de **solo lectura**. No instala, elimina, habilita ni deshabilita
paquetes o repositorios. La resolución definitiva de dependencias sigue siendo
responsabilidad del constructor al compilar.

## Estructura

```
core/software/
├── __init__.py       API pública de la política compartida
└── policy.py         validación de paquetes, grupos y búsquedas

core/repositories/
├── dnf_query.py      adaptador de solo lectura para DNF
└── __init__.py       exporta DnfQuery y sus modelos

gui/custom_distro.py  consulta en segundo plano y selección de software
gui/tab_software.py   campo extra_groups del asistente
gui/validation.py     validación del paso 3
```

`core/desktops/packages.py` ahora reutiliza la política compartida, por lo que
la interfaz, el motor Desktop y los adaptadores DNF aplican las mismas reglas.

## Modelos de datos

`core.repositories.dnf_query` expone:

| Modelo | Contenido |
|---|---|
| `DnfRepository` | `id`, `name`, `enabled` |
| `DnfPackage` | `name`, `summary`, `repository`, `version` |
| `DnfGroup` | `id`, `name`, `installed` |
| `DnfGroupDetails` | campos del grupo y listas mandatory/default/optional/conditional |

`DnfQuery` ofrece:

- `available()`
- `list_enabled_repositories()`
- `search_packages(query="", limit=500)`
- `list_groups()`
- `group_info(group_id)`

## Compatibilidad con DNF5

Fedora 44 usa DNF5. Durante la implementación se comprobó que
`dnf repoquery` **ya no acepta `--search`**. La consulta anterior de la interfaz
habría fallado en Fedora 44. La etapa 2 usa:

- `dnf repolist --enabled --json` para repositorios, con respaldo de texto para
  versiones anteriores;
- `dnf search --all -- <términos>` para búsquedas por nombre o descripción;
- `dnf repoquery --available --latest-limit=1 --qf ...` para el catálogo
  completo, donde sí se obtienen repositorio y versión;
- `dnf group list --hidden` y `dnf group info <id>` para grupos comps.

La salida se fuerza a `LC_ALL=C.UTF-8` para que los encabezados y las columnas
sean estables independientemente del idioma del equipo. Los resúmenes de
paquetes pueden aparecer en inglés por esa misma razón.

## Controles de seguridad

- **Sin shell:** todos los comandos se ejecutan con una lista de argumentos y
  `shell=False`.
- **Separador de opciones:** la búsqueda del usuario se pasa después de `--`
  para que DNF no la interprete como una opción.
- **Validación previa:** se rechazan controles, saltos de línea, textos de más
  de 120 caracteres y términos que empiecen con `-`.
- **Paquetes:** patrón RPM estricto, máximo 128 caracteres, lista de bloqueados
  de `core.security.allowlist` y deduplicación.
- **Grupos:** política separada, prefijo `@` o `@^`, máximo 64 caracteres y
  validación del identificador antes de consultar DNF.
- **Límites:** 500 resultados por búsqueda (máximo configurable 2000), tiempo de
  espera de 180 segundos y mensajes de error saneados y truncados.
- **Entrada de DNF:** la salida se interpreta como datos; nunca se evalúa como
  shell.
- **Entradas inválidas:** se informan al usuario y no se descartan en silencio.

## Integración con la interfaz

La pantalla **Nuevo proyecto** incorpora:

1. selector de tipo de proyecto;
2. botón para consultar repositorios habilitados y resumen con sus IDs;
3. carga de grupos comps, selector y lista de grupos elegidos;
4. búsqueda de paquetes, catálogo completo y listas de disponibles/elegidos.

Las consultas se ejecutan en un `QThread` (`DnfWorker`) para no congelar la
interfaz. Si DNF no está instalado, los controles de consulta se deshabilitan y
se muestra un mensaje; la selección manual de paquetes sigue disponible.

Al usar la selección:

- los paquetes se copian a `extra_packages`;
- los grupos se copian a `extra_groups` como `@grupo`;
- ambos campos se guardan en `QSettings` y en los perfiles;
- el paso 3 valida paquetes inválidos, bloqueados y grupos inválidos.

Con el motor Desktop, `DesktopKickstartGenerator` consume `extra_groups` y los
instala en la ISO. Con el motor Kiosco, la interfaz informa explícitamente que
los grupos no se aplican. La elección del motor se resuelve desde el perfil del
proyecto y se integra en `BuilderWorker` desde la etapa 3.

## Pruebas

Pruebas nuevas:

- `tests/test_software_policy.py`: validación de paquetes, grupos, búsquedas,
  longitudes, bloqueos y deduplicación.
- `tests/test_dnf_query.py`: parseo de repositorios JSON y de texto, búsquedas,
  catálogo completo, grupos, detalle de grupos, límites, tiempos de espera,
  errores saneados y ausencia de DNF.
- `tests/test_gui_smoke.py`: selección de grupos, aplicación a `extra_groups`,
  rechazo de grupos inválidos, resumen de repositorios, `collect_config` y
  resolución del motor desde el perfil.
- `tests/test_gui_validation.py`: paquetes bloqueados, grupos inválidos y
  validación específica del motor Desktop en el paso 3.
- `tests/test_desktops.py`: los grupos seleccionados llegan al Kickstart
  Desktop.
- `tests/test_build_engines.py`: selección del constructor y generación del
  Kickstart Desktop sin componentes de kiosco.

En este host Fedora 44 se consultaron DNF real para verificar el parseo:
repositorios habilitados, búsquedas por nombre y descripción, catálogo completo
con límite, grupos comps y detalle de un grupo. No se compiló ninguna ISO.

## Límites explícitos

- **No se generó una ISO Kiosco ni Desktop** en esta etapa.
- **No se ejecutó QEMU ni una prueba BIOS/UEFI.**
- **No se probó hardware físico**, incluida la Dell Vostro 1510.
- La disponibilidad de paquetes y grupos depende de los repositorios del host;
  no se garantiza que una selección concreta resuelva en otra release o
  arquitectura.
- El catálogo completo se limita en memoria a 500 resultados por defecto; DNF
  igualmente genera la salida completa antes de que el adaptador la recorte.
- La elección guiada de escritorio y usuario desde el asistente es la etapa 4.
  En esta entrega, un proyecto Desktop usa GNOME y el usuario `fedora` por
  defecto.

## Próximos pasos

1. Etapa 4: flujo guiado con tipo de distribución, escritorio, software,
   hardware, identidad, resumen y construcción.
2. Etapa 5: compatibilidad de gráficos, Wi-Fi, touchpad y asistente Wi-Fi en
   Live.
3. Laboratorio: compilar una ISO Desktop y probar BIOS/UEFI en QEMU.
