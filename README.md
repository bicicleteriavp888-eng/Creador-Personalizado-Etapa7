# Creador Personalizado — Etapa 7

Versión: **3.0.0-alpha.4**

Esta entrega incorpora gestión independiente de proyectos y configuraciones precargadas por perfil.

## Contenido de la entrega

El archivo `Creador-Etapa7.zip` incluye el proyecto completo, perfiles, pruebas, documentación y scripts de validación.

## Validación registrada

- Compilación Python (`compileall`): correcta.
- Pruebas seleccionadas: **30 passed**.
- Construcción de wheel: correcta.
- Suite completa, GUI Qt real, HiDPI y generación ISO: pendientes de validación en Fedora 44 del usuario.

## Instalación y pruebas

Extraer el ZIP y ejecutar:

```bash
cd Creador-Personalizado-3.0.0-alpha.4
chmod +x scripts/run_acceptance.sh
./scripts/run_acceptance.sh
```

Consultar `INFORME_ETAPA7.md` y `CHANGELOG-ETAPA7.md` dentro del proyecto para el detalle de cambios y limitaciones conocidas.

> Esta versión es alpha. Antes de generar una ISO para uso productivo, revisar la configuración del proyecto y completar las pruebas en el equipo destino.
