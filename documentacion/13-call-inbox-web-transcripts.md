# Call Inbox Web Transcripts

Fecha: 2026-06-09

## Objetivo

El dashboard web de GLAM HOMES debe mostrar las llamadas recientes y el
transcript literal de cada llamada en formato messenger.

## Acceso

- En local: `http://127.0.0.1:3000/`
- En publico: `https://glamhomes.aipeople.app/`

En local, el Call Inbox carga directo. En publico, el frontend pide la
`Dashboard key` para proteger telefonos, CallSid y conversaciones.

La llave vive en `.env` como:

`GLAM_DASHBOARD_KEY=...`

Tambien se dejo una copia local privada en:

`data/private/dashboard-access.txt`

Ese directorio esta ignorado por Git.

## Endpoints

- `GET /api/calls/inbox?limit=50`
  - Local: permitido.
  - Publico: requiere header `X-Glam-Dashboard-Key`.
  - Devuelve llamadas recientes por `CallSid`, numero origen/destino, hora,
    estado, duracion, preview y si existe transcript.

- `GET /api/calls/transcript?call_sid=...`
  - Local: permitido.
  - Publico: requiere header `X-Glam-Dashboard-Key`.
  - Devuelve eventos normalizados con roles:
    - `guest`
    - `concierge`
    - `system`
    - `tool`

## Fuente de datos

Los transcripts salen de:

`transcripts/YYYY-MM-DD/*.jsonl`

El frontend muestra el texto literal de cada evento guardado. No usa Twilio
Recording ni Twilio Transcription en esta version.

## Verificacion realizada

- Local Call Inbox: OK, 35 llamadas visibles.
- Transcript local: OK, primera llamada con 47 eventos.
- Publico sin llave: OK, responde 403 protegido.
- Publico con llave: OK, devuelve llamada con transcript.

## Notas de seguridad

No se exponen transcripts publicamente sin llave. El endpoint ya no devuelve
rutas locales de archivos del Mac.
