# Funcionamiento general

## Resumen

El agente telefonico de Glam Homes atendera llamadas relacionadas con reservas y soporte al huesped. Twilio recibira o iniciara la llamada, el backend conectara la llamada con el agente conversacional, y Guesty sera la fuente de verdad para consultar informacion de reservas y propiedades.

## Componentes

1. Twilio
   - Recibe llamadas entrantes.
   - Permite llamadas salientes para pruebas o seguimiento.
   - Envia eventos al backend mediante webhooks.

2. Backend del agente
   - Recibe webhooks de Twilio.
   - Controla la sesion de llamada.
   - Consulta herramientas externas como Guesty.
   - Decide cuando responder, preguntar, transferir o escalar.

3. Guesty
   - Fuente de datos para reservas, huespedes, propiedades, calendarios y estados.
   - Puede usarse primero en modo consulta y despues en modo accion, si se aprueba.

4. Base de conocimiento
   - Politicas, FAQs, reglas por propiedad y guias internas.
   - Debe estar separada por temas y actualizable sin tocar codigo critico.

5. Escalacion humana
   - El agente debe poder transferir o generar alerta cuando el caso exceda sus permisos.

## Flujo base de llamada entrante

1. Cliente llama al numero de Twilio.
2. Twilio envia el evento al webhook del backend.
3. El backend inicia una sesion del agente.
4. El agente saluda, identifica el motivo y recopila datos minimos.
5. Si el cliente tiene reserva, el agente valida identidad y busca la reserva en Guesty.
6. El agente responde o ejecuta acciones permitidas.
7. Si hay riesgo, falta de informacion o solicitud fuera de politicas, escala a una persona.
8. El backend guarda resumen, resultado y siguientes pasos.

## Flujos por etapa de reserva

- Pre-booking: resolver dudas, disponibilidad, precios orientativos y reglas.
- Booking activo: confirmar datos, responder dudas y preparar llegada.
- Pre-check-in: instrucciones, horarios, documentos, deposito y acceso.
- Durante estancia: soporte operativo, mantenimiento, quejas y emergencias.
- Post-check-out: objetos olvidados, cargos, reseñas y seguimiento.

## Primer alcance recomendado

Para la prueba inicial, el agente deberia operar en modo seguro:

- Responder FAQs.
- Buscar reservas en Guesty.
- Confirmar informacion no sensible.
- Tomar mensajes y crear resumen de seguimiento.
- Escalar cambios de dinero, cancelaciones, reembolsos, conflictos y emergencias.

Acciones como modificar reservas, cobrar, reembolsar o confirmar descuentos deberian quedar bloqueadas hasta validar politicas y permisos.
