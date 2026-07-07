# Guesty Confirmation And Human Handoff

Fecha: 2026-07-06

## Estado actual

El concierge de GLAM HOMES ya puede consultar Guesty en modo solo lectura. La
conexion live respondio correctamente con credenciales configuradas y token
valido.

## Herramientas habilitadas

- `guesty_status`: verifica credenciales y token Guesty.
- `guesty_search_reservation`: busca reservas por codigo, telefono, email o
  nombre.
- `guesty_confirm_reservation`: confirma una reserva de forma segura. En modo
  local `code_only` puede compartir datos basicos despues de confirmar el codigo.
  Si el codigo fue transcrito de forma aproximada, requiere validar nombre con
  similitud suficiente antes de compartir datos.
- `guesty_confirmed_stay_details`: consulta detalles internos confirmados de
  estancia, incluyendo direccion, horarios, amenities, custom fields, check-in,
  door code, Wi-Fi/StayFi e instrucciones cuando Guesty los tiene poblados.
- `guesty_get_reservation`: consulta una reserva por ID interno de Guesty.
- `guesty_list_listings`: lista propiedades desde Guesty.
- `guesty_available_listings`: consulta disponibilidad por fechas y numero de
  huespedes.
- `guesty_listing_calendar`: consulta calendario minificado de disponibilidad y
  precio por listing.
- `glam_search_public_property_links`: busca links publicos activos de Glam
  Homes, Airbnb, Booking o VRBO cuando existan en la base local.
- `twilio_send_property_link_sms`: envia por SMS un link activo de propiedad.
- `twilio_send_stay_details_sms`: envia detalles confirmados de estancia por
  SMS despues de validar la reserva.
- `twilio_send_human_handoff_sms`: manda SMS al contacto humano de soporte
  cuando el caller pide una persona o no quiere seguir con la IA.
- `twilio_transfer_call_to_human`: intenta transferir una llamada Twilio activa
  al contacto humano de soporte y tambien deja reporte por SMS.

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

1. Dar al concierge el codigo de confirmacion.
2. Confirmar que el agente repite el codigo antes de usar herramientas.
3. Confirmar que responde con datos basicos o detalles de estancia solo desde
   Guesty.
4. Confirmar que ofrece SMS para datos largos/sensibles como direccion,
   check-in, Wi-Fi o instrucciones.
5. Probar un codigo aproximado y validar que pida nombre si hay fuzzy match.

## Pruebas realizadas

- Guesty live status: OK.
- Confirmacion con codigo inexistente: OK, responde no encontrado.
- Confirmacion con codigo real: OK en modo local `code_only`.
- Confirmacion con codigo aproximado + nombre validado: OK para llamadas con
  transcripcion ruidosa.
- Detalles confirmados de estancia: OK cuando Guesty tiene fields poblados.
- Handoff SMS dry-run: OK, genera cuerpo y evento de transcript.
- Handoff/transfer humano: configurado para usar el contacto humano vigente.
