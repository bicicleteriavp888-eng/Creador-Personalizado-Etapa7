# Guía de aceptación final — Fedora 44

Esta guía complementa `INFORME_ETAPA6.md`. Ejecutar desde la raíz del proyecto en Fedora 44. No ejecutar como root salvo que un paso lo requiera expresamente.

## 1. Preparar entorno

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt
```

Comprobar PySide6:

```bash
python -c 'import PySide6; print(PySide6.__version__)'
```

## 2. Ejecutar aceptación automatizada

```bash
chmod +x scripts/run_acceptance.sh
./scripts/run_acceptance.sh
```

El script guarda logs, resumen y metadatos del entorno en `test-reports/`. Si falla, revisar primero el log del paso indicado en `summary.txt`.

## 3. GUI, navegación y temas

Iniciar la aplicación:

```bash
python main.py
```

Comprobar:

- Panel principal y datos del entorno.
- Navegación a todas las páginas y retorno al panel.
- Asistente de seis pasos: validación, avance y retroceso.
- Modalidades Desktop y Kiosco; confirmar que el selector de escritorio solo aplica a Desktop.
- Gestor de software: búsqueda, selección y simulación sin instalar paquetes en el host.
- Apariencia: tema claro y oscuro, contraste de tablas y estados.
- Configuración: guardar y restaurar; verificar que la contraseña no se persiste.
- USB: detección, confirmación y verificación; no confirmar escritura sobre un dispositivo real durante una prueba de interfaz.

## 4. Tamaños y escalado

Repetir el recorrido principal en:

| Perfil | Tamaño de ventana |
|---|---:|
| Compacto | 1080×720 |
| Medio | 1280×800 |
| Amplio | 1320×900 |

En cada tamaño:

- Revisar que botones, etiquetas, entradas y tablas no queden cortados.
- Confirmar que el scroll vertical sea funcional.
- Confirmar que las páginas comunes no tengan scroll horizontal accidental.
- Revisar tablas y paneles divididos después de cambiar el tamaño.

Si hay pantalla HiDPI disponible, repetir con el escalado del escritorio (por ejemplo, 125 % o 150 %) y anotar resolución física, factor de escala y resultado. No forzar variables de escalado sin registrar el valor original.

## 5. Operaciones largas y motores

- Abrir el gestor y ejecutar una consulta de repositorios con conectividad disponible.
- Confirmar que la ventana sigue respondiendo y que se puede navegar o cancelar cuando el flujo lo permita.
- Abrir un proyecto existente Desktop y verificar que mantiene `engine=desktop`.
- Abrir un proyecto existente Kiosco y verificar que mantiene `engine=kiosk`.
- Comprobar que el resumen de configuración refleja la modalidad elegida.

## 6. ISO de prueba (opcional y controlada)

Solo con espacio suficiente, dependencias completas y un directorio temporal:

- Ejecutar la validación previa del proyecto.
- Realizar una compilación de prueba para Desktop y otra para Kiosco, si ambos entornos están configurados.
- Registrar versión de Fedora, arquitectura, comandos, logs, duración y SHA-256 de cada ISO.
- No considerar una ISO válida solo porque el proceso terminó: inspeccionar metadatos y probar el arranque en un entorno de laboratorio cuando esté disponible.
- No escribir la ISO a un USB real como parte de esta aceptación.

## 7. Evidencias que deben guardarse

Crear una carpeta con fecha y guardar:

- `summary.txt` y logs de `test-reports/`.
- Capturas de panel y páginas representativas en tema claro/oscuro.
- Capturas en tamaños compacto, medio y amplio.
- Resultado de las pruebas de ambos motores.
- Incidencias encontradas, pasos para reproducir y capturas.
- Si se construyeron ISO: metadatos, logs y SHA-256.

La aceptación manual se considera aprobada solo si no hay controles cortados, scroll horizontal accidental, pérdida de navegación, congelamiento de interfaz ni cambio involuntario de motor/configuración.
