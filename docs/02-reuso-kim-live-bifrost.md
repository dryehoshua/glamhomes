# Reuso de Kim Live / BIFROST

## Fuentes revisadas

- `/Users/dryehoshuapython/Documents/BIFROST/kimtools/voice/kim_live/server.py`
- `/Users/dryehoshuapython/Documents/BIFROST/kimtools/voice/kim_live/twilio_realtime_bridge.py`
- `/Users/dryehoshuapython/Documents/BIFROST/kimtools/voice/kim_live/API_BRIDGE.md`
- `/Users/dryehoshuapython/Documents/BIFROST/docs/kim_live_inbound_privacy_spec.md`
- `/Users/dryehoshuapython/Documents/BIFROST/docs/kim_0053_twilio_crm_call_actions.md`

## Piezas reutilizables

### 1. Twilio Media Streams con OpenAI Realtime

Kim Live ya tiene un bridge funcional:

- Recibe audio de Twilio por WebSocket.
- Lo reenvia a OpenAI Realtime en formato `audio/pcmu`.
- Devuelve audio del agente a Twilio.
- Maneja interrupciones cuando el usuario empieza a hablar.
- Guarda transcripcion y metadatos de llamada.

Archivo base:

```text
/Users/dryehoshuapython/Documents/BIFROST/kimtools/voice/kim_live/twilio_realtime_bridge.py
```

Para Glam Homes conviene reutilizar esta arquitectura, pero cambiando:

- Instrucciones del agente.
- Nombre, tono y politicas.
- Memoria BIFROST por una memoria/CRM de Glam Homes.
- Herramientas internas por herramientas de Guesty.
- Etiquetas de transcript para `Guest` / `Agent` en lugar de asumir que habla el doctor.

### 2. Endpoints Twilio

Kim Live ya contiene endpoints utiles:

- `/twilio/voice`: responde TwiML y abre Media Stream.
- `/twilio/status`: recibe callbacks de estado.
- `/twilio/sms`: registra SMS entrantes.
- `/twilio/health`: healthcheck simple.

Para Glam Homes se recomienda mantener los mismos nombres o equivalentes:

- `/twilio/voice`
- `/twilio/status`
- `/twilio/sms`
- `/twilio/health`
- `/twilio/media`

### 3. Acciones Twilio con confirmacion

Kim Live implementa:

- `status`
- `list_numbers`
- `send_sms`
- `send_whatsapp`
- `call_phone`
- `schedule_call`
- `schedule_sms`

Tambien usa una regla importante: acciones externas hacia terceros se preparan primero y luego requieren confirmacion.

Para Glam Homes:

- Llamadas de prueba: pueden ser manuales y confirmadas.
- Llamadas automatizadas a huespedes: deben pasar por reglas de etapa de reserva.
- SMS/WhatsApp: deben tener consentimiento, plantillas y controles de envio.

### 4. CRM local y registro de interacciones

Kim Live tiene un CRM local con:

- contactos
- empresas
- interacciones
- acciones programadas
- transcripts de llamadas

Para Glam Homes puede servir como patron, pero el dominio cambia:

- Huespedes
- Reservas
- Propiedades
- Etapas de reserva
- Tickets o incidencias
- Escalaciones internas

La fuente de verdad deberia ser Guesty, no el CRM local. El CRM local del proyecto puede guardar historiales y auditoria, pero no reemplazar Guesty.

### 5. Politica de privacidad para llamadas entrantes

Kim Live ya aprendio una regla clave: una llamada entrante no siempre viene de una persona conocida y no debe filtrar contexto privado.

Para Glam Homes esto se traduce en:

- Identificar al huesped antes de revelar informacion de reserva.
- No compartir datos de otros huespedes.
- No confirmar codigos de acceso, pagos o datos sensibles sin validacion.
- Escalar emergencias, reembolsos, conflictos y casos legales.
- Registrar llamadas ambiguas para revision humana.

## Recomendacion tecnica inicial

Construir un proyecto nuevo, no copiar BIFROST completo.

Se puede migrar el patron en capas:

1. Backend pequeño con endpoints Twilio.
2. Bridge Realtime separado.
3. Registro local de llamadas.
4. Adaptador Guesty de solo lectura.
5. Herramientas del agente con permisos.
6. Confirmaciones para cualquier accion que modifique reservas o contacte a terceros.

## Riesgos al copiar directamente

- BIFROST contiene rutas absolutas y memoria personal del proyecto Kim.
- Hay supuestos de identidad del doctor que no aplican a huespedes.
- Hay integraciones que no pertenecen a Glam Homes.
- El tono, permisos y politicas deben rediseñarse.

Por eso la mejor ruta es reutilizar estructura y patrones, no clonar el sistema completo.
