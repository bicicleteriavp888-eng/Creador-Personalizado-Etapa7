# Política de RPM locales sin firma

La opción está disponible en **Selección de software → modo Avanzado**. Está desactivada por defecto. Al activarla, Creador-kiosk muestra una advertencia y exige confirmar que el usuario asume la responsabilidad.

La excepción se limita a paquetes que `rpmkeys --checksig --verbose` clasifique como realmente sin firma y cuyos digests indiquen `OK`. Una firma presente pero inválida, una clave desconocida (`NOKEY`/`NOTTRUSTED`) o un digest incorrecto siguen siendo bloqueantes. La opción no altera la política de paquetes prohibidos.

La preferencia se incluye en la configuración de compilación y, por tanto, en el registro de historial. No se guarda ninguna contraseña ni secreto.

**Riesgo:** un RPM sin firma no aporta autenticidad del editor. La comprobación de digests detecta corrupción respecto de los metadatos internos, pero no demuestra quién creó el paquete ni que sea benigno. Úsese solo con artefactos propios o de origen plenamente confiable.
