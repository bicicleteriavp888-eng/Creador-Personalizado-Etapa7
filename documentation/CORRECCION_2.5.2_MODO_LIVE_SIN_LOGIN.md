# Creador-kiosk 2.5.2 — Arranque Kiosco tipo Live, sin LightDM ni contraseña

## Objetivo

Eliminar la pantalla de inicio de sesión del motor Kiosco. Al arrancar la ISO,
la aplicación debe iniciarse automáticamente, como en un entorno Live, sin
pedir usuario ni contraseña.

## Cambios

- Se elimina el paquete LightDM del conjunto de paquetes del motor Kiosco.
- Se retira Elephant Greeter del código distribuido y de los archivos instalados
  dentro de la ISO Kiosco.
- La GUI ya no presenta la opción de LightDM ni el selector de fondo del greeter.
- La contraseña deja de ser obligatoria y el campo se oculta cuando se elige el
  perfil `kiosk`. Los perfiles Fedora Desktop mantienen su contraseña.
- `kioskuser` se crea sin hash de contraseña y se bloquea con `usermod -L`.
  Esto impide el inicio de sesión interactivo con contraseña; no impide que
  systemd ejecute el servicio como ese usuario.
- `kiosk.service` se habilita directamente y el objetivo predeterminado queda
  en `multi-user.target`. Cage o Sway se ejecutan en TTY1 como `kioskuser`.
- Se retira `PAMName=login` del servicio: systemd usa `PAMName=` para abrir
  una sesión PAM y realizar la comprobación de cuenta; esa comprobación puede
  rechazar una cuenta bloqueada. El servicio no necesita autenticación PAM
  porque systemd establece directamente `User=kioskuser` y el directorio
  `RuntimeDirectory=user/%U` crea `/run/user/<UID>` con permisos `0700`
  y propiedad de `kioskuser`, sin depender de `pam_systemd` ni ejecutar
  `mkdir/chown` sin privilegios.
- `getty@tty1` queda enmascarado para que no compita por la terminal con
  `kiosk.service`.
- La autoverificación comprueba que la cuenta exista y que su campo de
  contraseña esté bloqueado, en lugar de exigir un hash SHA-512.
- Las preferencias antiguas `enable_lightdm` se ignoran. Una configuración
  guardada anteriormente no puede volver a activar el greeter.

## Alcance

El cambio afecta exclusivamente al motor Kiosco. El motor Fedora Desktop sigue
siendo independiente y conserva GDM, SDDM o LightDM según el escritorio elegido
(por ejemplo, Xfce/LightDM). No se modifican sus credenciales ni su Kickstart.

## Validaciones ejecutadas

- `py_compile` sobre los módulos Python modificados: correcto.
- 101 pruebas seleccionadas de constructor, validación, seguridad, motor Desktop
y procesos: correctas.
- Las pruebas se ejecutaron con un adaptador mínimo de señales Qt porque el
  entorno de auditoría no tiene PySide6 instalado. La suite completa de GUI no
  se considera validada por este motivo.
- No se generó una ISO ni se probó en QEMU o hardware físico.

## Prueba pendiente en Fedora

1. Generar una ISO nueva con el perfil `kiosk`.
2. Arrancar desde USB o en QEMU.
3. Confirmar que no aparece LightDM ni un prompt de usuario/contraseña.
4. Confirmar que Cage/Sway abre la aplicación automáticamente.
5. Comprobar que si la aplicación termina, `Restart=always` la vuelve a iniciar
   cuando esa opción está habilitada.
6. Elegir la entrada de Anaconda y comprobar que el instalador se abre sin
   solicitar inicio de sesión.

## Nota de seguridad

La cuenta `kioskuser` queda bloqueada para autenticación por contraseña. No se
habilita SSH por defecto. La política de `sudo` conserva la opción configurada
en el asistente; el modo sin contraseña se refiere al inicio automático del
Kiosco, no a conceder privilegios administrativos sin autenticación.
