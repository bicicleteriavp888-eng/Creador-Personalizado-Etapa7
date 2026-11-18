# Estado de publicación — Creador-Personalizado 3.0

**Revisión:** 18 de noviembre de 2026  
**Rama revisada:** `main`  
**Commit de referencia:** `2d58ff6fabe609828f33e8f39a974c84d9f09958`

## 1. Estado verificable de la rama principal

La rama `main` contiene el código fuente identificado por el manifiesto de proyecto como **3.0.0a4**:

- `pyproject.toml`: `version = "3.0.0a4"`.
- `README.md` fue renovado para describir la identidad del producto y sus dos motores.
- El changelog disponible contiene historial de las versiones 2.x; no existe en esta rama un changelog alpha.7.
- No se encontró en esta rama el informe `CHANGELOG-3.0.0-alpha.7.md` ni `documentation/CAMBIOS_ALPHA7_AISLAMIENTO_KIOSCO_E_INSTALADOR.md`.

Por tanto, **alpha.7 no está publicada en la rama principal** y el número de versión del paquete no debe adelantarse hasta integrar el código fuente correspondiente.

## 2. Estado de alpha.7 conocido por el registro de desarrollo

La entrega alpha.7 fue preparada como un artefacto separado en el flujo de trabajo anterior. El alcance informado para esa entrega fue:

- Separar la configuración de aplicación y multiventana Kiosco en una página exclusiva, visible únicamente para el motor Kiosco.
- Mantener el paso 3 orientado al software Fedora y al escritorio Desktop.
- Separar visualmente opciones específicas de Kiosco (por ejemplo, bloqueo de terminales virtuales y resolución wlr-randr) de las opciones comunes o Desktop.
- Conservar la personalización de imagen y texto del instalador al alternar proyectos y al usar el modo Simple.
- Incorporar generación de banner y mensaje de bienvenida del instalador en el generador Kickstart Desktop.
- Corregir la restauración de identificador de perfil y evitar que proyectos sin texto explícito hereden el texto de bienvenida de otro proyecto.

Este apartado registra el alcance de trabajo comunicado para el artefacto alpha.7; **no certifica que esos cambios estén presentes en el código de esta rama**. Para publicar la versión es necesario incorporar el ZIP/código exacto de alpha.7 y repetir la verificación sobre ese contenido.

## 3. Evidencia de pruebas comunicada para el artefacto alpha.7

En el entorno de preparación se informó:

- Compilación sintáctica de archivos Python: correcta.
- Pruebas seleccionadas sin módulos Qt: `46 passed, 1 deselected`.
- Ejecución adicional excluyendo módulos dependientes de PySide6: `126 passed, 1 deselected`.
- Verificación de `SHA256SUMS.txt`: correcta.
- Integridad estructural del ZIP: correcta.
- PySide6 no estaba disponible en ese entorno; por eso no se ejecutó la suite GUI completa.
- No se informó una compilación real de ISO ni un arranque BIOS/UEFI de la imagen resultante.

Estos resultados son evidencia histórica del proceso de preparación, no una ejecución reproducida sobre el contenido actualmente publicado en GitHub.

## 4. Requisitos para publicar alpha.7

Antes de actualizar `pyproject.toml`, el changelog o crear una etiqueta de versión:

1. Incorporar el artefacto fuente exacto alpha.7 a un entorno de trabajo.
2. Comparar su base con el commit de esta rama y revisar todos los cambios.
3. Verificar que no se pierdan cambios publicados en GitHub después de crear el artefacto.
4. Ejecutar `python3 -m compileall -q .`.
5. Ejecutar la suite completa en Fedora con PySide6 disponible: `python3 -m pytest -q`.
6. Revisar las pruebas fallidas/omitidas y registrar los conteos reales.
7. Inspeccionar el ZIP final, generar y verificar SHA-256.
8. Publicar código, changelog e informe técnico en un commit identificable.
9. Crear una etiqueta alpha.7 únicamente después de verificar el commit publicado.
10. Mantener explícito que la generación de ISO y el arranque real requieren validación separada si no se ejecutan.

## 5. Límites de validación funcional

La generación de recursos de banner y texto en Kickstart no demuestra por sí sola que Anaconda los presente visualmente en todas las variantes del instalador. Esa comprobación requiere una ISO real y una prueba del instalador.

Del mismo modo, las pruebas unitarias no demuestran que una ISO Desktop o Kiosco arranque correctamente en hardware. Se deben registrar por separado las pruebas de construcción, arranque BIOS/UEFI, red, gráficos y periféricos.

## 6. Estado del nombre del repositorio

En la fecha de esta revisión, la API de GitHub sigue identificando el repositorio como:

`bicicleteriavp888-eng/Creador-Personalizado-Etapa7`

El nombre objetivo propuesto es:

`Creador-Personalizado-Fedora-Distribucion`

El cambio de nombre administrativo todavía no está aplicado. El README actualizado no modifica por sí mismo el nombre del repositorio.

## 7. Próximo paso requerido

Adjuntar o volver a subir el archivo **`Creador-Personalizado-3.0.0-alpha.7.zip`** preparado en la sesión anterior. Si el archivo no está disponible, no reconstruir el código a partir de esta descripción: recuperar primero la fuente exacta para evitar publicar una versión incompleta o divergente.
