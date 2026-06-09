# Guesty Confirmation And Human Handoff

Fecha: 2026-06-09

## Estado actual

El concierge de GLAM HOMES ya puede consultar Guesty en modo solo lectura. La
conexion live respondio correctamente con credenciales configuradas y token
valido.

## Herramientas habilitadas

- `guesty_status`: verifica credenciales y token Guesty.
- `guesty_search_reservation`: busca reservas por codigo, telefono, email o
  nombre.
- `guesty_confirm_reservation`: confirma una reserva de forma segura. Si solo
  recibe el codigo, detecta si existe pero pide un dato adicional antes de
  compartir fechas, propiedad o estado. Si el codigo y un dato del huesped
  coinciden, devuelve detalles basicos.
- `guesty_get_reservation`: consulta una reserva por ID interno de Guesty.
- `guesty_list_listings`: lista propiedades desde Guesty.
- `guesty_available_listings`: consulta disponibilidad por fechas y numero de
  huespedes.
- `guesty_listing_calendar`: consulta calendario minificado de disponibilidad y
  precio por listing.
- `glam_search_public_property_links`: busca links publicos activos de Glam
  Homes, Airbnb, Booking o VRBO cuando existan en la base local.
- `twilio_send_property_link_sms`: envia por SMS un link activo de propiedad.
- `twilio_send_human_handoff_sms`: manda SMS al contacto humano de soporte
  cuando el caller pide una persona o no quiere seguir con la IA.

## Limites actuales

- Guesty esta en modo read-only. El concierge puede consultar, pero no crear,
  modificar, cancelar ni cobrar reservas todavia.
- No se deben prometer cambios de reserva, pagos, refunds, late checkout, early
  check-in, eventos, mascotas o excepciones sin confirmacion humana.
- Para habilitar operaciones de escritura hay que definir permisos, auditoria,
  aprobaciones y politicas de pago antes de usar endpoints mutables.

## Perfiles de prueba

Se genero un archivo privado local con perfiles reales/redactados:

`data/private/guesty-test-profiles.json`

Ese directorio esta ignorado por Git para no subir PII. Los perfiles incluyen
reservas confirmadas cercanas, codigo de confirmacion, estado, fechas, propiedad
y un nombre de validacion para probar la compuerta de seguridad.

Flujo de prueba recomendado:

1. Dar al concierge solo el codigo de confirmacion.
2. Esperar que pida un segundo dato del huesped.
3. Dar el nombre de validacion del perfil.
4. Confirmar que responde solo detalles basicos y ofrece enviar la informacion
   por SMS.

## Pruebas realizadas

- Guesty live status: OK.
- Confirmacion con codigo inexistente: OK, responde no encontrado.
- Confirmacion con codigo real + nombre validado: OK, comparte estado, fechas y
  propiedad basica.
- Handoff SMS dry-run: OK, genera cuerpo y evento de transcript.
- Handoff SMS real a `+5230907754`: fallo Twilio `21211 Invalid 'To' Phone
  Number`. Se necesita un numero E.164 completo y valido para dejar el handoff
  enviando SMS reales.
