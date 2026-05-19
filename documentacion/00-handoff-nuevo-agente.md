# Handoff para nuevo agente

## Objetivo del proyecto

Construir un concierge/call center de voz para Glam Homes, enfocado en booking,
pre-booking, soporte al huesped y clasificacion comercial. El stack planeado es:

- OpenAI Realtime para voz instantanea.
- Twilio para llamadas y SMS.
- Guesty como fuente de verdad para reservas, propiedades, disponibilidad y
  calendario.

## Estado funcional

La app local `GLAM HOMES CONCIERGE` ya corre en:

```text
http://127.0.0.1:3000
```

El frontend usa identidad Glam Homes, tonos dorados, avatar ejecutivo y voz
masculina `ash`.

Guesty esta conectado por OAuth en la maquina local. Las credenciales viven en
`.env` y el token vive en `.cache/guesty_token.json`; ambos estan fuera de Git
por `.gitignore`.

## Guesty disponible hoy

Modo actual: solo lectura.

Capacidades probadas:

- Autenticacion OAuth `client_credentials`.
- Listar listings internos: 157 registros.
- Consultar disponibilidad por fechas y huespedes.
- Consultar calendario minificado por listing.
- Buscar reservas.
- Consultar reserva por ID o codigo.
- Consultar guests, conversations, webhooks y tasks segun permisos disponibles.

Capacidades documentadas pero NO habilitadas aun:

- Crear bookings/reservas.
- Modificar reservas.
- Cancelar reservas.
- Cobros, pagos, links de pago o deposits.
- Enviar mensajes/SMS por automatizacion.

Regla: cualquier escritura o pago requiere aprobacion humana explicita y logging
antes de activarse.

## Links publicos de propiedades

La API interna de Guesty tiene 157 listings, pero el booking site publico muestra
55 propiedades. Para SMS/chat se deben usar las 55 publicas.

Exports actuales:

- `data/guesty-property-links.csv`
- `data/guesty-property-links.json`
- `data/guesty-property-links.md`

Actualizar:

```bash
python3 apps/voice-agent/export_property_links.py
```

## Comandos importantes

Arrancar app:

```bash
python3 apps/voice-agent/server.py
```

Revisar estado local:

```bash
curl http://127.0.0.1:3000/api/status
curl "http://127.0.0.1:3000/api/guesty/status?live=1"
```

Probar Guesty CLI:

```bash
python3 apps/voice-agent/guesty_client.py auth-check
python3 apps/voice-agent/guesty_client.py listings --limit 5
python3 apps/voice-agent/guesty_client.py reservations --limit 5
```

## Siguiente etapa recomendada

1. Conectar Twilio al backend local con Cloudflare Tunnel o URL publica temporal.
2. Activar inbound voice con el numero `+17864813013`.
3. Agregar SMS saliente controlado para enviar links de propiedades.
4. Crear tabla/log local de llamadas, clasificacion de buyer persona y handoff.
5. Definir aprobaciones antes de habilitar cualquier escritura en Guesty.
