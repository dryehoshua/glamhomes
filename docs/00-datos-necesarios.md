# Datos necesarios para empezar

## 1. Contexto de negocio

- Nombre legal/comercial exacto de Glam Homes.
- Ciudades o mercados donde opera.
- Tipos de propiedades que manejan.
- Idiomas que debe hablar el agente desde la prueba inicial.
- Horarios de atencion humana y horarios donde el agente toma control.
- Casos donde el agente debe transferir a una persona.

## 2. Flujos de llamada

- Booking nuevo: que informacion debe capturar antes de avanzar.
- Reserva existente: como identificar al huesped.
- Cambios de fechas.
- Cancelaciones.
- Check-in y check-out.
- Problemas durante la estancia.
- Preguntas frecuentes por propiedad.
- Emergencias o casos sensibles.

## 3. Twilio

- Confirmar si el numero +17864813013 sera para llamadas entrantes, salientes o ambas.
- Account SID.
- Auth Token o API Key/Secret.
- Twilio phone number SID, si aplica.
- Webhook esperado para llamadas entrantes.
- Pais/mercados permitidos para llamadas salientes.
- Reglas de grabacion de llamadas.
- Reglas de consentimiento para grabacion, si se va a grabar.

## 4. Guesty

- Tipo de acceso disponible: API key, OAuth o entorno sandbox.
- Documentacion o credenciales del entorno de prueba.
- Campos disponibles para reservas, huespedes, propiedades, calendarios y pagos.
- Permisos permitidos: solo lectura o tambien crear/modificar reservas.
- Webhooks disponibles para cambios de reserva.

## 5. Base de conocimiento

- FAQs actuales.
- Politicas de cancelacion.
- Reglas por propiedad.
- Manual de check-in/check-out.
- Scripts actuales de atencion, si existen.
- Escalaciones internas: nombres, roles, telefono/correo y horario.

## 6. Voz y comportamiento del agente

- Nombre del agente.
- Tono: formal, calido, premium, directo, bilingue, etc.
- Frases prohibidas o temas que debe evitar.
- Limites: que nunca debe prometer ni confirmar sin validacion.
- Politica para errores o informacion incompleta.

## 7. Pruebas

- Numeros de telefono autorizados para pruebas.
- Escenarios de prueba prioritarios.
- Reservas ficticias o reales para test.
- Criterios para considerar exitosa la prueba.

## 8. Decisiones tecnicas

- Proveedor de IA para voz/conversacion.
- Stack preferido para el backend.
- Hosting deseado para webhooks.
- Base de datos, si se requiere guardar historiales.
- Canal para alertas internas: email, Slack, Teams, WhatsApp u otro.
