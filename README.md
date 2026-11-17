# Creador-Personalizado Fedora Distribución

**Constructor de distribuciones Fedora de escritorio y sistemas Kiosco.**  
*Tu distribución, tus reglas.*

Creador-Personalizado es una aplicación de escritorio desarrollada en Python y PySide6 para diseñar proyectos de distribuciones basadas en Fedora, configurar sus componentes y generar imágenes ISO personalizadas.

El proyecto mantiene dos motores de construcción independientes:

- **Fedora Desktop:** distribuciones con GNOME, KDE Plasma o Xfce, sus gestores de sesión y configuración de usuario de escritorio.
- **Kiosco:** sistemas de propósito específico con Cage o Sway, inicio directo de la aplicación y configuración de acceso restringido.

La interfaz comparte las herramientas generales del proyecto, pero las opciones específicas de cada modalidad deben permanecer aisladas para evitar que una configuración de Kiosco afecte a una distribución Desktop, o viceversa.

## Estado del repositorio

- Rama principal: `main`.
- Versión que actualmente refleja el código publicado en esta rama: **3.0.0-alpha.4**.
- Versión de desarrollo posterior preparada fuera de este repositorio: **3.0.0-alpha.7**. Su publicación y sincronización con la rama principal todavía deben realizarse y validarse; por eso no se presenta aquí como código ya incorporado.
- Plataforma objetivo de las imágenes: Fedora 44.
- Licencia: GPL-3.0-or-later.

Las versiones alpha son de desarrollo. La generación de una ISO y su arranque en hardware real o máquina virtual deben verificarse por separado; las pruebas unitarias no equivalen a una certificación de imagen.

## Funcionalidades del proyecto

- Creación, apertura y guardado de proyectos independientes.
- Perfiles y plantillas para iniciar configuraciones.
- Selección de paquetes, grupos y repositorios Fedora mediante DNF.
- Resolución de dependencias durante la preparación de la imagen.
- Escritorios GNOME, KDE Plasma y Xfce para Fedora Desktop.
- Composición Kiosco con Cage o Sway y aplicación de inicio.
- Personalización de identidad, recursos gráficos y bienvenida del instalador.
- Validación de configuración antes de construir.
- Registro de compilaciones, logs e integridad SHA-256.
- Herramientas para validar imágenes ISO y probar arranque con QEMU.
- Escritura de imágenes a USB con confirmación y verificación.

La disponibilidad concreta de cada función depende de la versión y del motor seleccionado. Consultá el código y la documentación de la versión antes de asumir que una función está integrada en la rama publicada.

## Arquitectura

```text
main.py
gui/                  Interfaz gráfica y asistente de configuración
core/
  builders/           Resolución de motores de construcción
  desktops/           Motor Fedora Desktop
  repositories/       Consultas de repositorios y DNF
  software/            Políticas y selección de software
  projects/            Gestión de proyectos
  builder.py           Motor de construcción Kiosco
profiles/              Perfiles y plantillas
packaging/             Integración e instalación en Fedora
scripts/               Herramientas de validación y mantenimiento
tests/                 Pruebas automatizadas
documentation/         Diseño, auditorías y seguimiento técnico
```

## Requisitos

El entorno de desarrollo y construcción está orientado a Fedora. Entre las dependencias principales se encuentran:

- Python 3.
- PySide6.
- DNF5 y herramientas de repositorios Fedora.
- Herramientas de creación de imágenes Live/ISO utilizadas por el motor.
- Pytest para ejecutar las pruebas.

Las dependencias exactas deben comprobarse en los archivos de configuración y scripts de instalación de la versión que se esté utilizando.

## Ejecutar la aplicación

Desde la carpeta del proyecto:

```bash
python3 main.py
```

## Ejecutar las pruebas

```bash
python3 -m compileall -q .
python3 -m pytest -q
```

Para una validación integral también se necesita un entorno Fedora preparado, acceso a los repositorios, espacio de almacenamiento suficiente y pruebas de arranque BIOS/UEFI de la ISO resultante.

## Principios de desarrollo

1. Mantener los motores Fedora Desktop y Kiosco independientes.
2. No declarar una función como implementada sin verificarla en el código.
3. No marcar una etapa como validada sin pruebas y evidencia.
4. Mantener la resolución automática de dependencias de paquetes y grupos.
5. Aislar la configuración y los recursos de cada proyecto.
6. Documentar los límites conocidos y distinguir pruebas unitarias de pruebas de ISO real.

## Documentación

La carpeta `documentation/` contiene auditorías, decisiones de arquitectura y seguimiento de las etapas. Los archivos `CHANGELOG` describen los cambios de cada versión cuando están presentes.

---

**Creador-Personalizado Fedora Distribución**  
Proyecto de software libre bajo licencia GPL-3.0-or-later.
