# Guesty access, booking flow y ticket de soporte

Fecha de revision: 2026-05-19

## Respuesta corta

Si, podemos trabajar con Guesty.

Para la primera prueba necesitamos `Client ID` y `Client Secret`.

Hay dos tipos que conviene distinguir:

- Guesty Open API OAuth: sirve para consultar PMS, propiedades, reservas,
  webhooks y Reservations V3.
- Guesty Booking Engine API instance: sirve para flujo de booking engine,
  quotes y checkout estilo direct booking.

Sin credenciales no podemos consultar datos reales ni crear reservas desde
codigo.

## Que se puede hacer

### 1. Consultar propiedades, disponibilidad y reservas

Disponible con Guesty Open API:

- Autenticacion OAuth 2.0 con `client_credentials`.
- Listar propiedades.
- Buscar propiedades disponibles por fechas y ocupacion.
- Buscar reservas por filtros.
- Consultar detalle de reserva.

Esto es suficiente para la primera etapa del call center:

1. El cliente llama.
2. El concierge pregunta fechas, huespedes y motivo.
3. El backend consulta disponibilidad.
4. El concierge recomienda opciones reales.
5. Si el cliente quiere avanzar, se captura telefono/correo y se escala o se
   envia link por SMS.

### 2. Crear quotes y reservas

Tambien es posible, pero debe activarse como fase controlada.

Guesty documenta tres caminos:

- Booking Engine API reservation quote flow: recomendado para un flujo de
  reserva web/direct booking. Usa una instancia de Booking Engine API.
- Reservations V3 API: nuevo flujo Open API para quotes y direct bookings, con
  mas personalizacion. Usa Open API OAuth.
- `POST /reservations`: flujo legacy; Guesty indica que solo conviene si ya
  existe una integracion basada en ese flujo.

Decision recomendada para Glam Homes:

1. Fase 1: solo lectura + disponibilidad.
2. Fase 2: crear quote o inquiry, no reserva confirmada.
3. Fase 3: permitir reserva confirmada solo con validaciones duras y aprobacion
   humana.
4. Fase 4: automatizar confirmacion cuando ya existan reglas de pago,
   contrato, taxes, depositos y cancelacion.

### 3. Enviar link por SMS

Si no queremos crear reservas automaticamente al inicio, el fallback correcto es:

- Consultar disponibilidad.
- Recomendar propiedad.
- Enviar por SMS un link directo al cliente usando Twilio.
- Registrar resumen de la llamada y buyer persona.

El SMS puede incluir:

```text
Glam Homes: aqui tienes la opcion que revisamos por telefono:
<booking_link>

Fechas: <check_in> a <check_out>
Huespedes: <guests>

Responde a este mensaje si quieres que el equipo te ayude a finalizar.
```

Pendiente: definir de donde saldra el `booking_link` por propiedad. Puede venir
de Guesty, del sitio de Glam Homes, o de una tabla interna si Guesty no expone
el link exacto que queremos enviar.

## Donde crear las credenciales Open API OAuth

Link directo:

```text
https://app.guesty.com/main/integrations/open-api/applications
```

Ruta en Guesty:

1. Iniciar sesion en Guesty.
2. Ir a `Integrations`.
3. Seleccionar `OAuth applications`.
4. Crear `New application`.
5. Nombre recomendado: `GLAM HOMES Call Center Agent`.
6. Copiar `Client ID` y `Client Secret`.

Importante: el `Client Secret` solo se ve una vez. Si no se guardo, hay que
crear otra aplicacion OAuth.

## Donde crear credenciales Booking Engine API

Ruta en Guesty:

1. Iniciar sesion en Guesty.
2. Ir a `Marketing y ventas`.
3. Abrir `Distribucion`.
4. Entrar a `API del motor de reservas de Guesty`.
5. Crear una nueva clave API.
6. Elegir si el flujo sera `Solicitar reserva` o `Reserva instantanea`.
7. Seleccionar propiedades.
8. Guardar y copiar `Client ID` y `Client Secret`.

Importante: en sandbox normalmente solo permite una instancia API.

## Si no aparece OAuth applications

Levantar ticket aqui:

```text
https://help.guesty.com/hc/es/requests/new
```

La pagina pide iniciar sesion para enviar la solicitud.

Tambien se puede entrar desde:

```text
https://www.guesty.com/contact-us/
```

Elegir `Support` / `Submit a ticket for technical support`.

## Email / ticket sugerido

Asunto:

```text
Request for Guesty Open API OAuth access - Glam Homes Call Center Agent
```

Mensaje:

```text
Hello Guesty Support / Developer Team,

We are building a voice-based call center concierge for Glam Homes that will
help guests with booking questions, property availability, reservation lookup,
and support routing.

We need to enable Guesty Open API access for our account and generate OAuth
client credentials for a new application:

Application name:
GLAM HOMES Call Center Agent

Initial scope:
- Read listings and property details
- Search availability by check-in/check-out dates and guest count
- Search and retrieve reservations
- Later phase: create reservation quotes or inquiries, pending our internal
  approval flow

Could you please confirm:
1. Whether Open API access is enabled for our account.
2. Where we can create the OAuth application inside Guesty.
3. Whether our plan supports Booking Engine API and/or Reservations V3 API.
4. Whether Booking Engine API credentials are separate from Open API OAuth in our account.
5. The recommended API flow for creating quotes/inquiries and, later, confirmed
   direct bookings.
6. Any permissions or account settings required for these endpoints.

We understand that Guesty Open API uses OAuth client credentials and that the
Client Secret is only visible once, so we will store it securely.

Thank you,
Glam Homes
```

Version corta en espanol:

```text
Hola equipo de Guesty,

Estamos creando un concierge telefonico con IA para Glam Homes. Necesitamos
habilitar Guesty Open API y crear una aplicacion OAuth para consultar
propiedades, disponibilidad y reservas. En una fase posterior queremos crear
quotes/inquiries y posiblemente reservas directas confirmadas.

Podrian confirmar si nuestra cuenta tiene Open API habilitada, donde crear el
Client ID y Client Secret, y si recomiendan Booking Engine API o Reservations V3
para el flujo de reserva?

Aplicacion sugerida: GLAM HOMES Call Center Agent

Gracias.
```

## Referencias oficiales

- Crear OAuth app y obtener Client ID/Client Secret:
  `https://help.guesty.com/hc/es/articles/9370472424605-Utilizando-la-API-abierta-de-Guesty`
- Autenticacion Open API:
  `https://open-api-docs.guesty.com/docs/authentication`
- Disponibilidad/listings:
  `https://open-api-docs.guesty.com/docs/available-listings`
- Reservations V3 booking flow:
  `https://open-api-docs.guesty.com/docs/reservations-v3-booking-flow`
- Booking Engine reservation quote flow:
  `https://booking-api-docs.guesty.com/docs/new-reservation-creation-flow`
- Contacto Guesty:
  `https://www.guesty.com/contact-us/`
