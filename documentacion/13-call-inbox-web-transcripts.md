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

Clave actual local: `MosesGlam`.

## Endpoints

- `GET /api/calls/inbox?limit=50`
  - Acepta busqueda con `q=...`.
  - Local: permitido.
  - Publico: requiere header `X-Glam-Dashboard-Key`.
  - Devuelve llamadas recientes por `CallSid`, numero origen/destino, hora,
    estado, duracion, preview, si existe transcript, KPIs y conceptos
    frecuentes.

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

## Frontend actual

El dashboard quedo separado en dos pestañas principales:

- `Voice Console`: operacion del concierge, monitor Twilio, prueba de voz y chat
  local.
- `Calls & Analytics`: inbox de llamadas, busqueda, KPIs y graficas.

La pestaña `Calls & Analytics` usa una distribucion de dos columnas en desktop:
analitica a la izquierda y transcripts a la derecha. En mobile, cada zona tiene
scroll propio para evitar que el inbox o el transcript deformen toda la pagina.

El inbox ahora se agrupa por numero de telefono, como una conversacion continua
tipo messenger/WhatsApp. Si un cliente llamo ayer y vuelve a llamar hoy, no se
crea una tarjeta nueva para cada `CallSid`; se abre el mismo hilo del numero.

Cada item del inbox muestra solo:

- Nombre detectado o `Unknown`.
- Numero de telefono.
- Ultima hora en que hablo el cliente; si no hay turno del cliente, ultima
  actividad registrada.

Filtros disponibles:

- `Recent`: ultimas conversaciones.
- `Most interaction`: clientes con mas llamadas/mensajes.
- `Least interaction`: clientes con menor interaccion.

Endpoints de hilos:

- `GET /api/calls/threads?limit=50&sort=recent|most|least&q=...`
- `GET /api/calls/thread?thread_id=phone:<digits>`

Graficas incluidas:

- Barra: volumen por temas detectados.
- Dona: mezcla de prospectos, soporte, handoffs y otros.

El modulo de graficas esta vendorizado localmente en:

`apps/voice-agent/public/vendor/chart.umd.min.js`

Esto evita depender de un CDN en cada carga del dashboard.

## Verificacion realizada

- Local Conversation Inbox: OK, 5 hilos por numero visibles.
- Hilo local principal: OK, `+525630907754` agrupado con 22 llamadas y 273
  eventos visibles en un solo historial continuo.
- Publico sin llave: OK, responde 403 protegido.
- Publico con llave: OK, devuelve llamada con transcript.
- Busqueda: filtra por numero, CallSid o palabras dentro del transcript.
- KPIs: calcula llamadas, prospectos, cobertura de transcript, handoffs,
  llamadores unicos, herramientas usadas y conceptos frecuentes.
- Frontend desktop: OK, pestañas navegables, charts renderizados y sin errores
  de consola.
- Frontend mobile: OK, sin overflow horizontal, listado y transcript con scroll
  propio.
- Public health: OK, voice service y SMS service activos en
  `https://glamhomes.aipeople.app/api/twilio/public-health`.

## Notas de seguridad

No se exponen transcripts publicamente sin llave. El endpoint ya no devuelve
rutas locales de archivos del Mac.

## Login AI People

La llave `MosesGlam` es una proteccion interina para demos y operacion interna.
Para una plataforma madura con `aipeople.app`, hay tres caminos:

1. Login visual/fake: solo redirecciona a una pantalla. Sirve para demo, pero no
   protege datos.
2. Cookie de sesion compartida: `aipeople.app` crea una sesion firmada y
   `glamhomes.aipeople.app` valida esa cookie en backend. Es el camino mas
   simple si ambos viven bajo el mismo dominio padre.
3. JWT/OAuth interno: `aipeople.app` emite un token firmado con expiracion y
   roles. GLAM valida firma, expiracion y permisos antes de entregar transcripts.
   Es el camino recomendado para produccion.

Hasta que el login de AI People tenga token o cookie firmada real, el dashboard
mantiene `GLAM_DASHBOARD_KEY` como barrera de acceso.
