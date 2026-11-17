# Creador Personalizado — Etapa 7

<sub>Versión del proyecto: **3.0.0-alpha.4** · Repositorio privado</sub>

Este repositorio distribuye el **parche de código de Etapa 7** y su documentación. No contiene una copia autónoma completa de la aplicación base. El parche se aplica sobre el árbol fuente de la versión anterior de Creador Personalizado (Etapa 6 / base alpha.3).

## Descargar desde GitHub

El archivo binario está en la raíz del repositorio:

- `Etapa7-overlay.tar.gz` — código modificado y documentación de Etapa 7.
- `INFORME_ETAPA7.md` — informe técnico.
- `CHANGELOG-ETAPA7.md` — resumen de cambios.
- `documentation/ETAPA7_GESTION_PROYECTOS.md` — guía de gestión y precarga.

Desde GitHub, abrir **Etapa7-overlay.tar.gz** y elegir **Download raw file**, o descargar el repositorio completo desde **Code → Download ZIP**. Como el repositorio es privado, hay que iniciar sesión con una cuenta autorizada.

## Aplicar el parche en Fedora 44

1. Descargar o clonar este repositorio.
2. Tener a mano la carpeta fuente existente de Creador Personalizado (base alpha.3 / Etapa 6).
3. Abrir una terminal en la carpeta descargada y ejecutar:

```bash
chmod +x apply-etapa7-overlay.sh
./apply-etapa7-overlay.sh /ruta/a/Creador-Personalizado-3.0.0-alpha.3
```

El script valida el destino y el archivo comprimido, crea una copia temporal de los archivos existentes que reemplazará y después aplica los archivos del parche. No elimina el resto del proyecto.

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
