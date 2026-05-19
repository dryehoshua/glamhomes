# Guesty Open API - estudio inicial

Fecha de revision: 2026-05-18

## Link para crear credenciales

Trabaja aqui, despues de iniciar sesion en Guesty:

https://app.guesty.com/main/integrations/open-api/applications

Ruta en el dashboard:

1. Entrar a Guesty.
2. Ir a `Integrations`.
3. Abrir `OAuth applications`.
4. Crear `New application`.
5. Nombre recomendado: `GLAM HOMES Call Center Agent`.
6. Copiar `Client ID` y `Client Secret`.

Importante: Guesty muestra el `Client Secret` solo la primera vez. Guardarlo en un lugar seguro.

No compartir la contrasena de la cuenta Guesty o Gmail para esta integracion. La integracion debe funcionar con `Client ID` y `Client Secret` de una app OAuth.

## Documentacion oficial revisada

- Quick start: https://open-api-docs.guesty.com/docs/quick-start-guide
- Authentication: https://open-api-docs.guesty.com/docs/authentication
- Rate limits: https://open-api-docs.guesty.com/docs/rate-limits
- Search reservations: https://open-api-docs.guesty.com/docs/how-to-search-for-reservations
- Reservation reference: https://open-api-docs.guesty.com/reference/get_reservations
- Listings guide: https://open-api-docs.guesty.com/docs/searching-for-available-listings-and-all-listings
- Webhooks overview: https://open-api-docs.guesty.com/docs/webhooks

## Autenticacion

Guesty Open API usa OAuth 2.0 con `client_credentials`.

Endpoint de token:

```text
POST https://open-api.guesty.com/oauth2/token
```

Body `application/x-www-form-urlencoded`:

```text
grant_type=client_credentials
scope=open-api
client_id=<GUESTY_CLIENT_ID>
client_secret=<GUESTY_CLIENT_SECRET>
```

El API responde con:

- `access_token`
- `token_type=Bearer`
- `expires_in=86400`
- `scope=open-api`

Regla critica: Guesty permite pocos tokens por dia. Hay que cachear el token y reutilizarlo hasta que este cerca de expirar.

## Base URL

```text
https://open-api.guesty.com/v1
```

Todas las llamadas usan:

```text
Authorization: Bearer <access_token>
Accept: application/json
```

## Endpoints necesarios para el agente

### Reservas

Buscar reservas:

```text
GET /reservations
```

Parametros utiles:

- `filters`: array JSON con filtros.
- `fields`: campos separados por espacios.
- `sort`: ordenar por `_id`, `createdAt`, `lastUpdatedAt`, etc.
- `limit`: maximo 100.
- `skip`: paginacion.

Buscar por confirmation code:

```json
[{"operator":"$in","field":"confirmationCode","value":["GY-XXXX"]}]
```

Campos iniciales recomendados:

```text
_id confirmationCode status checkInDateLocalized checkOutDateLocalized listing._id listing.title guest._id guest.fullName guest.email guest.phone source balanceDue money.totalPaid money.balanceDue plannedArrival plannedDeparture
```

Traer detalle:

```text
GET /reservations/{id}
```

Para horarios de llegada/salida conviene pedir:

```text
listing.defaultCheckInTime plannedArrival listing.defaultCheckOutTime plannedDeparture checkInDateLocalized checkOutDateLocalized
```

### Listings / propiedades

Listar propiedades:

```text
GET /listings
```

Campos iniciales:

```text
_id title nickname address.full address.city address.country accommodates bedrooms bathrooms amenities pictures active listed
```

Buscar disponibilidad:

```text
GET /listings?available={"checkIn":"YYYY-MM-DD","checkOut":"YYYY-MM-DD","minOccupancy":2}
```

### Guests

Listar/buscar huespedes:

```text
GET /guests-crud
```

Campos iniciales:

```text
fullName guestEmail guestPhone address id
```

## Webhooks utiles

Para etapas automatizadas mas adelante:

- `reservation.new`
- `reservation.updated`
- `reservation.messageReceived`
- `reservation.messageSent`
- `payments.received`
- `payments.failed`
- `payments.refunded`
- `payments.overdue`
- `listing.updated`
- `guest.created`
- `guest.updated`

Crear webhook:

```text
POST /webhooks
```

Body:

```json
{
  "url": "https://PUBLIC_BASE_URL/guesty/webhook",
  "events": ["reservation.new", "reservation.updated"]
}
```

Los webhooks deben responder con status 2xx rapido. Guesty reintenta con backoff si fallan.

## Rate limits

Open API:

- 15 requests por segundo.
- 120 requests por minuto.
- 5,000 requests por hora.

Si Guesty devuelve `429`, respetar el header `Retry-After`.

## Modo seguro recomendado para el call center

Etapa 1: solo lectura.

- Buscar reserva por confirmation code.
- Buscar reservas por telefono/correo/nombre cuando validemos campos reales.
- Consultar propiedad.
- Consultar estado, fechas, nombre de propiedad y datos permitidos.
- Guardar resumen y decision de seguimiento.

Bloqueado hasta aprobacion:

- Crear reserva.
- Modificar fechas.
- Cancelar.
- Reembolsar.
- Cambiar pagos.
- Dar descuentos.
- Enviar mensajes masivos.

## Pendiente para validar con credenciales reales

- Confirmar permisos exactos del OAuth application.
- Confirmar nombres reales de campos para telefono/correo del guest en reservas.
- Probar filtro por `confirmationCode`.
- Probar filtro por `guest.email` y `guest.phone` si estan disponibles.
- Probar listing availability para booking.
- Confirmar si se usara Open API, Booking Engine API o ambos para reservas nuevas.

## Implementacion local actual

Backend:

```text
apps/voice-agent/server.py
```

Cliente CLI:

```text
apps/voice-agent/guesty_client.py
```

Endpoints locales:

```text
GET /api/guesty/status?live=1
GET /api/guesty/listings?limit=5
GET /api/guesty/reservations?limit=5
GET /api/guesty/reservation-by-code?code=GY-XXXX
GET /api/guesty/reservation?id=<reservation_id>
POST /api/guesty/tool
```

Herramientas de voz Realtime configuradas en modo solo lectura:

- `guesty_status`
- `guesty_search_reservation`
- `guesty_get_reservation`
- `guesty_list_listings`

Regla operativa: si no hay credenciales, el agente debe decirlo y pedir escalacion/configuracion. Si hay credenciales, puede consultar reservas y propiedades, pero no modificar nada.
