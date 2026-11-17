# Corrección del verificador RPM en Fedora en español

## Causa
El verificador anterior buscaba exclusivamente la cadena inglesa `digests OK`.
En Fedora configurado en español, `rpmkeys --checksig --verbose` devuelve líneas
como `Header SHA256 resumen: OK` y `Payload SHA256 resumen: OK`. La detección
anterior clasificaba erróneamente estos paquetes como si sus digests no fueran
verificables.

## Cambio
- Reconoce la salida inglesa habitual y la salida localizada en español.
- Clasifica como RPM sin firma los paquetes con digests correctos y sin
  indicadores de firma.
- Mantiene el rechazo de digests incorrectos/no verificables.
- Mantiene la política de no aceptar automáticamente firmas inválidas o claves
  desconocidas.
- Añade pruebas de regresión para la salida española y un digest defectuoso.

## Pruebas
`python -m pytest -q tests/test_security.py`: 10 pruebas aprobadas.
`python -m pytest -q`: suite completa aprobada en este entorno.

La instalación real en Fedora debe verificarse en el equipo destino. Para este
RPM sin firma, la opción «Permitir RPM sin firma» debe estar activada; no se
debe activar ningún bypass de integridad.
