# Informe de implementación y pruebas — Creador-kiosk 2.1

**Fecha:** 13/11/2026  
**Entorno:** Linux de revisión, Python 3.13.5; no es Fedora y no tiene PySide6, DNF, QEMU ni OVMF.

## Trabajo incorporado

- Historial SQLite automático desde `KioskISOBuilder.build`: ID, tiempos, estado, ruta, SHA-256, log y configuración redactada.
- Herramienta CLI para consultar el historial.
- Respaldos TAR.GZ con manifiesto SHA-256, verificación, rechazo de rutas duplicadas/traversal/enlaces y restauración solo a destino vacío.
- Perfiles con identificadores seguros, escritura atómica, importación y exportación.
- Rechazo de paquetes bloqueados y verificación estricta de firmas RPM locales con claves de confianza.
- Inspector ISO xorriso/isoinfo y CLI de laboratorio con informes TXT/JSON y QEMU BIOS/UEFI opcional en snapshot, sin red ni discos físicos del host.
- Metadatos de distribución Python, lanzador, escritorio, instalador y desinstalador Fedora.
- Prompt Maestro y seguimiento actualizados con criterios de aceptación y prohibición de simular pruebas.

## Resultados reproducibles en este entorno

| Comprobación | Resultado |
|---|---|
| `python3 -m compileall -q .` | Correcto |
| Pruebas focalizadas sin shim (historial, perfiles, seguridad, ISO, runner, catálogo) | **32 passed** |
| Suite backend/validación/USB con shim temporal QtCore, excluyendo GUI smoke | **107 passed** |
| Construcción wheel con `pip wheel --no-deps --no-build-isolation` | Correcta; contenido principal y datos inspeccionados |
| `bash -n` instalador/desinstalador/lanzadores | Correcto |
| Crear, verificar y restaurar respaldo desde CLI | Correcto; 212 archivos en la prueba de aceptación inicial |
| CLI de validación ISO y CLI de respaldo (`--help`) | Correcto |

### Interpretación de las pruebas

El shim temporal solo permite importar y probar la lógica backend que depende de `QtCore`; no reemplaza PySide6 ni valida renderizado, eventos reales, accesibilidad o interacción gráfica. La prueba GUI smoke se excluyó.

La ejecución normal de `pytest` sin shim no puede recolectar cuatro módulos porque PySide6 no está instalado en este entorno.

## Etapas: estado real

| Etapa | Estado de implementación | Validación que falta |
|---|---|---|
| 1–3 | Históricamente validadas en auditoría 2.0 | Regresión con la versión actual |
| 4 | Motor modular y runner integrados parcialmente | Integración completa Builder/GUI y cancelación en Fedora |
| 5 | CRUD/import/export y catálogo | Revisión de esquema y prueba en Fedora |
| 6 | Hash de clave temporal, allowlist y firma RPM | PAM/LightDM, autologin Live, instalación, primer cambio de clave y elevación |
| 7 | Herramientas de inspección y laboratorio implementadas | ISO real, QEMU BIOS y UEFI, revisión visual |
| 8 | Historial y respaldos implementados y probados | Uso real en Fedora y recuperación operativa |
| 9 | 107 pruebas backend/USB/validación pasan con shim | Suite completa con PySide6 real y GUI smoke |
| 10 | Wheel, instalador y desinstalador preparados | Instalación limpia en Fedora y actualización/desinstalación |

## Comandos de aceptación en Fedora

```bash
sudo dnf install python3-pyside6 python3-pytest qemu-system-x86-core edk2-ovmf
bash scripts/run_acceptance.sh
```

Después de generar una ISO de prueba:

```bash
bash scripts/run_acceptance.sh /ruta/a/creador-kiosk.iso --boot-mode dual --qemu --timeout 90
```

El informe queda en `test-reports/`. Para cerrar la política de contraseña, comprobar `chage -l kioskuser` en Live y en el sistema instalado, realizar el primer inicio interactivo y confirmar que el kiosco no queda bloqueado por el autologin.

## Conclusión

La mayor parte del trabajo de código y automatización que puede completarse sin el host Fedora está incorporada. **No se declara release final ni se marcan todas las etapas como validadas**: todavía faltan pruebas dependientes de PySide6 real, Fedora, una ISO construida y arranques QEMU BIOS/UEFI. No se han simulado esos resultados.
