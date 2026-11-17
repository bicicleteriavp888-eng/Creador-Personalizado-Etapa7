# Creador Personalizado — Etapa 7

<sub>Versión: **3.0.0-alpha.4** · Licencia: **GNU GPL versión 3 o posterior**</sub>

Creador Personalizado permite preparar distribuciones Fedora personalizadas en modalidades Desktop y Kiosco.

## Licencia

El código del proyecto incluido en esta entrega se distribuye bajo **GNU General Public License v3.0 or later (GPL-3.0-or-later)**. Consultá el archivo [LICENSE](LICENSE) para leer el texto íntegro.

La licencia del proyecto no reemplaza ni modifica las licencias de PySide6/Qt ni de otras dependencias o componentes de terceros. Cada componente conserva sus propios términos.

## Alcance de esta publicación

Este repositorio publica el **parche de código de Etapa 7** y su documentación. No contiene una copia autónoma completa de la aplicación base. El parche se aplica sobre el árbol fuente de la versión anterior de Creador Personalizado (Etapa 6 / base alpha.3).

## Descargar desde GitHub

El archivo recomendado está en la raíz del repositorio:

- [`Etapa7-overlay-GPLv3.tar.gz`](Etapa7-overlay-GPLv3.tar.gz) — cambios de código de Etapa 7, documentación y licencia GPL.
- [`LICENSE`](LICENSE) — texto íntegro de GPL-3.0-or-later.
- [`INFORME_ETAPA7.md`](INFORME_ETAPA7.md) — informe técnico y validaciones.
- [`CHANGELOG-ETAPA7.md`](CHANGELOG-ETAPA7.md) — resumen de cambios.
- [`documentation/ETAPA7_GESTION_PROYECTOS.md`](documentation/ETAPA7_GESTION_PROYECTOS.md) — guía de gestión y precarga.

En GitHub, abrí el archivo del paquete y elegí **Download raw file**, o descargá el repositorio con **Code → Download ZIP**. Mientras el repositorio sea privado, solo podrán acceder las cuentas autorizadas.

## Aplicar el parche en Fedora 44

1. Descargá el repositorio y la carpeta fuente existente de Creador Personalizado (base alpha.3 / Etapa 6).
2. Colocá `Etapa7-overlay-GPLv3.tar.gz` y `apply-etapa7-overlay.sh` en la misma carpeta.
3. Ejecutá:

```bash
chmod +x apply-etapa7-overlay.sh
./apply-etapa7-overlay.sh /ruta/a/Creador-Personalizado-3.0.0-alpha.3
```

El script valida el destino y el archivo comprimido, crea una copia temporal de los archivos existentes que reemplazará y aplica el parche. No elimina el resto del proyecto.

## Qué incorpora Etapa 7

- Gestor de proyectos independientes con UUID y almacenamiento local.
- Manifiesto `project.json` escrito de forma atómica.
- Directorios `assets/`, `builds/` y `logs/` por proyecto.
- Copia de recursos locales seleccionados al proyecto.
- Precarga de los perfiles nominales existentes: Terminal de Atención, Kiosco Navegador, Kiosco Multiventana, Equipo de Oficina y Estación de Trabajo.
- Plantillas generales adicionales: Kiosco, Oficina, Web, Gaming, Laboratorio de ciberseguridad y Personalizado.
- Acciones **Nuevo proyecto**, **Abrir proyecto** y **Guardar proyecto** en el panel principal.
- Recuperación del último proyecto abierto.
- No se persisten contraseñas, tokens ni secretos.

## Validación registrada

- `python -m compileall -q main.py core gui tests`: correcta.
- Pruebas seleccionadas: **30 passed**.
- Construcción de wheel: correcta.
- Suite completa, GUI Qt real, HiDPI y generación ISO: pendientes de validación en el Fedora 44 de destino. El entorno de preparación no tenía PySide6 para recolectar la suite completa.

Para revalidar en Fedora 44, después de aplicar el parche:

```bash
chmod +x scripts/run_acceptance.sh
./scripts/run_acceptance.sh
```

Antes de generar una ISO para uso real, revisar especialmente SSH: los perfiles nominales Equipo de Oficina y Estación de Trabajo heredan SSH habilitado de sus JSON originales.

## Integrar la aplicación completa alpha.4

**Estado de la rama `main`:** contiene el parche de Etapa 7 y la documentación; el árbol fuente completo todavía debe incorporarse desde el paquete integral. Para hacerlo sin reemplazar la licencia ni los antecedentes del repositorio:

1. Descargá el paquete `Creador-Personalizado-3.0.0-alpha.4-Full-GPLv3.zip` preparado para esta publicación.
2. Cloná este repositorio y descargá el importador [`import-full-app.sh`](import-full-app.sh) (o usá el que ya está en la raíz del clon).
3. Desde la carpeta del clon ejecutá:

```bash
chmod +x import-full-app.sh
./import-full-app.sh /ruta/al/Creador-Personalizado-3.0.0-alpha.4-Full-GPLv3.zip
```

El script comprueba que el destino sea este repositorio, que estés en la rama `main` y que no haya cambios locales pendientes. Copia el proyecto completo en la raíz, preserva el aviso GPL y el overlay histórico, prepara un commit y lo publica con `git push`. Si falla una comprobación, se detiene antes de hacer el commit.

## Incorporar el código completo sin descargar el ZIP de ChatGPT

Si ya tenés en Fedora la carpeta fuente de la Etapa 6 que usaste para las pruebas, podés publicar la aplicación completa directamente desde esa carpeta:

```bash
git pull --ff-only origin main
bash import-full-app-from-local-source.sh ~/Descargas/Creador-Personalizado-3.0.0-alpha.3
```

El importador copia el árbol fuente a una zona temporal, aplica el overlay GPLv3 de Etapa 7, conserva los avisos de licencia y los archivos históricos, y luego crea el commit y hace `git push`. No necesita descargar el ZIP generado en ChatGPT. Si la carpeta fuente está en otra ubicación, pasá esa ruta como argumento.

La carpeta local debe contener `main.py`, `pyproject.toml`, `requirements.txt`, `core/`, `gui/` y `profiles/`. El importador excluye entornos virtuales, cachés, reportes de pruebas, compilaciones y archivos ISO/RAW.
