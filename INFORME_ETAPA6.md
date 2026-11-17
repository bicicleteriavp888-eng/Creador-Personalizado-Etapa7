# Informe de cierre — Etapa 6

**Producto:** Creador Personalizado — Constructor de distribuciones Fedora  
**Versión de código:** 3.0.0-alpha.3  
**Etapa:** 6 — Pruebas y entrega  
**Base validada:** `Creador-Personalizado-3.0.0-alpha.3-Etapa5.zip`  
**Fecha de ejecución:** 2026-11-17  
**Plataforma objetivo del producto:** Fedora 44

## 1. Resumen ejecutivo

Se realizó la validación automatizada posible en el entorno de trabajo y se preparó una entrega limpia con el informe, el changelog de etapa y una guía para completar las verificaciones que requieren Fedora 44 y PySide6 real.

**Resultado:** 111 pruebas automatizadas pasaron. La compilación de bytecode Python, la sintaxis de los scripts shell y la construcción del wheel también finalizaron correctamente.

La etapa queda **cerrada en cuanto a validación automatizada reproducible en este entorno**, pero no se declara certificación integral de GUI ni de generación de ISO: PySide6 no está instalado aquí. Por ello no fue posible ejecutar las pruebas Qt, comprobar visualmente el redimensionado/HiDPI ni realizar una compilación real de Fedora. La guía incluida permite completar esos controles en el equipo Fedora 44.

## 2. Entorno de pruebas

| Elemento | Resultado |
|---|---|
| Sistema del entorno de ejecución | Linux de contenedor (no Fedora 44) |
| Python | 3.13.5 |
| pytest | 9.0.2 |
| PySide6 | No instalado |
| PyYAML | 6.0.3 |
| Pillow | 12.3.0 |
| Plataforma Qt | No disponible; no se ejecutó GUI real |

La primera invocación de `pytest` no encontró los paquetes locales porque no estaba definida la ruta de importación. Se corrigió la invocación con `PYTHONPATH=.`; los errores restantes fueron dependencias PySide6 ausentes, no fallos de aserciones.

## 3. Pruebas ejecutadas

| Comprobación | Resultado |
|---|---:|
| Suite compatible con el entorno | **111 passed** |
| Prueba dependiente de PySide6 excluida explícitamente | 1 deselected |
| Módulos no colectados por ausencia de PySide6 | 6 |
| `python -m compileall -q .` | Correcto |
| `bash -n` en scripts de ejecución e instalación | Correcto |
| `pip wheel --no-deps --no-build-isolation` | Correcto |

Wheel generado durante la comprobación:

- Archivo: `creador_personalizado-3.0.0a3-py3-none-any.whl`
- Tamaño: 224,949 bytes
- SHA-256: `6f03d7de113d592ae4eb34f96b9c7b629a8be5ac258292cf7b0e34be29aa54c2`

### 3.1 Suite pytest compatible

Comando exacto:

```bash
PYTHONPATH=. pytest -q \
  --ignore=tests/test_build_engines.py \
  --ignore=tests/test_builder.py \
  --ignore=tests/test_gui_redesign.py \
  --ignore=tests/test_gui_smoke.py \
  --ignore=tests/test_gui_validation.py \
  --ignore=tests/test_usb.py \
  --deselect=tests/test_desktops.py::test_el_perfil_kiosco_conserva_sus_componentes
```

Salida: `111 passed, 1 deselected`.

La exclusión no se debe a una prueba fallida: los módulos indicados importan PySide6 durante la colección. El test de `test_desktops.py` indicado importa `core.builder`, que también requiere PySide6.

### 3.2 Construcción de paquete

Comando:

```bash
python -m pip wheel --no-deps --no-build-isolation -w /tmp/wheels .
```

Resultado: wheel construido correctamente. Esto valida metadatos y empaquetado Python; no equivale a instalar la aplicación en Fedora ni a construir una ISO.

## 4. Cobertura existente revisada

El repositorio incluye pruebas específicas para:

- Humo de GUI y navegación del asistente.
- Cambio de tema claro/oscuro.
- Persistencia de configuración sin guardar la contraseña.
- Validación de pasos y compatibilidad del diccionario de configuración.
- Comportamiento del gestor de software y estado separado del asistente.
- Contraste de colores y reglas de tablas.
- Ausencia de scroll horizontal en áreas comunes a 1080×720.
- Historial de compilaciones.
- Motores Desktop/Kiosco, seguridad, perfiles, procesos y USB.

La existencia de estas pruebas se verificó en el código. Las pruebas Qt no se consideran ejecutadas en esta sesión porque no se pudo importar PySide6.

## 5. Verificaciones pendientes en Fedora 44

Estas verificaciones requieren el entorno de destino y quedan claramente identificadas como pendientes:

1. Instalar dependencias con el método documentado en `README.md`.
2. Ejecutar la suite completa con PySide6 real.
3. Abrir la aplicación y recorrer panel, asistente, gestor de software y herramienta USB.
4. Repetir las pruebas visuales en 1080×720, 1280×800 y 1320×900; comprobar también escalado HiDPI disponible.
5. Confirmar que no hay controles cortados ni scroll horizontal accidental.
6. Verificar ambos temas y la legibilidad de tablas.
7. Comprobar que una consulta/operación prolongada no bloquea la interfaz.
8. Abrir proyectos existentes de modalidad Desktop y Kiosco y confirmar que mantienen su motor.
9. Si el entorno dispone de dependencias y recursos, realizar una compilación ISO de prueba por modalidad. No escribir USB ni usar operaciones privilegiadas sin autorización explícita.

Los pasos reproducibles están en `documentation/GUIA_VALIDACION_FEDORA44_ETAPA6.md`.

## 6. Integridad de arquitectura y alcance

Esta etapa se centró en pruebas, empaquetado y documentación. No se reescribieron los motores de construcción ni se fusionaron las modalidades Desktop y Kiosco. No se sustituyeron servicios reales por mocks en el producto.

No se declara que se haya generado o arrancado una ISO, que se haya escrito una unidad USB, ni que se haya inspeccionado la GUI en pantalla durante esta ejecución.

## 7. Archivos agregados para esta etapa

- `INFORME_ETAPA6.md`: resultados, alcance y limitaciones.
- `CHANGELOG-ETAPA6.md`: resumen de la entrega.
- `documentation/GUIA_VALIDACION_FEDORA44_ETAPA6.md`: pasos para completar la validación en el sistema destino.

## 8. Conclusión

La entrega supera las comprobaciones automatizadas que podían ejecutarse en este entorno: **111 pruebas pasaron**, Python compiló sin errores de sintaxis, los scripts shell validaron su sintaxis y el wheel se construyó correctamente.

La aceptación visual final y la validación de los flujos reales de GUI/ISO dependen de ejecutar la guía en Fedora 44 con PySide6 instalado. Hasta entonces, el estado correcto es: **Etapa 6 automatizada completada; validación manual en Fedora 44 pendiente**.
