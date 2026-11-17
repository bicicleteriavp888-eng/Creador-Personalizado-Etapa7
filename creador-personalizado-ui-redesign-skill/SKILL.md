---
name: creador-personalizado-ui-redesign
description: Guía para renovar la interfaz de Creador Personalizado con PySide6, preservando los motores y la lógica funcional existente.
---

# Skill: Renovación integral de la interfaz de Creador Personalizado

## 1. Misión

Guiar a otra IA en la renovación visual y estructural de la aplicación **Creador Personalizado**, convirtiéndola en una aplicación de escritorio integrada, profesional, adaptable y fácil de usar, sin romper las funciones existentes.

La renovación debe mejorar tanto la presentación como la organización de la experiencia. No consiste en cambiar colores superficialmente ni en reescribir toda la aplicación.

## 2. Identidad del producto

- Nombre: **Creador Personalizado**.
- Subtítulo: **Constructor de distribuciones Fedora**.
- Lema: **Tu distribución, tus reglas.**
- Tecnología existente: Python + PySide6.
- Plataforma objetivo declarada por el proyecto: Fedora 44.
- Modalidades: Fedora Desktop y Kiosco.
- Motores Desktop y Kiosco deben seguir siendo independientes.

## 3. Fuente de verdad y estado inicial

La base de trabajo entregada es `Creador-Personalizado-3.0.0-alpha2-gestor-software.zip` (directorio interno `Creador-Personalizado-3.0.0-alpha.2/`). Antes de editar:

1. Inspeccionar el ZIP y confirmar su estructura y versión.
2. Leer `main.py`, `gui/layouts.py`, `gui/theme.py`, `gui/components.py` y todas las páginas de `gui/`.
3. Seguir las señales, slots, modelos, servicios y llamadas que conectan cada pantalla con la lógica real.
4. Ejecutar y registrar las pruebas disponibles antes de modificar.
5. No asumir que una función existe porque aparezca en un botón, etiqueta, informe o conversación anterior.

### Hallazgos verificados en la base adjunta

- `main.py` establece un tamaño mínimo de ventana de `1080 x 720`.
- `main.py` fija la barra lateral en `270` píxeles.
- `gui/layouts.py` define `add_page(..., content_width=1180)` y utiliza `QScrollArea`.
- `gui/theme.py` centraliza parte de los estilos Qt mediante hojas de estilo.
- Existen páginas separadas en `gui/`, entre ellas `custom_distro.py`, `tab_software.py`, `tab_aesthetic.py`, `tab_installer.py`, `tab_security.py`, `tab_build.py` y `tab_usb.py`.

Estos puntos son observaciones de la base inspeccionada, no una autorización para eliminar o cambiar esos componentes sin rastrear primero sus dependencias.

## 4. Objetivo de experiencia

La aplicación debe dejar de sentirse como una secuencia rígida de formularios y pasar a ser una suite de escritorio coherente, con:

- Navegación predecible y jerarquía visual clara.
- Paneles que aprovechen el espacio disponible.
- Páginas adaptables al tamaño de ventana y al escalado de pantalla.
- Tablas legibles, con selección y estados visibles.
- Formularios agrupados por propósito.
- Mensajes de estado, progreso, errores y advertencias consistentes.
- Tema claro y oscuro con contraste suficiente.
- Diálogos y controles visualmente homogéneos.
- Sin desplazamiento horizontal accidental ni controles cortados.

## 5. Dirección visual propuesta

Estética profesional, moderna, sobria y minimalista. Mantener la identidad de Creador Personalizado:

- Azul petróleo / azul profundo como color estructural.
- Blanco y grises suaves para superficies en tema claro.
- Superficies oscuras diferenciadas en tema oscuro.
- Azul de acento para acciones primarias y selección.
- Tipografía legible y jerarquía consistente.
- Bordes discretos, radios moderados y espaciado uniforme.
- Evitar saturación de colores, sombras excesivas, adornos y tarjetas innecesarias.

No fijar colores arbitrarios en cada widget. Definir tokens/variables de tema centralizados y reutilizables.

## 6. Arquitectura de navegación sugerida

### A. Panel principal

Una portada con proyectos recientes, estado del entorno, accesos directos, últimas compilaciones y avisos relevantes. No inventar métricas: mostrar solo información disponible y comprobada.

### B. Espacio de trabajo del proyecto

Mantener las secciones de configuración existentes, pero organizarlas por dominio y contexto. La modalidad del proyecto (Fedora Desktop o Kiosco) debe ser explícita. No seleccionar Kiosco por defecto si el proyecto no lo define.

### C. Gestor de software

Debe funcionar como herramienta especializada, con:

- Búsqueda y filtros.
- Catálogo con nombre, resumen, versión, arquitectura, repositorio y tipo cuando los datos estén disponibles.
- Panel de detalles del elemento seleccionado.
- Selección de paquetes individuales.
- Grupos Comps y metapaquetes diferenciados claramente.
- Lista de cambios pendientes: instalar, quitar, actualizar o mantener.
- Simulación de transacción, dependencias, conflictos y resumen de cambios.
- Estados legibles y consistentes; no usar filas con texto oscuro sobre fondo oscuro.
- Diseño que no recorte la tabla ni los botones al cambiar el tamaño de ventana.

No confundir grupos Comps con metapaquetes RPM. La resolución debe utilizar el backend real disponible en el proyecto (DNF5/libdnf5 si está implementado y verificado). La selección y simulación no deben instalar paquetes en el sistema anfitrión.

### D. Compilación y validación

Un espacio unificado para progreso, etapa actual, registros, errores, advertencias y resultados. No bloquear el hilo principal de la interfaz con operaciones largas; usar el mecanismo de tareas/hilos adecuado al diseño existente.

### E. Herramientas

Mantener accesos a funciones auxiliares como creación de unidad USB, respetando sus servicios y permisos actuales.

## 7. Reglas de adaptación y layout

- La ventana debe poder redimensionarse.
- Revisar si el mínimo actual de `1080 x 720` puede reducirse sin degradar la experiencia; no cambiarlo sin probar.
- Evitar `setFixedWidth` en paneles principales salvo que exista una razón funcional clara.
- Preferir layouts Qt (`QHBoxLayout`, `QVBoxLayout`, `QGridLayout`, `QSplitter`, `QSizePolicy`) frente a geometrías absolutas.
- Usar `QSplitter` cuando el usuario deba ajustar paneles laterales y centrales.
- Las tablas deben tener políticas de tamaño y modos de redimensionado de columnas razonables.
- Los botones importantes deben permanecer accesibles; permitir salto de línea o reorganización cuando el ancho sea reducido.
- Evitar que una página imponga un ancho fijo de contenido que provoque scroll horizontal.
- El scroll vertical es válido para contenido largo; el horizontal solo cuando sea realmente necesario.
- Probar ventanas pequeñas, medianas y grandes, además de escalado HiDPI.

## 8. Principios de ingeniería: preservar lo que funciona

1. Separar cambios visuales de cambios de lógica.
2. No reescribir motores de construcción durante la renovación de UI.
3. No mezclar responsabilidades de Fedora Desktop y Kiosco.
4. Mantener contratos públicos, señales, slots y modelos salvo migración documentada.
5. No reemplazar servicios reales por datos simulados para que una pantalla parezca completa.
6. No ejecutar operaciones privilegiadas desde la UI sin el mecanismo de autorización ya previsto.
7. No bloquear la interfaz durante consultas de repositorios, resolución de dependencias o compilaciones.
8. Mantener compatibilidad con proyectos existentes y sus archivos de configuración.
9. No borrar pantallas ni controles hasta demostrar que son redundantes y que sus funciones tienen destino.
10. Ante incertidumbre, inspeccionar y probar; no adivinar.

## 9. Plan de trabajo por etapas

### Etapa 0 — Auditoría y línea base

- Inventario de pantallas, widgets, servicios y rutas de navegación.
- Diagrama de dependencias UI → servicios → motores.
- Pruebas iniciales y registro de fallas preexistentes.
- Capturas de referencia en tamaños de ventana conocidos.
- Lista de funcionalidades que no deben cambiar.

### Etapa 1 — Sistema visual

- Definir paleta, tipografía, espaciado, bordes y estados.
- Unificar `gui/theme.py` y componentes comunes.
- Revisar botones, entradas, tablas, pestañas, diálogos y notificaciones.
- Comprobar contraste en ambos temas.

### Etapa 2 — Estructura principal

- Rediseñar navegación lateral/superior y encabezado de página.
- Crear portada del panel principal.
- Adaptar la estructura central al ancho disponible.
- Preservar las rutas y acciones existentes.

### Etapa 3 — Componentes adaptables

- Tablas y listas.
- Formularios y grupos de configuración.
- Paneles divididos y áreas de detalle.
- Estados vacíos, carga, error y éxito.
- Diálogos consistentes.

### Etapa 4 — Gestor de software

- Integrar el catálogo y el backend existente sin sustituirlos por mocks.
- Corregir contraste, columnas, selección y panel de detalles.
- Adaptar el panel de cambios pendientes y simulación.
- Validar paquetes, grupos y metapaquetes con datos reales.

### Etapa 5 — Resto de módulos

- Identidad, apariencia, instalador, seguridad/servicios, compilación/validación y USB.
- Adaptar cada página a los componentes comunes.
- Mantener las diferencias funcionales entre Desktop y Kiosco.

### Etapa 6 — Pruebas y entrega

- Pruebas unitarias y de integración.
- Pruebas de GUI con PySide6 real cuando esté disponible.
- Pruebas de redimensionado y HiDPI.
- Verificación manual de flujos principales.
- Comparación de capturas antes/después.
- ZIP limpio, changelog, instrucciones y SHA-256.

## 10. Criterios de aceptación

La renovación no se considera terminada hasta que:

- No haya controles cortados en las resoluciones probadas.
- No aparezca scroll horizontal accidental en páginas comunes.
- Las tablas mantengan contraste y legibilidad en tema claro y oscuro.
- Los paneles se adapten al ancho disponible.
- La navegación lleve a las mismas funciones verificadas de antes.
- Las operaciones largas no congelen la interfaz.
- El gestor muestre datos reales y estados coherentes, no mensajes de éxito ficticios.
- Los proyectos existentes sigan abriendo y conservando su modalidad.
- Los motores Desktop y Kiosco sigan separados.
- Las pruebas ejecutadas y las limitaciones se documenten con honestidad.

## 11. Protocolo de cada entrega

Para cada etapa:

1. Enumerar archivos modificados y motivo.
2. Explicar cambios funcionales y visuales por separado.
3. Ejecutar pruebas relevantes y reportar resultados reales.
4. No afirmar que se probó una GUI real si solo se usó un mock o shim.
5. No afirmar que se generó/probó una ISO si no ocurrió.
6. Excluir `__pycache__`, `.pytest_cache`, `build/`, `dist/` y `*.egg-info` salvo que sean necesarios para la entrega.
7. Entregar ZIP completo con versión clara, changelog e instrucciones.
8. Calcular SHA-256 del ZIP final.

## 12. Primer encargo para la IA que use este Skill

Retomar la base `Creador-Personalizado-3.0.0-alpha2-gestor-software.zip` y preparar la **Etapa 0: auditoría de interfaz y línea base**. No rediseñar todavía ni modificar código. Entregar:

- Mapa de navegación actual.
- Inventario de pantallas y componentes compartidos.
- Dependencias entre interfaz, servicios y motores.
- Problemas de adaptación detectados con archivo y línea.
- Estado de las pruebas y dependencias disponibles.
- Propuesta concreta de migración incremental, indicando qué se puede renovar sin tocar lógica.

Esperar aprobación antes de iniciar la Etapa 1.
