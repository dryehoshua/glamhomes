# Arquitectura tecnica inicial

## Objetivo de la primera prueba

Conectar el numero Twilio `+17864813013` a un agente telefonico que pueda:

- Contestar llamadas de prueba.
- Saludar como Glam Homes.
- Entender si la llamada es booking, reserva existente o soporte.
- Guardar transcript y resumen.
- Escalar casos fuera de alcance.
- Consultar Guesty en modo solo lectura cuando tengamos credenciales.

## Componentes propuestos

```text
Twilio Phone Number
  -> Twilio Voice Webhook /twilio/voice
  -> TwiML Connect Stream
  -> WebSocket /twilio/media
  -> OpenAI Realtime Agent
  -> Backend Tools
      -> Guesty Adapter
      -> Knowledge Base
      -> Call Log / CRM local
      -> Escalation Alerts
```

## Servicios del backend

### HTTP

- `GET /health`
- `GET /twilio/health`
- `POST /twilio/voice`
- `GET /twilio/voice`
- `POST /twilio/status`
- `POST /twilio/sms`

### WebSocket

- `GET /twilio/media`

## Variables de entorno

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_API_KEY`
- `TWILIO_API_SECRET`
- `TWILIO_PHONE_NUMBER`
- `OPENAI_API_KEY`
- `PUBLIC_BASE_URL`
- `GUESTY_API_BASE_URL`
- `GUESTY_CLIENT_ID`
- `GUESTY_CLIENT_SECRET`
- `GUESTY_API_KEY`

## Modo seguro inicial

El agente puede:

- Saludar y clasificar la llamada.
- Pedir nombre, telefono, correo y codigo de reserva si aplica.
- Responder FAQs aprobadas.
- Consultar datos de reserva si Guesty esta disponible.
- Guardar resumen de llamada.
- Marcar casos para seguimiento humano.

El agente no puede todavia:

- Modificar reservas.
- Confirmar descuentos.
- Procesar pagos.
- Reembolsar.
- Cancelar.
- Dar codigos de acceso sin validacion.
- Hacer promesas fuera de politicas.

## Primer prompt operativo

El agente debe comportarse como recepcion y soporte de Glam Homes:

- Tono calido, claro, premium y eficiente.
- Puede hablar español e ingles si el cliente lo requiere.
- Debe identificar el motivo antes de responder detalles.
- Debe validar identidad antes de compartir informacion de reserva.
- Debe escalar casos sensibles o no autorizados.
- Debe evitar sonar como IVR.

## Integracion Guesty

Primera etapa recomendada: solo lectura.

Consultas necesarias:

- Buscar reserva por codigo, telefono, correo o nombre.
- Obtener estado de reserva.
- Obtener propiedad asociada.
- Obtener fechas de llegada y salida.
- Obtener instrucciones generales permitidas.
- Obtener estado de pago o deposito solo si la politica lo permite.

Segunda etapa: acciones controladas con confirmacion humana.

- Crear tarea interna.
- Agregar nota a reserva.
- Enviar mensaje al huesped.
- Solicitar cambio de reserva.

Tercera etapa: acciones automaticas por reglas aprobadas.

- Recordatorios pre-check-in.
- Seguimiento post-check-out.
- Confirmaciones de datos faltantes.

## Evidencia por llamada

Cada llamada debe guardar:

- CallSid de Twilio.
- Numero origen.
- Numero destino.
- Fecha y hora.
- Transcript.
- Resumen.
- Intencion.
- Reserva asociada, si existe.
- Resultado.
- Si requiere seguimiento humano.
- Nivel de riesgo.

## Siguiente implementacion

1. Crear backend base en `apps/voice-agent`.
2. Adaptar el bridge Twilio Realtime de Kim Live.
3. Crear almacenamiento local de llamadas.
4. Exponer endpoints Twilio.
5. Probar con tunel publico.
6. Conectar Twilio `+17864813013`.
7. Agregar Guesty cuando tengamos credenciales y documentacion.
