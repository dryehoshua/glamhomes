# Call Analytics y Guest Journey

Fecha: 2026-06-10

## Dashboard web

Las metricas internas de llamadas son solo para usuarios con acceso al dashboard
web. No deben entregarse por telefono al publico general.

Capacidades actuales:

- Consultar volumen de llamadas por periodo.
- Filtrar por `Today`, `7 days`, `30 days`, `All` o rango custom.
- El rango default del dashboard es `7 days` para que abra con actividad
  reciente; `Today` queda disponible para corte diario.
- Ordenar conversaciones por:
  - `Recent`
  - `Relevant`
  - `Most interaction`
  - `Least interaction`
- Ver hilos por numero telefonico, no por `CallSid` individual.
- Abrir el historial del numero dentro del periodo seleccionado.

Endpoints:

- `GET /api/calls/threads?limit=50&sort=recent|relevant|most|least&q=...&start=...&end=...`
- `GET /api/calls/thread?thread_id=phone:<digits>&start=...&end=...`

`start` y `end` se mandan como timestamps ISO desde el navegador. El endpoint
requiere el acceso protegido ya existente.

## Regla para voz

Si alguien pide por llamada datos internos como cantidad de llamadas, transcripts,
llamadas del dia, reportes de la semana/mes o llamadas relevantes, el concierge
no debe leer esos datos por telefono. Debe indicar que esa informacion esta
disponible solo en el dashboard web seguro o por flujo admin aprobado.

## SMS durante llamadas

El agente debe ofrecer SMS de forma proactiva, especialmente cuando:

- Recomienda propiedades.
- Comparte links directos, Airbnb, Booking o VRBO.
- Confirma informacion util.
- Resume siguientes pasos.

Frase sugerida:

`I can also text that link to you now if you'd like.`

## Soporte humano temporal

Numero humano actual para eventualidades y handoff:

`+525630907754`

Variable local:

`GLAM_HUMAN_SUPPORT_PHONE`

El agente debe mandar SMS de handoff cuando:

- El cliente pide humano/agente/representante.
- El cliente ya no quiere seguir con IA.
- Hay acceso bloqueado, mantenimiento serio, seguridad, agua, electricidad,
  cerradura, AC critico, cliente molesto durante estancia, pagos, refunds,
  cancelaciones, cambios de fecha o excepciones de politica.

## Roles del concierge

### 1. Pre-booking concierge

Objetivo: recomendar propiedades, calificar al cliente y mover a link/quote/handoff.

Datos a pedir:

- Fechas.
- Numero de huespedes.
- Zona o preferencia de experiencia.
- Motivo del viaje.
- Must-haves.
- Presupuesto aproximado si hay friccion de precio.

Reglas:

- No inventar disponibilidad ni totales.
- Revisar Guesty si hay fechas/guests.
- Recomendar 1-3 opciones maximo.
- Ofrecer SMS con links.

### 2. Reservation confirmation

Objetivo: confirmar una reserva sin exponer datos sensibles.

Datos a pedir:

- Confirmation code.
- Al menos un dato coincidente: telefono, email o nombre.
- Si hay duda, pedir un segundo dato razonable.

Puede compartir:

- Status basico.
- Fechas.
- Propiedad.
- Fuente de reserva.

No compartir:

- Codigos de acceso.
- Datos de pago sensibles.
- Direccion exacta si no corresponde.
- Cambios o excepciones sin humano.

### 3. Pre-check-in welcome

Objetivo: preparar llegada.

Datos a confirmar:

- Nombre.
- Confirmation code o telefono/email asociado.
- Fecha de llegada.
- Hora estimada de llegada.
- Numero de huespedes.
- Si necesitan orientacion por SMS.

Accion:

- Dar bienvenida.
- Confirmar que el equipo puede ayudar con llegada.
- Enviar SMS de orientacion si existe recurso disponible.
- Escalar si piden early check-in, access code, excepciones o hay riesgo.

### 4. Check-in welcome / stay kickoff

Objetivo: confirmar entrada y arrancar la estancia.

Preguntas:

- `Have you already completed check-in and are you inside?`
- `Is everything working as expected so far?`

Accion:

- Si ya entro: bienvenida breve, recordar que puede pedir ayuda.
- Si no entro: capturar problema, propiedad/reserva y escalar si es acceso.
- Ofrecer SMS con orientacion o links utiles.

### 5. Mid-stay follow-up

Objetivo: detectar problemas temprano.

Preguntas:

- Como va la estancia.
- Que ha sido lo mejor.
- Si algo necesita atencion.

Escalar:

- Mantenimiento.
- Acceso.
- Seguridad.
- Cliente molesto.
- Queja seria.

### 6. Checkout reminder

Objetivo: orientar salida.

Datos a confirmar:

- Reserva.
- Fecha de checkout.
- Preguntas de salida.

Reglas:

- Late checkout requiere humano/Guesty/politica.
- No prometer excepciones.
- Ofrecer enviar instrucciones por SMS si estan disponibles.

### 7. Post-stay

Objetivo: agradecimiento, feedback y retorno.

Accion:

- Agradecer.
- Capturar feedback.
- Escalar objetos perdidos, refunds, quejas o nuevas reservas que requieran
  humano.

## Pendiente para siguiente etapa

- Definir si estos roles viviran en un solo numero o varias lineas.
- Crear scheduler para mensajes outbound basados en Guesty:
  - pre-check-in
  - check-in day
  - mid-stay
  - checkout reminder
  - post-stay
- Decidir politica legal/consentimiento para mensajes automaticos.
- Definir plantillas SMS por propiedad y etapa.
- Ampliar Guesty de read-only a acciones controladas solo con aprobacion humana.
