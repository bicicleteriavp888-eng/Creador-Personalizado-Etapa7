# Creador Personalizado 3.0 — Arquitectura objetivo y plan de migración

## 1. Identidad del producto

- **Nombre:** Creador Personalizado.
- **Descripción:** Constructor de distribuciones Fedora.
- **Lema:** Tu distribución, tus reglas.
- **Público:** usuarios que necesitan crear una Fedora Desktop, un sistema Kiosco o una distribución personalizada.
- **Interfaz:** PySide6; estilo profesional, sobrio, accesible y consistente.

La versión 3.0.0-alpha.1 es una transición de identidad sobre la base funcional 2.5.5. No se afirma que toda la arquitectura objetivo esté implementada.

## 2. Principios no negociables

1. Los motores Desktop y Kiosco tienen configuraciones, recetas Kickstart, validaciones y ciclos de compilación independientes.
2. Los servicios comunes se comparten mediante contratos explícitos; no se importa lógica específica de un motor desde el otro.
3. Toda selección de paquetes se valida y se resuelve con DNF5/libdnf5 en el entorno destino. La simulación no instala paquetes en el anfitrión.
4. Un proyecto nuevo declara explícitamente su motor (`desktop` o `kiosk`). La compatibilidad con proyectos antiguos se resuelve mediante migración identificable, nunca por una elección silenciosa que pueda producir una ISO equivocada.
5. Ninguna compilación se considera validada o probada solo porque se haya generado el archivo ISO.
6. Cada migración preserva proyectos, perfiles, historial y datos del usuario; las rutas antiguas se mantienen hasta disponer de una migración verificada.

## 3. Arquitectura objetivo

```text
Creador Personalizado (PySide6)
  ├── Presentación: panel, asistente, modo Simple/Avanzado, ayuda
  ├── Aplicación: casos de uso y coordinación de proyectos
  ├── Dominio: proyecto, selección de software, transacción, validación
  ├── Servicios compartidos
  │    ├── repositorios y consultas DNF5
  │    ├── resolución/simulación de paquetes
  │    ├── perfiles y plantillas
  │    ├── procesos, privilegios y seguridad
  │    ├── historial, diagnósticos e inspección ISO
  │    └── importación/exportación y migración
  └── Adaptadores de construcción
       ├── Fedora Desktop: Kickstart, validación y builder propios
       └── Kiosco: Kickstart, validación y builder propios
```

### Estado comprobado en la base 2.5.5

- La selección de motor existe en `core/builders/registry.py`.
- `DesktopISOBuilder` está en `core/builders/desktop.py` y genera una receta Desktop propia.
- El constructor Kiosco reside en `core/builder.py`.
- Desktop reutiliza actualmente el ciclo de construcción heredando de `KioskISOBuilder`. Es una dependencia técnica conocida que debe eliminarse en una etapa específica; no se oculta ni se declara ya resuelta.
- Existen servicios separados para repositorios, perfiles, historial, validación, procesos, seguridad y software.
- La interfaz principal y varios mixins siguen concentrados en `main.py` y `gui/`; su modularización será incremental.

## 4. Modelo de proyecto

Todo proyecto nuevo deberá guardar como mínimo:

- `schema_version`: versión del esquema de configuración.
- `product_name`, `product_version`, `release` y `architecture`.
- `engine`: `desktop` o `kiosk`, obligatorio en proyectos nuevos.
- `desktop_environment` cuando `engine=desktop`.
- perfil, paquetes, grupos, repositorios y operaciones de software.
- apariencia, instalador, seguridad, servicios y opciones de hardware.

La migración de configuraciones antiguas debe generar un informe con el motor inferido, el motivo de inferencia y cualquier dato que requiera confirmación. No sobrescribir el archivo original.

## 5. Organización de la experiencia

1. Inicio y proyectos recientes.
2. Tipo de distribución y datos del proyecto.
3. Sistema base y entorno.
4. Software: paquetes, grupos Comps, metapaquetes y simulación de transacciones.
5. Identidad visual y arranque.
6. Hardware, instalador, seguridad y servicios.
7. Resumen, validación y construcción.

Modo Simple presenta perfiles y decisiones esenciales. Modo Avanzado expone repositorios, paquetes individuales, opciones técnicas y políticas. La ayuda debe explicar consecuencias y no solo describir controles.

## 6. Etapas de implementación

| Etapa | Resultado exigible |
|---|---|
| 0 | Identidad 3.0, comandos nuevos, compatibilidad de rutas y documentación |
| 1 | Modelo de proyecto versionado y migrador 2.x → 3.x con pruebas |
| 2 | Shell visual renovado, navegación y accesibilidad |
| 3 | Gestor Synaptic completo conectado a DNF5 |
| 4 | Contrato común de builder y ciclo de construcción independiente |
| 5 | Validación, diagnóstico, recuperación y laboratorio ISO |
| 6 | RPM, actualización, desinstalación y documentación de usuario |

## 7. Criterios de aceptación globales

- Los proyectos 2.x se pueden abrir o migrar sin pérdida silenciosa de configuración.
- Los proyectos nuevos no pueden iniciar compilación sin un motor explícito.
- Una selección de paquetes muestra dependencias, conflictos, sustituciones y eliminaciones antes de confirmar.
- Desktop no instala componentes exclusivos de Kiosco y Kiosco no instala entornos Desktop salvo selección explícita válida.
- Las pruebas unitarias, GUI, empaquetado y validación de ISO se reportan por separado.
- Una ISO solo se marca como generada, validada o probada según la evidencia real disponible.

## 8. Alcance de esta entrega alpha.1

Implementado: identidad visual textual principal, nombre de paquete Python, nuevos comandos de ejecución y validación, lanzador y archivo de escritorio, icono SVG, instalador actualizado y esta especificación de arquitectura.

Compatibilidad temporal: se mantienen el identificador QSettings, rutas internas `creador-kiosk`, nombres de clases y APIs históricas. Los alias de comandos antiguos se conservan para evitar romper automatizaciones.

Pendiente: migración de proyectos, eliminación de la herencia Desktop→Kiosco, rediseño completo de pantallas, pruebas GUI en Fedora 44 y generación/arranque de ISO.
