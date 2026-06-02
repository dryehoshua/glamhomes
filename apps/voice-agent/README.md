# GLAM HOMES Voice Agent

Backend inicial para el agente telefonico de Glam Homes.

## Frontend local

```bash
cd "/Users/dryehoshuapython/Desktop/GLAM HOMES"
python3 apps/voice-agent/server.py
```

URL local:

```text
http://127.0.0.1:3000
```

La interfaz `GLAM HOMES CONCIERGE` usa WebRTC con OpenAI Realtime y deja `Ash`
como voz masculina por defecto. El idioma de producto es ingles por default.
Para activar voz real, define `OPENAI_API_KEY` en `.env` o usa el API key
guardado en Keychain por Codex/Kim Live.

El agente de voz ya tiene herramientas Guesty de solo lectura:

- `guesty_status`
- `guesty_search_reservation`
- `guesty_get_reservation`
- `guesty_list_listings`
- `guesty_available_listings`
- `guesty_listing_calendar`
- `glam_search_public_property_links`
- `twilio_send_property_link_sms`

Mientras falten credenciales, el agente respondera que Guesty no esta configurado. Cuando existan `GUESTY_CLIENT_ID` y `GUESTY_CLIENT_SECRET`, las mismas herramientas empezaran a consultar Open API.

## Twilio Media Streams

Para llamadas reales se levantan dos procesos:

```bash
python3 apps/voice-agent/server.py
apps/voice-agent/run_twilio_bridge.sh
apps/voice-agent/run_public_proxy.sh
```

Para mantener todo el stack de Glam vivo en una sola supervision local:

```bash
apps/voice-agent/run_glam_stack.sh
```

Ese supervisor revisa periodicamente el backend `3000`, el media bridge `8877`,
el proxy publico `8890` y el tunnel Cloudflare de Glam. Si alguno se cae, lo
vuelve a levantar sin tocar procesos de Kim Live.

El endpoint TwiML queda en `/twilio/voice` y el WebSocket del audio queda en
`/twilio/media` por medio del tunel Cloudflare `glamhomes.aipeople.app`.
El proxy publico local escucha en `127.0.0.1:8890` y enruta HTTP al frontend/API
en `3000`, mientras que `/twilio/media` se envia al bridge de Twilio en `8877`.

Si el tunel tokenizado existe en `~/.cloudflared/glam-homes-token`, arranca el
tunel contra ese proxy:

```bash
apps/voice-agent/run_cloudflare_tunnel.sh
```

Antes de aplicar webhooks:

```bash
python3 apps/voice-agent/configure_twilio_number.py
```

Cuando el tunel responda:

```bash
python3 apps/voice-agent/configure_twilio_number.py --apply
```

No tocar numeros de Kim Live; el script bloquea numeros terminados en `7532`.

Las transcripciones se guardan en `transcripts/YYYY-MM-DD/`.

## Endpoints Guesty locales

```text
GET /api/guesty/status?live=1
GET /api/guesty/listings?limit=5
GET /api/guesty/available-listings?check_in=2026-08-01&check_out=2026-08-04&guests=2
GET /api/guesty/listing-calendar?listing_id=<listing_id>&start_date=2026-08-01&end_date=2026-08-15
GET /api/guesty/reservations?limit=5
GET /api/guesty/reservation-by-code?code=GY-XXXX
GET /api/guesty/reservation?id=<reservation_id>
POST /api/guesty/tool
GET /api/properties/search?query=Amazing&platform=direct&check_in=2026-06-10&check_out=2026-06-14&guests=4
```

## Guesty CLI de prueba

Este cliente usa Guesty Open API con OAuth `client_credentials`.

Antes de probar, crea un archivo `.env` en la raiz del proyecto con:

```text
GUESTY_CLIENT_ID=
GUESTY_CLIENT_SECRET=
GUESTY_API_BASE_URL=https://open-api.guesty.com/v1
GUESTY_TOKEN_URL=https://open-api.guesty.com/oauth2/token
```

Forma recomendada:

```bash
python3 apps/voice-agent/setup_guesty_env.py
```

No uses ni pegues la contrasena de tu cuenta Guesty/Gmail. Este proyecto necesita las credenciales OAuth de la app: `Client ID` y `Client Secret`.

Comandos:

```bash
python3 apps/voice-agent/guesty_client.py auth-check
python3 apps/voice-agent/guesty_client.py listings --limit 5
python3 apps/voice-agent/guesty_client.py available-listings --check-in 2026-08-01 --check-out 2026-08-04 --guests 2 --limit 5
python3 apps/voice-agent/guesty_client.py calendar-minified LISTING_ID --start-date 2026-08-01 --end-date 2026-08-15
python3 apps/voice-agent/guesty_client.py reservations --limit 5
python3 apps/voice-agent/guesty_client.py reservation-by-code GY-XXXX
python3 apps/voice-agent/guesty_client.py reservation RESERVATION_ID
```

El token se cachea en `.cache/guesty_token.json` para no pedir tokens innecesarios.

## Links publicos del booking site

Para refrescar el mapa de propiedades compartibles por SMS/chat:

```bash
python3 apps/voice-agent/export_property_links.py
```

Genera:

- `data/guesty-property-links.json`
- `data/guesty-property-links.csv`
- `data/guesty-property-links.md`
- `data/glam_homes_property_links.sqlite`

Por defecto el concierge comparte links directos de Glam Homes. Si el cliente
pide Airbnb, Booking o VRBO, el bridge devuelve ese link si existe para la
propiedad activa. Los links directos de Glam Homes aceptan prefill con
`checkIn`, `checkOut` y `minOccupancy`.
