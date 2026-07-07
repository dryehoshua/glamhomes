# Handoff para nuevo agente

## Objetivo del proyecto

Construir un concierge/call center de voz para Glam Homes, enfocado en booking,
pre-booking, soporte al huesped y clasificacion comercial. El stack planeado es:

- OpenAI Realtime para voz instantanea.
- Twilio para llamadas y SMS.
- Guesty como fuente de verdad para reservas, propiedades, disponibilidad y
  calendario.

## Estado funcional final

La app local `GLAM HOMES CONCIERGE` ya corre en:

```text
http://127.0.0.1:3000
```

El frontend usa identidad Glam Homes, tonos dorados, avatar ejecutivo,
dashboard operativo y voz `ash` por defecto. Tambien existe opcion Vapi
`vapi:riley` si se configuran credenciales. El idioma por defecto del producto
es ingles; cambia a espanol solo si el cliente lo pide o inicia claramente en
espanol.

Guesty esta conectado por OAuth en la maquina local. Las credenciales viven en
`.env` y el token vive en `.cache/guesty_token.json`; ambos estan fuera de Git
por `.gitignore`.

El agente carga al iniciar la knowledge base conversacional privada de Guesty:

```text
data/private/guesty-conversations/GLAM HOMES KNOWLEDGE BASE/agent_runtime_best_practices.md
```

Esto es entrenamiento operativo por runtime prompt, no fine-tuning del modelo.
Guesty sigue siendo la fuente de verdad para datos actuales.

## Guesty disponible hoy

Modo actual: solo lectura.

Capacidades probadas:

- Autenticacion OAuth `client_credentials`.
- Listar listings internos: 157 registros.
- Consultar disponibilidad por fechas y huespedes.
- Consultar calendario minificado por listing.
- Buscar reservas.
- Consultar reserva por ID o codigo.
- Consultar detalles confirmados de estancia, incluyendo listing, direccion,
  instrucciones, custom fields, access/check-in, Wi-Fi/StayFi cuando existen en
  Guesty.
- Consultar guests, conversations, webhooks y tasks segun permisos disponibles.
- Enviar SMS de links publicos.
- Enviar SMS de handoff humano.
- Transferir llamada Twilio a soporte humano.
- Agrupar transcripts y analytics por numero telefonico en el dashboard.

Capacidades documentadas pero NO habilitadas aun:

- Crear bookings/reservas.
- Modificar reservas.
- Cancelar reservas.
- Cobros, pagos, links de pago o deposits.
- Mensajes outbound automatizados calendarizados.

Regla: cualquier escritura o pago requiere aprobacion humana explicita y logging
antes de activarse.

## Links publicos de propiedades

La API interna de Guesty tiene mas listings que el booking site publico. El
export publico actual muestra 54 propiedades activas. Para SMS/chat se deben
usar solo esas propiedades publicas activas.

Exports actuales:

- `data/guesty-property-links.csv`
- `data/guesty-property-links.json`
- `data/guesty-property-links.md`
- `data/glam_homes_property_links.sqlite`

Herramientas Realtime activas:

- `glam_search_public_property_links`: busca links activos; por defecto devuelve
  link directo de Glam Homes, y puede devolver Airbnb/Booking/VRBO si se pide.
- `twilio_send_property_link_sms`: envia un link activo por SMS con Twilio. En
  llamadas reales usa el numero caller si el modelo no manda `phone_number`.
- `twilio_send_stay_details_sms`: envia por SMS detalles confirmados de estancia
  cuando la reserva fue validada y Guesty tiene datos.
- `twilio_send_human_handoff_sms`: notifica al contacto humano de soporte.
- `twilio_transfer_call_to_human`: transfiere llamadas Twilio a soporte humano.

Los links directos de Glam Homes pueden precargarse con fechas usando
`checkIn`, `checkOut` y `minOccupancy`.

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

1. Exportar/copiar la carpeta completa usando
   `documentacion/15-cierre-exportacion-github.md`.
2. Mantener GitHub limpio sin `.env`, `API Keys/`, `data/private/`,
   `transcripts/` ni `logs/`.
3. En el nuevo entorno, recrear `.env` desde `.env.example`.
4. Confirmar `curl http://127.0.0.1:3000/api/status` y revisar que
   `knowledge_base_loaded` sea `true`.
5. Si se activa produccion real, definir login formal del dashboard y politicas
   para escrituras/pagos Guesty antes de habilitarlas.
