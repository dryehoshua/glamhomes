# Checklist del siguiente paso

## Necesario para conectar Twilio

- Confirmar que `+17864813013` tiene capacidad de Voice.
- Account SID.
- Auth Token o API Key/Secret.
- Confirmar si usaremos credenciales en `.env` local o macOS Keychain.
- URL publica para webhooks durante pruebas.
- Numero personal autorizado para recibir/hacer llamadas de prueba.
- Confirmar si grabaremos llamadas o solo guardaremos transcript.

## Necesario para Guesty

- Acceso a Guesty API o sandbox.
- Tipo de autenticacion.
- Permisos disponibles.
- Documentacion/API reference.
- Ejemplos de reservas de prueba.
- Lista de propiedades y reglas basicas.

## Necesario para el agente

- Nombre del agente.
- Idiomas iniciales.
- Guion de bienvenida.
- Politicas de cancelacion.
- Reglas de escalacion.
- Telefonos o correos internos para seguimiento.
- FAQ actual.
- Instrucciones de check-in/check-out.

## Archivos utiles para adjuntar

- Export de FAQ.
- Politicas de Glam Homes.
- Manual operativo.
- Scripts actuales de call center.
- Ejemplos de conversaciones reales anonimizadas.
- Ejemplos de reservas o capturas de Guesty.
- Lista de propiedades con reglas por propiedad.

## Decision recomendada para empezar

Arrancar con una prueba de llamadas entrantes en modo recepcion:

1. El cliente llama.
2. El agente identifica el motivo.
3. Si hay reserva, pide datos de validacion.
4. Si aun no hay Guesty conectado, toma recado y crea resumen.
5. Si Guesty ya esta conectado, consulta reserva en solo lectura.
6. Todo cambio o caso sensible se escala.
