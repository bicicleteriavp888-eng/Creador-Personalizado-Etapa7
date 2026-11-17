# Informe técnico — Etapa 7

**Proyecto:** Creador Personalizado  
**Versión:** 3.0.0-alpha.4  
**Fecha:** 16 de noviembre de 2026  
**Estado:** implementación entregada; aceptación final en Fedora 44 pendiente

## 1. Objetivo

Incorporar gestión de proyectos independientes y precarga inicial según el tipo de sistema a construir, manteniendo separados los motores Desktop y Kiosco y conservando los flujos existentes.

## 2. Cambios implementados

### Almacenamiento de proyectos
- Nuevo módulo `core/projects/manager.py` con `ProjectStore`.
- Identificador UUID por proyecto.
- Manifiesto `project.json` con guardado atómico mediante archivo temporal y `os.replace`.
- Directorios propios `assets/`, `builds/` y `logs/`.
- Copia de recursos locales al proyecto y resolución de rutas relativas al cargar.
- No se guardan contraseñas, tokens ni secretos.

### Catálogo y precargas
- Se conservan y leen los cinco perfiles nominales existentes: Terminal de Atención, Kiosco Navegador, Kiosco Multiventana, Equipo de Oficina y Estación de Trabajo.
- Se agregan seis plantillas generales: Kiosco, Oficina, Web, Gaming, Laboratorio de ciberseguridad y Personalizado.
- La precarga utiliza los JSON originales para los perfiles nominales, incluyendo URL, modalidad, opciones de arranque y seguridad.
- Las opciones precargadas son editables antes de construir.

### Integración de interfaz
- Acciones Nuevo proyecto, Abrir proyecto y Guardar proyecto.
- Restauración del último proyecto abierto.
- Persistencia del proyecto activo al guardar, cerrar y antes de iniciar una compilación.
- Destino ISO inicial dentro de la carpeta `builds/` del proyecto.
- Al cambiar el tipo de proyecto se actualiza el motor de construcción correspondiente.

## 3. Archivos principales modificados o añadidos

- `core/projects/manager.py`
- `core/projects/catalog.py`
- `core/projects/__init__.py`
- `main.py`
- `gui/tab_meta.py`
- `gui/custom_distro.py`
- `tests/test_project_store.py`
- `tests/test_branding_3.py`
- `pyproject.toml`
- Documentación de Etapa 7.

## 4. Validación realizada en el entorno de preparación

| Comprobación | Resultado |
|---|---|
| `python -m compileall -q main.py core gui tests` | Correcto |
| Pruebas seleccionadas de proyectos, branding, plantillas, catálogo, historial y política de software | **30 passed** |
| Construcción del wheel con `pip wheel . --no-deps --no-build-isolation` | Correcta |
| Wheel generado | `creador_personalizado-3.0.0a4-py3-none-any.whl` |
| SHA-256 del wheel | `118ee0b7395a93a37bf808d926aa932a3b2b9634da6597d3a4d5c6fcb2b50d4b` |

El wheel fue inspeccionado y contiene el gestor de proyectos y los perfiles de distribución.

## 5. Validaciones pendientes en el Fedora 44 de destino

- La suite completa no se ejecutó aquí porque el entorno de preparación no tenía PySide6 y no pudo recolectar los tests que dependen de Qt.
- GUI real, HiDPI, alternancia entre proyectos con reinicio y recuperación no fueron comprobados en este entorno.
- No se generó una ISO real durante esta etapa.
- Antes de compilar, revisar las opciones SSH heredadas de los perfiles Equipo de Oficina y Estación de Trabajo, que lo dejan habilitado en sus JSON originales.

Ejecutar en Fedora 44:

```bash
chmod +x scripts/run_acceptance.sh
./scripts/run_acceptance.sh
```

Después realizar la prueba manual documentada en `documentation/ETAPA7_GESTION_PROYECTOS.md`.

## 6. Formato de publicación en este repositorio

Por la limitación de transferencia binaria de la integración, el repositorio distribuye las modificaciones de Etapa 7 como `Etapa7-overlay.tar.gz`, junto con el script `apply-etapa7-overlay.sh`. Este archivo es un **parche de actualización**, no una copia autónoma completa de la aplicación. Debe aplicarse sobre el árbol fuente base de la versión anterior (Etapa 6 / alpha.3).

La suma SHA-256 del archivo publicado figura en `SHA256SUMS.txt`.
