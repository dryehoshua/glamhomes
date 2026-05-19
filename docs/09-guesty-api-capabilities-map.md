# Guesty API capabilities map para GLAM HOMES CONCIERGE

Fecha de revision: 2026-05-19

Este mapa separa capacidades probadas con las credenciales actuales, capacidades
documentadas por Guesty pero no activadas por seguridad, y decisiones necesarias
antes de permitir que el concierge opere reservas reales.

## Estado de credenciales

Guesty Open API OAuth quedo configurado localmente.

Archivo local:

```text
.env
```

Permisos:

```text
-rw-------
```

Token cacheado:

```text
.cache/guesty_token.json
```

No imprimir ni compartir `GUESTY_CLIENT_SECRET`.

## Pruebas reales no destructivas

Todas estas pruebas se hicieron sin imprimir datos privados de huespedes ni
valores completos de reservas.

| Capacidad | Endpoint probado | Resultado |
| --- | --- | --- |
| Autenticacion OAuth | `POST /oauth2/token` | OK, token emitido y cacheado |
| Listar propiedades | `GET /listings` | OK, 157 listings visibles |
| Buscar disponibilidad | `GET /listings?available=...` | OK, 44 disponibles para fechas de prueba |
| Calendario/precio nocturno | `GET /availability-pricing/api/calendar/listings/minified/{listingId}` | OK, devuelve dias, precio, minimo de noches y bloqueos |
| Buscar reservas | `GET /reservations` | OK, 684 reservas visibles |
| Buscar guests | `GET /guests-crud` | OK, guest records visibles |
| Webhooks configurados | `GET /webhooks` | OK, 12 webhooks existentes visibles |
| Conversaciones | `GET /communication/conversations` | OK, endpoint accesible |
| Saved replies | `GET /saved-replies` | OK, endpoint accesible; sin replies en muestra |
| Tareas | `GET /tasks-open-api/tasks` | OK con `limit >= 25` |
| Vendors/accounting | `GET /vendors` | 403, accounting feature disabled |
| Quotes list | `GET /quotes` | 404; quotes se crean/leen por flujo especifico, no como listado general |
| Reservations V3 read | `GET /reservations-v3` | Requiere `reservationIds`; no es listado general |

## Capacidades inmediatas del concierge

### Pre-booking / booking calls

Ya podemos preparar el agente para:

- Preguntar fechas, salida, numero de huespedes, ciudad/zona, presupuesto y
  motivo.
- Consultar propiedades disponibles por fechas y ocupacion.
- Recomendar 1 a 3 propiedades reales.
- Consultar calendario minificado de una propiedad para noches, restricciones,
  precio nocturno y minimo de noches.
- Decir si hay disponibilidad general sin inventar.
- Capturar telefono/correo para seguimiento.
- Enviar link por SMS via Twilio cuando definamos la fuente del booking link.

Importante: el precio nocturno de calendario no necesariamente equivale al total
final con taxes, fees, descuentos, depositos o contrato. Para total final hay
que usar quote flow.

### Post-booking

Ya podemos preparar el agente para:

- Buscar reserva por confirmation code.
- Buscar por nombre, email o telefono con validacion.
- Consultar estado, fechas, propiedad, source, check-in/check-out y datos
  basicos permitidos.
- Validar identidad antes de revelar datos.
- Escalar si el huesped pide cambio, cancelacion, reembolso, early check-in,
  late checkout o codigo de acceso.

### In-stay / soporte

Ya podemos preparar el agente para:

- Identificar reserva y propiedad.
- Consultar tareas existentes si se define el flujo de maintenance.
- Escalar mantenimiento critico.
- Crear resumen operativo para el equipo.

Pendiente: confirmar si crearemos o actualizaremos tareas desde API. Aunque el
endpoint de tareas responde, no active operaciones de escritura.

### Webhooks

Guesty documenta webhooks para:

- Reservas: `reservation.new`, `reservation.updated`.
- Mensajes: `reservation.messageReceived`, `reservation.messageSent`.
- Pagos: `payments.received`, `payments.failed`, `payments.refunded`, etc.
- Listings: `listing.new`, `listing.updated`, `listing.removed`.
- Calendario: `listing.calendar.updated`, `calendar.updated.v2`.
- Tasks: `task.created`, `task.updated`, `task.deleted`.
- Guests: `guest.created`, `guest.updated`, `guest.deleted`.

Esto sirve para que el concierge no dependa solo de consultas manuales:

- Actualizar cache local cuando cambia disponibilidad.
- Detectar nuevas reservas.
- Activar llamadas por etapa.
- Sincronizar tareas/maintenance.
- Enviar alertas internas.

Pendiente: exponer URL publica con Cloudflare y crear webhooks apuntando al
backend local/produccion.

## Capacidades documentadas pero no activadas

### Quotes

Guesty documenta `POST /v1/quotes` y `GET /v1/quotes/{quoteId}` para crear una
cotizacion y recuperar el quote.

Uso recomendado:

1. Cliente da fechas, propiedad y huespedes.
2. El agente consulta disponibilidad.
3. El backend crea quote con `ignoreCalendar=false`, `ignoreTerms=false` e
   `ignoreBlocks=false`.
4. El cliente acepta.
5. El equipo humano o el flujo de checkout termina la reserva.

No active esto todavia porque crea objetos reales de quote en Guesty.

### Inquiries / instant bookings

Guesty Booking Engine API y Reservations V3 soportan flujos para crear inquiries
o reservas directas. Esto debe ir despues de:

- Reglas de pago.
- Contrato.
- Taxes/fees/depositos.
- Politica de cancelacion.
- Validacion de edad, ocupacion, eventos y mascotas.
- Confirmacion de si Glam Homes prefiere `inquiry` o `instant booking`.

### Pagos y reembolsos

Guesty documenta flujos de pagos, scheduled payments, refunds y payment
webhooks. Para el concierge, esto debe estar bloqueado hasta aprobacion expresa.

### Cambios/cancelaciones

Guesty documenta alteraciones: extender/acortar, relocations y cancelaciones.
Para el concierge, esto debe ser solo captura + escalacion humana al inicio.

## Recomendacion de fases

### Fase 1 - segura ahora

- Read-only Guesty.
- Disponibilidad.
- Calendario minificado.
- Lookup de reservas.
- Buyer persona + resumen de llamada.
- SMS con link de booking.

### Fase 2 - ventas asistidas

- Crear quote, no reserva.
- Enviar quote/link al cliente.
- Alertar a humano para cierre.
- Guardar quote ID y decision.

### Fase 3 - reservas controladas

- Crear inquiry o reserva segun reglas.
- Confirmacion humana requerida antes del primer booking real.
- Logs completos.
- Limites por monto, fecha y propiedad.

### Fase 4 - operaciones avanzadas

- Webhooks en produccion.
- Tareas de maintenance.
- Reglas de escalacion por urgency.
- Analytics por buyer persona, etapa y conversion.

## Implementacion local actual

Herramientas Realtime disponibles:

- `guesty_status`
- `guesty_search_reservation`
- `guesty_get_reservation`
- `guesty_list_listings`
- `guesty_available_listings`
- `guesty_listing_calendar`

Endpoints locales:

```text
GET /api/guesty/status?live=1
GET /api/guesty/listings?limit=5
GET /api/guesty/available-listings?check_in=2026-08-01&check_out=2026-08-04&guests=2
GET /api/guesty/listing-calendar?listing_id=<listing_id>&start_date=2026-08-01&end_date=2026-08-15
GET /api/guesty/reservations?limit=5
GET /api/guesty/reservation-by-code?code=GY-XXXX
GET /api/guesty/reservation?id=<reservation_id>
POST /api/guesty/tool
```

CLI:

```bash
python3 apps/voice-agent/guesty_client.py auth-check
python3 apps/voice-agent/guesty_client.py listings --limit 5
python3 apps/voice-agent/guesty_client.py available-listings --check-in 2026-08-01 --check-out 2026-08-04 --guests 2 --limit 5
python3 apps/voice-agent/guesty_client.py calendar-minified LISTING_ID --start-date 2026-08-01 --end-date 2026-08-15
python3 apps/voice-agent/guesty_client.py reservations --limit 5
```

## Fuentes oficiales

- Guesty Open API authentication:
  `https://open-api-docs.guesty.com/docs/authentication`
- Searching for available listings:
  `https://open-api-docs.guesty.com/docs/searching-for-available-listings-and-all-listings`
- Reservation search:
  `https://open-api-docs.guesty.com/docs/how-to-search-for-reservations`
- Reservations V3 booking flow:
  `https://open-api-docs.guesty.com/docs/reservations-v3-booking-flow`
- Booking Engine reservation quote flow:
  `https://booking-api-docs.guesty.com/docs/new-reservation-creation-flow`
- Webhooks overview:
  `https://open-api-docs.guesty.com/docs/webhooks`
