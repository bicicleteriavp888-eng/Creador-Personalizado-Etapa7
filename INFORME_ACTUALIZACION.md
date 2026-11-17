# Informe de actualización y endurecimiento — Creador-kiosk

**Fecha:** 12 de noviembre de 2026  
**Base revisada:** código fuente entregado en `Creador-kiosk.zip`  
**Plataforma objetivo:** Fedora 44 / Python 3 / PySide6

## 1. Resumen ejecutivo

Se realizó una primera actualización enfocada en mejorar la presentación de
la aplicación, reducir riesgos de seguridad en las imágenes generadas,
proteger la operación destructiva de escritura USB y actualizar la
información de uso. Se conservó Python/PySide6, la organización funcional
existente, el backend de Kickstart y el flujo de compilación.

La interfaz ahora tiene una estética clara inspirada en el instalador de
Windows 11: encabezado de producto, fondo gris azulado, paneles blancos,
acentos azules, controles uniformes y pestañas presentadas como etapas.
No se incorporaron dependencias visuales externas.

## 2. Cambios implementados

### 2.1 Interfaz

- Ventana principal ampliada y con tamaño mínimo razonable.
- Encabezado con nombre del producto, descripción y edición Fedora 44.
- Navegación por etapas con pestañas estilizadas.
- Campos, botones, grupos, barras de progreso y tooltips unificados.
- Acción principal de compilación diferenciada visualmente.
- Acción destructiva de escritura USB identificada con color de advertencia.
- Consolas de registro con contraste y tipografía monoespaciada.
- El tema visual se separó en `gui/theme.py` para mantener `main.py` más limpio.
- Previsualizaciones con fondos claros y bordes coherentes con el tema.
- Nombres de pestañas y acciones principales normalizados en español.

### 2.2 Seguridad del sistema generado

- Kickstart cambia de `selinux --disabled` a `selinux --enforcing`.
- SSH queda deshabilitado por defecto.
- Los paquetes OpenSSH y el servicio `sshd` solo se incluyen cuando el usuario
  activa expresamente la administración remota.
- La autenticación SSH por contraseña queda desactivada por defecto.
- La regla de firewall para SSH solo se agrega cuando SSH fue habilitado.
- Se mantiene `root` bloqueado y `sudo` con contraseña por defecto.
- Se mantienen el sandbox de Chromium y el firewall como opciones seguras.
- Se restauran contextos SELinux de rutas personalizadas cuando `restorecon`
  está disponible.

### 2.3 Validación de entradas y branding

- La interfaz valida nombre de ISO, versión, creador y nombre de producto.
- El nombre de ISO y la versión tienen formatos y longitudes acotados.
- La contraseña requiere al menos 12 caracteres y no admite caracteres de
  control. El backend vuelve a comprobar esta regla antes de generar el hash.
- Los valores de branding se codifican en Base64 antes de incorporarse a los
  scripts generados, evitando interpolar directamente texto del usuario en
  comandos shell.
- El nombre de producto rechaza comillas, barras invertidas, `$` y caracteres
  de control para preservar el formato de `/etc/os-release`.
- El nombre del creador se normaliza para impedir que inserte nuevas líneas
  en comentarios del Kickstart.
- La compilación se detiene si hay menos de 12 GiB libres o si el directorio
  de trabajo está en `tmpfs`; antes solo se emitía una advertencia.
- Se eliminó una ruta absoluta a un RPM particular de `/home/sergio`; la
  selección de aplicaciones locales vuelve a ser configurable.

### 2.4 Escritura USB

- `lsblk` solicita también el identificador `MAJ:MIN`.
- La selección conserva una instantánea de identidad del dispositivo.
- Antes de escribir se vuelve a enumerar el dispositivo y se comparan
  `MAJ:MIN`, capacidad, modelo y número de serie cuando están disponibles.
- Se comprueba el identificador de bloque real mediante `stat`.
- Dentro del proceso privilegiado se vuelve a verificar `MAJ:MIN`, capacidad
  y número de serie antes de ejecutar `dd`.
- Después de `dd` y `sync`, `cmp -n` compara el contenido escrito con la ISO.
- Los nombres de ISO existentes no se reemplazan: se genera un sufijo único.
- La interfaz exige confirmación y obliga a confirmar nuevamente al cambiar
  el dispositivo seleccionado.

### 2.5 Documentación

- README reescrito con requisitos, inicio, seguridad y pruebas.
- Se agregó este informe con cambios y limitaciones.
- El informe original `INFORME.txt` se conserva como documentación de la
  versión previa; algunas descripciones de seguridad allí pueden no reflejar
  los valores predeterminados nuevos.

## 3. Pruebas realizadas

| Comprobación | Resultado |
|---|---|
| `python -m compileall -q .` | Correcto |
| Suite pytest | 53 pruebas aprobadas con shim temporal de QtCore |
| Sintaxis shell de `_post_base()` + branding (SSH desactivado y activado) | `sh -n` correcto |
| Compilación real de ISO Fedora 44 | No ejecutada en este entorno |
| Arranque BIOS y UEFI | Pendiente de prueba en host/hardware |
| Interfaz gráfica PySide6 real | No ejecutada en este entorno |

**Nota de entorno de pruebas:** el entorno usado para esta revisión no tiene
PySide6 instalado. Para ejecutar la lógica unitaria se utilizó un shim
transitorio de `PySide6.QtCore` fuera del proyecto. No se incluyó ese shim en
el ZIP. Por lo tanto, el resultado de pytest valida lógica de backend y
funciones aisladas, pero no sustituye la ejecución con PySide6 real en Fedora.

## 4. Pendientes recomendados antes de distribuir ISOs

1. Instalar dependencias en Fedora 44 y abrir la GUI para validar tamaños,
   fuentes, scroll, diálogos y señales de PySide6.
2. Construir una ISO de prueba completa con los repositorios reales de Fedora.
3. Verificar Kickstart y scripts `%post` en el entorno de instalación.
4. Arrancar la ISO en UEFI y BIOS (si se seleccionó modo dual).
5. Probar Anaconda, Cage, Sway, LightDM, red y aplicaciones locales.
6. Probar escritura USB con un pendrive descartable y confirmar la comparación
   byte a byte posterior a `dd`.
7. Evaluar compatibilidad real de `livecd-creator` con Fedora 44; esta revisión
   no demuestra por sí sola que esa herramienta genere una ISO válida en el
   host final.
8. Considerar dividir `core/builder.py` en módulos después de estabilizar la
   funcionalidad. Una refactorización amplia ahora elevaría el riesgo sin ser
   necesaria para los cambios de seguridad y presentación de esta entrega.

## 5. Riesgos y alcance

- La escritura USB destruye el contenido del dispositivo elegido. La nueva
  validación reduce el riesgo de selección equivocada, pero el usuario debe
  revisar cuidadosamente destino y capacidad antes de confirmar.
- El chequeo `cmp` puede tardar varios minutos en pendrives lentos; esto es
  deliberado para no informar éxito sin verificar los datos.
- SELinux `enforcing` es la opción correcta como valor seguro, pero debe
  validarse con los servicios personalizados y las aplicaciones elegidas.
- SSH permanece opcional; cuando se habilita, el operador debe preparar claves
  públicas si mantiene desactivada la autenticación por contraseña.
- No se ejecutó una compilación ISO completa ni se probó arranque real.

## 6. Resultado

La entrega queda preparada como una actualización de código fuente con
mejoras de interfaz, defaults de seguridad más conservadores, validación de
entradas, controles reforzados de escritura USB, pruebas ampliadas y
 documentación revisada. Se recomienda completar las pruebas de Fedora 44
indicadas en la sección 4 antes de considerar la ISO apta para producción.

## 7. Actualización 2.0 — ETAPA 3 (2026-11-13)

La interfaz descripta en la sección 2.1 fue reemplazada por la interfaz 2.0:

- Panel principal con estado real del entorno, última ISO, SHA-256 en segundo
  plano, espacio, dependencias, servicios, configuración activa, tareas
  pendientes y últimos errores.
- Navegación lateral y asistente de seis pasos con validación por etapa,
  guardado, retroceso y ayuda contextual.
- Modos Simple y Avanzado, con confirmación y restablecimiento de opciones
  avanzadas al pasar a Simple.
- Temas claro y oscuro persistentes.
- Nuevos módulos `gui/components.py`, `gui/status.py`, `gui/validation.py` y
  `gui/tab_security.py`.

Validaciones ejecutadas: `compileall` sin errores, **84 pruebas en verde** y
recorrido de la GUI con Qt `offscreen` a 1320×900 y 1080×720 sin scroll
horizontal. No se ejecutó una compilación real de ISO ni un arranque BIOS/UEFI;
esas pruebas siguen pendientes y no se declaran como aprobadas.

El detalle técnico completo está en
[`documentation/AUDITORIA_2.0.md`](documentation/AUDITORIA_2.0.md), Anexo B.
