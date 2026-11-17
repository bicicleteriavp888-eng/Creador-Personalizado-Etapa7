# Auditoría y reestructuración propuesta — Creador-kiosk 2.3

## Base revisada

Se revisó el código fuente del archivo `Creador-kiosk-2.2-fedora-a-medida(1).zip`.
La aplicación es Python/PySide6 y su motor principal está en `core/builder.py`.

## Hallazgos principales

1. **El producto sigue siendo un constructor de kioscos.** `KioskISOBuilder`
   genera una receta Kickstart que instala Cage o Sway, configura `kioskuser`,
   `kiosk.service` y valida los scripts de la sesión kiosco. El selector de
   paquetes previo solo agregaba nombres a `extra_packages`; no sustituía ese
   modelo por una distribución de escritorio general.
2. **Acoplamiento alto.** GUI, validación y constructor comparten campos y
   decisiones específicas de kiosco. La separación por `core/` y `gui/` es un
   buen comienzo, pero falta una interfaz común de motores de imagen.
3. **La búsqueda DNF depende del host.** `dnf repoquery` consulta los
   repositorios habilitados en el equipo donde se ejecuta Creador-kiosk. No es
   todavía un catálogo remoto independiente ni garantiza que el paquete exista
   para cualquier release/arquitectura objetivo.
4. **Compatibilidad de hardware no es todavía un perfil real.** No existe un
   selector completo de compatibilidad heredada para gráficos, Wi-Fi, touchpad
   y BIOS; esos cambios deben aplicarse al manifiesto de paquetes y a la
   configuración de arranque del sistema generado.
5. **La plantilla `mi_sitio/` es un sitio estático separado** y no forma parte
   del constructor de ISO. Debe quedar fuera de los paquetes de distribución
   de la aplicación, salvo que el proyecto decida integrarla como producto web.
6. **El verificador RPM tenía un caso de salida en inglés mal clasificado.** La forma `digests signatures OK` no coincidía con el patrón anterior; se corrigió y se conserva la detección localizada de los resúmenes SHA256 en español.
7. **Los cachés y bytecode no deben distribuirse.** `.pytest_cache/` y
   `__pycache__/` se excluyen de los artefactos de entrega.

## Cambios de esta revisión

- Se añadió `core/projects/catalog.py` como catálogo tipado de seis objetivos:
  kiosco, oficina, web/servicios, gaming, laboratorio de ciberseguridad y
  distribución personalizada.
- Se añadieron funciones para cargar perfiles aislados y combinar nombres de
  paquetes con validación estricta y deduplicación.
- La pantalla Nuevo proyecto ahora permite elegir un objetivo, leer su
  descripción y cargar una selección inicial de paquetes antes de consultar
  los repositorios Fedora.
- El tipo de proyecto se incluye en la configuración recogida por la GUI y se
  guarda como preferencia local.
- Se añadieron pruebas unitarias independientes para el catálogo y la
  validación de paquetes.
- Se corrigió el reconocimiento de `digests signatures OK` en inglés en el
  verificador RPM, además de los mensajes españoles `Header/Payload SHA256 resumen: OK`.

## Límite funcional explícito de esta entrega

Los perfiles de esta fase son **plantillas de selección de software**. El
constructor de ISO sigue siendo el motor kiosco heredado. Oficina, web,
gaming y laboratorio todavía no generan una sesión de escritorio propia; no
se deben presentar como motores finalizados ni desplegar como tales. El paso
siguiente es separar `KioskISOBuilder` en motores intercambiables y construir
un motor Fedora Desktop genérico con sesiones, usuarios, NetworkManager,
primer inicio y validación propios.

## Arquitectura objetivo

- `core/projects/`: modelo de proyecto, perfiles, validación y manifiesto.
- `core/repositories/`: repositorios por release/arquitectura, búsqueda,
  resolución de dependencias y caché.
- `core/builders/base.py`: contrato común para motores.
- `core/builders/kiosk.py`: conserva el motor actual.
- `core/builders/desktop.py`: motor general para GNOME/Xfce/KDE y selección
  de paquetes.
- `core/hardware/`: detección de GPU, Wi-Fi, audio, touchpad, firmware y modo
  de arranque; perfiles conservador/automático.
- `core/live/`: bienvenida Live, asistente Wi-Fi opcional, NetworkManager y
  diagnóstico de dispositivos.
- `core/validation/`: validación de manifiesto, paquetes, ISO y arranque.
- `gui/wizard/`: flujo progresivo con resumen persistente y navegación clara.

## Flujo de usuario propuesto

1. **Tipo de distribución:** kiosco, oficina, web, gaming, laboratorio o libre.
2. **Base y hardware:** Fedora/release/arquitectura, BIOS/UEFI y compatibilidad
   estándar o heredada.
3. **Escritorio y experiencia:** Cage/Sway para kiosco; GNOME, KDE o Xfce para
   escritorio; modo Live y asistente Wi-Fi.
4. **Software:** categorías y búsqueda de paquetes DNF, con dependencias,
   tamaño estimado y avisos de repositorios externos.
5. **Usuarios y seguridad:** cuentas, cambio de contraseña, firewall, SSH,
   SELinux, firmas RPM y servicios explícitos.
6. **Identidad y apariencia:** nombre, branding, idioma, zona horaria y tema.
7. **Resumen:** manifiesto legible, paquetes, espacio estimado y advertencias.
8. **Construir y probar:** compilación, validación, QEMU BIOS/UEFI, informe y
   escritura USB con confirmación.

## Seguridad y calidad

- No instalar ni activar servicios de red por el mero hecho de incluir un
  paquete de servidor.
- No incluir repositorios de terceros silenciosamente. Mostrar origen, licencia
  y condición de confianza antes de habilitarlos.
- Los perfiles de ciberseguridad se orientan a auditoría defensiva y pruebas
  autorizadas; no ejecutar escaneos o ataques automáticamente.
- Mantener la verificación de integridad RPM separada de la política de firma.
- No marcar una ISO como probada por el solo hecho de generarla o de que QEMU
  permanezca abierto hasta un timeout.

## Verificación ejecutada en este entorno

- `python -m compileall -q main.py gui core tests`: aprobado.
- `python -m pytest -q tests/test_project_templates.py tests/test_profiles_catalog.py`: 7 pruebas aprobadas.
- Suite de módulos independientes de Qt, incluyendo seguridad RPM: 39 pruebas aprobadas.
- La suite completa no pudo recolectarse en este entorno porque no está
  instalado PySide6 (`ModuleNotFoundError`). La GUI y el constructor requieren
  ejecución de pruebas en Fedora con las dependencias del proyecto.
