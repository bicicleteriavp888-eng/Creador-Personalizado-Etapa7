# Seguimiento de etapas — Creador-kiosk 2.1

**Fecha de referencia:** 13/11/2026  
**Fuente de estado:** archivos del ZIP recibido y `documentation/AUDITORIA_2.0.md`.  
**Regla:** este tablero es una línea base documental. Los estados no sustituyen una ejecución de pruebas en el equipo Fedora objetivo.

## Resumen ejecutivo (actualizado)

- Etapas 1–3: validadas históricamente en la auditoría 2.0; se debe repetir regresión tras cambios.
- Etapa 4: motor modular ampliado; continúa pendiente la prueba completa de integración Builder/GUI en Fedora.
- Etapa 5: CRUD/importación/exportación de perfiles con protección de rutas y pruebas automatizadas.
- Etapa 6: se exige firma RPM verificable y se bloquean paquetes inseguros; PAM/LightDM, privilegios y flujo de expiración requieren cierre real.
- Etapa 7: CLI de laboratorio, inspección El Torito mejorada e intento QEMU BIOS/UEFI implementados; no existe ISO real para certificar en este entorno.
- Etapa 8: historial SQLite integrado al ciclo de compilación; snapshots TAR.GZ con manifiesto, verificación y restauración segura implementados.
- Etapa 9: 32 pruebas focalizadas aprobadas; con un shim QtCore temporal, 107 pruebas de backend/validación/USB aprobaron (GUI smoke excluida); la ejecución real con PySide6 sigue pendiente.
- Etapa 10: metadatos Python, lanzador, entrada de escritorio e instalador Fedora preparados; instalación real en Fedora no ejecutada.

## Tablero de etapas

| Etapa | Estado inicial | Evidencia disponible | Criterio para cerrar |
|---|---|---|---|
| 1. Auditoría | VALIDADA | `documentation/AUDITORIA_2.0.md` contiene inventario, riesgos y plan | Mantener auditoría actualizada ante cambios de arquitectura |
| 2. Estabilización | VALIDADA | Auditoría documenta correcciones y 62 pruebas al cierre de etapa | Regresión completa sin fallos en entorno objetivo |
| 3. Interfaz profesional | VALIDADA | Auditoría documenta asistente, modos, temas, panel y 84 pruebas | Repetir humo GUI al modificar interfaz |
| 4. Motor modular | EN CURSO | `core/kickstart`, `core/processes`, `core/repositories`, `core/security`, `core/validation`, `core/iso`; `tests/test_modular_engine.py`; el Builder delega ejecución/cancelación de procesos a `core.processes.runner` | Contratos, eventos reales, cancelación/limpieza, fachada compatible y pruebas golden Kickstart |
| 5. Perfiles y catálogo | IMPLEMENTADA / PRUEBAS PARCIALES | `core/profiles/manager.py` con CRUD/import/export y validación de clave; catálogo y `tests/test_profile_security.py` | Validar esquema completo y consulta real en Fedora |
| 6. Seguridad | EN CURSO | `core/security/` con allowlist, credentials, policy y verificador RPM; Builder rechaza paquetes bloqueados y RPM no confiables; pruebas negativas añadidas | Pruebas de firmas/procedencia, permisos, auditoría de elevación, rechazo de entradas inseguras y validación PAM/LightDM de expiración |
| 7. Laboratorio ISO | IMPLEMENTADO / SIN ISO REAL | `scripts/validate_iso.py`, `core/iso/iso_inspector.py`, validador e informes QEMU; reportes distinguen modos requeridos | Ejecutar con una ISO real; BIOS/UEFI QEMU y revisión visual |
| 8. Historial y respaldos | IMPLEMENTADA / PRUEBAS FOCALES | `core/history/manager.py`, integración en `KioskISOBuilder.build`, `scripts/build_history.py`, `scripts/backup_project.py`, `tests/test_history.py` | Probar uso continuado y recuperación en Fedora; agregar UI de consulta si se requiere |
| 9. Pruebas integrales | EN CURSO | `tests/` contiene pruebas de builder, GUI, perfiles, catálogo, seguridad y módulos | Suite completa reproducible, integración de laboratorio/historial y GUI; fallos corregidos |
| 10. Distribución | PREPARADA / NO INSTALADA | `pyproject.toml`, `MANIFEST.in`, `packaging/install-fedora.sh`, `.desktop`, lanzador | Ejecutar instalador en Fedora limpio y verificar desinstalación/actualización |

## Bloqueos y limitaciones conocidos

1. No se ejecutó compilación ISO completa ni arranque BIOS/UEFI en la auditoría base.
2. La auditoría indica un host con 3 GiB RAM y `sudo -n` no disponible; las operaciones privilegiadas requieren intervención controlada.
3. En el entorno de revisión, `python3 -m compileall -q .` termina correctamente. La suite total falla durante la colección por `ModuleNotFoundError: No module named 'PySide6'`; se ejecutaron por separado 32 pruebas focalizadas y 107 pruebas backend/USB/validación con un shim QtCore temporal (GUI smoke excluida).
4. No declarar QEMU/ISO aprobados hasta ejecutar las pruebas reales en el host objetivo.
5. El instalador Fedora no se ejecutó porque el entorno actual no es Fedora y no dispone de DNF ni acceso a QEMU/OVMF.

## Validaciones pendientes en el entorno Fedora objetivo

### Etapa 4 — Integración final del motor
- Inventariar API pública de `core/builder.py` y consumidores.
- Revisar módulos extraídos y evitar lógica duplicada.
- Implementar/validar eventos de build con etapas y tiempos reales, ID de build, cancelación y limpieza.
- Añadir pruebas de contrato y Kickstart golden.
- Ejecutar compileall, suite completa y GUI smoke.

### Etapa 5 — Cierre de integración de perfiles y catálogo
- Verificar CRUD, duplicación, confirmación al eliminar, import/export y migración de schema.
- Verificar que el catálogo consulta repositorios seleccionados y no presume disponibilidad.

### Etapa 6 — Cierre de seguridad en PAM/LightDM y elevación
- Revisar verificación de firma RPM, allowlist, repositorios y privilegios.
- Añadir pruebas negativas y auditoría de operaciones privilegiadas.

### Etapa 7 — Laboratorio con ISO real
- Inspección ISO9660/El Torito/EFI/kernel/initramfs.
- Validación Kickstart/paquetes y reporte.
- QEMU BIOS y UEFI con discos virtuales descartables.

### Etapas 8–10 — Aceptación en Fedora
- Confirmar consulta de historial y restauración desde el entorno instalado.
- Ejecutar suite real con PySide6 y pruebas GUI smoke.
- Instalar y desinstalar en Fedora limpio; generar y arrancar una ISO de prueba.

## Registro de sesiones

| Fecha | Etapa | Trabajo | Pruebas/evidencia | Resultado | Próximo paso |
|---|---|---|---|---|---|
| 2026-11-13 | Línea base 2.1 | Se incorporó este tablero y el protocolo de seguimiento al Prompt Maestro 2.1. | `compileall` correcto; pytest general bloqueado por ausencia de PySide6. | Seguimiento creado; no se modificó la lógica de la aplicación. | Auditar/cerrar ETAPA 4 con pruebas en el entorno Fedora objetivo. |
| 2026-11-13 | Seguridad: clave inicial temporal | Se eliminó el mínimo de 12 caracteres; se centralizó el hash SHA-512; se añadió caducidad con `chage --lastday 0` y paquete `shadow-utils`; se actualizó GUI, README y Prompt Maestro. | `python3 -m compileall -q .` correcto. `python3 -m pytest -q tests/test_process_runner.py tests/test_security.py`: 8 passed. Suite general no recolecta por falta de PySide6. | Cambio implementado; falta probar expiración real en Live y tras instalación, especialmente PAM/LightDM y sesiones automáticas. | Ejecutar en Fedora una ISO de prueba y verificar `chage -l kioskuser`, primer login y persistencia de `/etc/shadow` tras instalar. |
| 2026-11-13 | Etapa 4: ejecución modular | `core.builder` ahora delega ejecución, comprobación y cancelación de procesos en `core.processes.runner`, conservando las fachadas privadas para compatibilidad. Se añadieron pruebas del ejecutor. | `python3 -m compileall -q .` correcto; `python3 -m pytest -q tests/test_process_runner.py tests/test_security.py`: 8 passed. Suite completa bloqueada durante colección por ausencia de PySide6. | Refactor acotado implementado; falta integración/regresión en Fedora. | Ejecutar `tests/test_builder.py` y suite completa en Fedora con PySide6. |
| 2026-11-14 | 2.5 — Etapas 4 y 5 | Flujo guiado implementado: tipo de distribución (paso 1), escritorio (paso 3), validación de tipo, resumen (paso 6); módulos de hardware en `core/desktops/hardware.py` (gráficos, Wi-Fi, touchpad, asistente Live). Versión 2.5.0. | `python3 -m compileall -q main.py gui core tests` correcto. `python3 -m pytest -q`: **213 passed**. | Etapas 4 y 5 implementadas con pruebas; no se generó ISO ni QEMU/hardware físico. | Laboratorio: compilar ISO Desktop en Fedora 44 y probar BIOS/UEFI en QEMU; cerrar etapa 10 (empaquetado). |

## Plantilla para cada cierre de etapa

- **Estado:**
- **Fecha:**
- **Archivos modificados:**
- **Criterios completados:**
- **Comandos ejecutados:**
- **Resultados exactos:**
- **Evidencia (logs/reportes/capturas):**
- **Pendientes/bloqueos:**
- **Aprobación de puerta:** sí/no (justificación)


## Política de contraseña inicial (actualización 2026-11-13)

- Se permite cualquier contraseña inicial no vacía de hasta 128 caracteres, sin caracteres de control ni saltos de línea.
- El hash se genera con SHA-512; la contraseña en texto plano no se persiste en perfiles ni configuraciones.
- El `%post` instala `shadow-utils` y ejecuta `chage --lastday 0 kioskuser`. Esto exige cambio en el siguiente inicio de sesión interactivo.
- La política está incorporada en la imagen Live y se espera que viaje con la cuenta al sistema instalado. Debe verificarse en una instalación real.
- La caducidad no cambia la contraseña por sí sola. Una sesión automática del kiosco que no pase por PAM no mostrará el diálogo; validar el flujo de acceso interactivo y documentar el procedimiento de cambio.


## Registro de sesión — cierre de implementación disponible (2026-11-13)

| Etapa | Trabajo nuevo | Evidencia local | Estado honesto |
|---|---|---|---|
| 4 | El Builder registra ID de build y delega procesos al runner modular. | `compileall`; pruebas runner y builder no-GUI parciales | Integración completa pendiente |
| 5 | Perfiles con clave segura, escritura atómica, importación/exportación. | 32 pruebas focalizadas incluyen CRUD y rechazo de traversal | Implementación verificada parcialmente |
| 6 | Se conserva contraseña inicial corta no vacía; hash SHA-512; `chage --lastday 0`. | pruebas de credenciales y política | PAM/LightDM y Live/instalado requieren validación real |
| 7 | Inspector xorriso/isoinfo, CLI JSON/TXT, intento QEMU BIOS/UEFI. | compileall; script --help | ISO real y QEMU no ejecutados |
| 8 | SQLite registra compilaciones y SHA-256; backups TAR.GZ con manifiesto y restauración segura. | tests de ciclo, redacción, integridad y traversal | Implementación y pruebas focales aprobadas |
| 9 | Añadidas pruebas de historial, perfiles y restauración. | 32 focalizadas passed; 107 passed con shim QtCore, GUI smoke excluida; PySide6 real no disponible | Parcial |
| 10 | pyproject, manifest, lanzador, .desktop e instalador Fedora. | compileall y revisión estática | Instalación limpia no ejecutada |

### Prueba ejecutada en el entorno de revisión

- `python3 -m compileall -q .`: correcto.
- `python3 -m pytest -q tests/test_history.py tests/test_profile_security.py tests/test_profiles_catalog.py tests/test_modular_engine.py tests/test_process_runner.py tests/test_package_checker.py tests/test_security.py tests/test_iso_lab.py`: **32 passed**.
- Con shim QtCore temporal: `PYTHONPATH=/tmp/qtstub:$PWD python3 -m pytest -q --ignore=tests/test_gui_smoke.py`: **107 passed**. El shim no sustituye la ejecución real con PySide6.
- Sin shim, la colección total se bloquea por ausencia de PySide6 en cuatro módulos.
- No se compiló una ISO; no se probó QEMU, BIOS, UEFI ni instalación física/virtual.


## Actualización: aceptación explícita de RPM sin firma

- Se agregó `allow_unsigned_rpms` a la configuración de compilación; el valor predeterminado es `false`.
- La interfaz ofrece una casilla en Selección de software (modo Avanzado) y exige confirmación adicional.
- Solo se acepta un RPM clasificado como realmente sin firma y con `digests OK`.
- Una firma presente pero inválida/no confiable, o digests incorrectos, no se pueden omitir con esta opción.
- La decisión queda en el JSON de configuración del historial de compilación.
- Pruebas locales disponibles: `tests/test_security.py`, `tests/test_history.py` y `tests/test_package_checker.py`. La integración Qt completa requiere PySide6 en Fedora.
