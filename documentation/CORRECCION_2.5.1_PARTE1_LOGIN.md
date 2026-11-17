# Creador-kiosk 2.5.1 — Corrección de autenticación (parte 1)

## Alcance

Esta corrección afecta exclusivamente al motor Kiosco (`core/builder.py`).
No modifica el motor Fedora Desktop ni el código de Elephant Greeter.

## Problema

Cuando `enable_lightdm` está activado, el constructor instala LightDM + Elephant
Greeter. Sin embargo, `_post_base()` también ejecutaba `chage --lastday 0
kioskuser` si `force_password_change` estaba activado (su valor predeterminado).
Eso marca la contraseña como vencida y obliga a PAM a iniciar el flujo de cambio
de contraseña en el primer acceso. Elephant Greeter no implementa ese flujo.

## Cambio aplicado

Se separa la existencia de la contraseña inicial de su caducidad:

- Se sigue generando e instalando el hash SHA-512 de la contraseña configurada.
- Con LightDM + Elephant Greeter, no se ejecuta `chage --lastday 0`.
- Sin LightDM, se conserva el comportamiento anterior: si se exige cambio de
  contraseña, la clave se marca como temporal.
- El modo sin contraseña inicial mantiene su comportamiento anterior.

## Pruebas

- `py_compile` sobre `core/builder.py` y `tests/test_builder.py`: correcto.
- Prueba directa del método `_post_base()` con LightDM desactivado: conserva el
  hash y genera la caducidad esperada.
- Prueba directa del método `_post_base()` con LightDM activado: conserva el
  hash y no genera la caducidad.
- Se añadió una prueba de regresión en `tests/test_builder.py` para el caso
  LightDM.
- La ejecución de pytest no pudo completar la recolección en este entorno
  porque no está instalada la dependencia `PySide6`.

## Pendiente de validación

La corrección de generación del Kickstart está comprobada a nivel de código,
pero todavía debe validarse en una ISO arrancada: contraseña correcta,
contraseña incorrecta y acceso efectivo a la sesión Kiosco.
