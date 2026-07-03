# Glam Homes Concierge - Operating Manual

Fecha: 2026-07-02
Estilo: AI People / executive operations
Sistema: Glam Homes AI Concierge

## 1. Executive Summary

Glam Homes Concierge es un call center de IA para voz, SMS y soporte operativo
de huespedes y prospectos. Atiende llamadas por Twilio, conversa con OpenAI
Realtime en modo estandar, consulta Guesty en solo lectura, envia SMS cuando el
cliente necesita datos accionables y escala a humanos cuando la solicitud rebasa
la autoridad del concierge.

El sistema ya no debe evaluarse solo por volumen de llamadas. El tablero debe
responder cuatro preguntas de direccion:

1. Que necesita atencion humana hoy.
2. Que problemas se repiten por cliente, tema o subtopic.
3. Que tan bien resuelve la IA sin repetir llamadas.
4. Que oportunidades comerciales o VIP deben pasar a un manager.

## 2. Operating Principles

- Customer first: el cliente no debe trabajar para el sistema. Si da el codigo
  de reservacion, el concierge valida y consulta.
- Fast resolution: resolver en la primera llamada siempre que exista informacion
  suficiente.
- Human safety net: si el cliente pide humano, esta molesto, hay emergencia,
  hay informacion faltante o se requiere aprobacion, se notifica y se ofrece
  interconexion telefonica.
- SMS as memory: cualquier dato importante o delicado se ofrece por SMS al
  numero desde el cual llama el cliente, salvo alertas internas de emergencia o
  VIP.
- Guesty as source of truth: reservas, estado, propiedad, amenidades, direccion,
  check-in information, door code y Wi-Fi deben venir de Guesty cuando existan.
- No false confirmation: disponibilidad no significa aprobacion. Extensiones,
  descuentos, servicios especiales y excepciones requieren validacion humana.

## 3. System Architecture

### Channels

- Voice inbound: Twilio recibe la llamada y conecta el audio al bridge local.
- AI conversation: OpenAI Realtime maneja voz estandar y tool calling.
- SMS outbound: Twilio envia datos de estadia, links de propiedades, reportes
  a humanos y confirmaciones.
- Dashboard local: `glamhomes.aipeople.app` o `http://127.0.0.1:3000` muestra
  estado, analytics, llamadas y seguridad.

### Data Sources

- Guesty Open API: reservas, propiedades, disponibilidad, calendarios, custom
  fields y check-in information.
- Transcripts locales: carpeta `transcripts/`, ignorada por Git por privacidad.
- Data local: contactos de emergencia/VIP, propiedades publicas y configuracion.
- Twilio API: salud de numero, mensajes y llamadas recientes cuando hay
  credenciales.

### AI Engine

- Standard voices: flujo recomendado y activo para llamadas.
- Vapi voices: integracion disponible como opcion, pero no es el flujo objetivo
  actual cuando el usuario pide GPT/standard.

## 4. Frontend Panels

### Voice Panel

Objetivo: operar y probar el concierge.

Funciones principales:

- Seleccion de voz standard o Vapi.
- Estado de servicios: servidor local, Guesty, Twilio, modelo, voz activa.
- Monitor operativo de Twilio: llamadas recientes, mensajes y alertas.
- Indicador de anomalias: si un servicio critico falla, el tablero debe mostrar
  estado rojo.

Uso recomendado:

- Antes de probar llamadas reales, revisar que el monitor este verde.
- Si hay latencia o baja calidad, confirmar que el engine activo sea standard y
  que el bridge de Twilio este corriendo.

### Analytics Panel

Objetivo: direccion operativa del call center.

Metricas principales:

- Total calls: llamadas dentro del rango seleccionado.
- Prospects: llamadas con intencion de reservar.
- Transcript coverage: porcentaje de llamadas con transcript util.
- Human handoffs: escalaciones a humano.
- First call resolution: llamadas elegibles resueltas sin transferencia, sin
  abandono y sin repeticion posterior del mismo tema/subtopic.
- Avg resolution: tiempo medio hasta resolver o transferir.
- Repeat contact: clientes que llaman mas de una vez en ventana de 48 horas.
- Issues detected: cantidad de asuntos/subtopics detectados.
- Influencers: llamadas o numeros donde el cliente manifiesta ser influencer,
  creador o colaborador.
- Needs attention: conversaciones agresivas, frustradas o no resueltas.
- Missed / abandoned: llamadas perdidas o abandonadas.
- SMS sent: mensajes enviados a huespedes o humanos.

Secciones nuevas:

- Operations Priorities: resumen ejecutivo de lo que requiere accion.
  - Priority queue: conversaciones rojas por frustracion o problema no resuelto.
  - Repeat issue: subtopic con mayor repeticion.
  - VIP pipeline: llamadas de influencer/VIP.
  - Quality signal: llamadas con felicitacion o agradecimiento fuerte.
- Calls by day and hour: mapa para cobertura de horarios.
- Subtopics and repeats: volumen, repeticion, escalacion y duracion por
  subtopic.
- Escalations by reason: motivo de transferencia o reporte humano.
- Frequent concepts: conceptos reales inferidos de conversaciones, no texto
  aleatorio.

Critica de standard industrial:

- Lo correcto: ya mide FCR, repeat contact, handoffs, abandono, SMS y subtopics,
  que son indicadores comparables a un contact center moderno.
- Riesgo actual: demasiadas metricas sin jerarquia pueden ocultar la accion.
- Mejora aplicada: agregar una capa de prioridades operativas encima de las
  graficas para que el manager vea primero alertas, repeticion, VIP y calidad.
- Siguiente nivel: agregar CSAT post-call, politica formal de consentimiento,
  average speed of answer, service level y QA score automatizado por rubrica.

Benchmarks de referencia:

- FCR: los contact centers suelen medir resolucion en el primer contacto como
  indicador central de experiencia y eficiencia.
- Repeat contact: clave para saber si el primer contacto realmente resolvio el
  problema.
- AHT / resolution time: util, pero no debe optimizarse sacrificando resolucion.
- Abandon/missed calls: necesario para detectar fallas de respuesta o latencia.

Referencias utiles:

- Salesforce - First Call Resolution:
  https://www.salesforce.com/service/contact-center/first-call-resolution/
- SQM Group - FCR metric:
  https://www.sqmgroup.com/resources/library/blog/fcr-metric-operating-philosophy
- Zoom - Call center metrics:
  https://www.zoom.com/en/blog/call-center-metrics/
- Twilio Calls API:
  https://www.twilio.com/docs/voice/api/call-resource

### Calls Panel

Objetivo: inbox operativo de conversaciones.

Estructura:

- Lado izquierdo: numeros/clientes agrupados.
- Filtros: rango de fecha/hora, busqueda por telefono y keyword.
- Selector de llamadas: permite navegar primera, segunda o siguientes llamadas
  del mismo cliente.
- Vista limpia: estilo chat, solo huesped e IA.
- Vista tecnica: eventos, tool calls y resultados internos.
- Vista SMS: mensajes enviados como chat telefonico.
- Vista Audio: reproductor protegido de la grabacion Twilio por llamada, con
  controles nativos para adelantar/regresar y selector de velocidad.

Codigos visuales:

- Dorado: conversacion neutral.
- Rojo: cliente agresivo, frustrado o con problema no resuelto.
- Verde: cliente muy amable, agradecido o que felicito al concierge.
- Estrella: influencer o creador detectado.

Badges:

- Repeat contact: el cliente volvio a llamar.
- Same subtopic repeat: regreso por el mismo problema.
- Multiple issues: una llamada tuvo varios asuntos.
- Escalated: hubo reporte o transferencia humana.
- SMS: se enviaron mensajes relacionados.
- Needs attention: revisar prioritariamente.
- Praise: llamada con senal positiva.

### Security Panel

Objetivo: proteger configuraciones sensibles.

Acceso:

- Analytics, Calls, Security y cambio de voces quedan bloqueados con password.
- Password operativo actual: configurado por `GLAM_EMERGENCY_CONTACT_PASSWORD`,
  con fallback local `MosesGlam`.

Configuraciones:

- Emergency Advisor: numero que recibe reportes de emergencia o asuntos humanos.
- VIP Reservations: numero que recibe leads de influencer/VIP. Por ahora puede
  ser el mismo numero que emergencia.
- Requisitos de seguridad: permite bajar/subir candados de validacion de reserva
  desde el front end.
- Voice engine: selector entre Standard voices y Vapi voices, protegido.

## 5. Call Handling Logic

### Reservation Lookup

- El codigo de reservacion es suficiente para consultar.
- Si el codigo se escucha parecido, se permite tolerancia aproximada de 80%.
- Si el codigo no es exacto, el concierge pide nombre y acepta similitud
  fonetica aproximada de 80%.
- Si Caller ID encuentra una reserva activa o futura, saluda por nombre y ofrece
  ayuda con esa reserva.
- Si Caller ID encuentra solo reserva pasada o cancelada, saluda con
  "welcome back" y no asume que esa reserva esta activa.

### Property Expertise

Al validar una reserva, el concierge debe poder responder como experto de esa
propiedad:

- Direccion.
- Wi-Fi / StayFi.
- Door code.
- Check-in instructions.
- Check-in/out time.
- Amenidades.
- House rules.
- Parking.
- Custom fields.
- Campos faltantes en Guesty.

Si Guesty devuelve un campo vacio, el concierge lo dice claramente y escala a
humano.

### Extensions

Si el cliente pide extender:

1. Verificar disponibilidad en Guesty.
2. Explicar que disponibilidad no confirma la extension.
3. Notificar a humano para aprobacion final.
4. Ofrecer SMS con resumen.

### Human Advisor

Debe activarse cuando:

- El cliente lo pide.
- Hay emergencia.
- Hay cliente agresivo o problema no resuelto.
- Falta informacion critica en Guesty.
- Se pide servicio especial.
- Hay excepcion de politica.
- Hay VIP/influencer/collaboration.
- La IA no puede resolver con confianza.

Accion esperada:

1. Contestar al cliente que se avisa a un asesor humano.
2. Enviar SMS interno con numero del cliente, reservation code si existe y
   resumen del problema.
3. Ofrecer resolverlo por telefono e interconectar si la llamada esta activa.

## 6. Analytics Definitions

### FCR

Llamada elegible con transcript, sin transferencia, sin abandono y sin repeticion
posterior del mismo telefono/tema/subtopic dentro de 48 horas.

### Avg Resolution Time

Duracion Twilio si existe. Si no existe, ultimo evento menos primer evento. Si
hubo transferencia, se corta en el evento `human_transfer`.

### Repeat Contact

Mismo telefono con mas de una llamada dentro de 48 horas.

### Same-Subtopic Repeat

Repeat contact donde ambas llamadas comparten al menos un subtopic.

### Attention Call

Conversacion marcada roja por:

- Lenguaje agresivo o frustrado.
- Senal de no resuelto.
- Abandono/perdida con problema no cerrado.

### Praise Call

Conversacion marcada verde por:

- Agradecimiento fuerte.
- Felicitacion.
- Comentario positivo explicito sobre el servicio.

### Influencer

Llamada marcada cuando el cliente dice que es influencer, content creator,
TikTok/Instagram/YouTube creator, tiene seguidores o pide colaboracion.

## 7. Escalation Reason Taxonomy

Categorias soportadas:

- guest_requested_human
- missing_information
- unsupported_request
- operational_request
- access_issue
- maintenance
- policy_exception
- emergency
- vip_reservations
- ai_failure
- other

## 8. SMS Governance

Tipos:

- property_link
- stay_details
- human_handoff
- caller_confirmation
- inbound_sms
- sms

Reglas:

- Ofrecer SMS para datos importantes.
- Usar el numero del caller por defecto.
- No pedir otro numero salvo que el cliente lo solicite expresamente.
- Para emergencia/VIP, enviar al numero interno configurado.
- Registrar preview protegido, destino, tipo, CallSid y MessageSid cuando exista.

## 9. Security And Privacy

- No guardar credenciales en Git.
- Transcripts contienen PII y deben quedarse fuera de Git.
- El dashboard protegido no debe exponer telefonos, llamadas o configuracion sin
  password.
- Audio recording se controla con `GLAM_RECORD_CALLS`.
- Cuando esta activo, Twilio inicia `<Start><Recording>` antes del stream de IA.
- El panel reproduce el audio por endpoint protegido; no expone URLs publicas de
  Twilio en el navegador.
- Se debe validar el aviso de consentimiento de grabacion antes de produccion.

## 10. Human Verification Plan

Antes de presentar al cliente:

1. Abrir `http://127.0.0.1:3000`.
2. Confirmar que el monitor no tenga anomalias rojas.
3. Desbloquear dashboard con password.
4. Analytics:
   - Probar Today, 7 days, 30 days, All y Custom.
   - Confirmar que Operations Priorities no se encime en desktop ni mobile.
   - Revisar FCR, repeat contact, same subtopic y attention calls.
5. Calls:
   - Buscar por telefono.
   - Cambiar entre llamadas del mismo numero.
   - Revisar Clean chat, Technical view y SMS.
   - Confirmar que conversaciones rojas/verdes/doradas se distingan.
6. Security:
   - Cambiar Emergency Advisor y VIP Reservations.
   - Confirmar que quedan bloqueados al recargar sin password.
7. Llamada real:
   - Probar reservation code exacto.
   - Probar reservation code parecido + nombre parecido.
   - Pedir Wi-Fi/direccion/door code y aceptar SMS.
   - Pedir humano y confirmar SMS interno.
   - Pedir extension y confirmar que solo se informa disponibilidad, no
     aprobacion final.

## 11. Roadmap

Fase 1 completada / en curso:

- Dashboard operativo.
- Subtopics y repeat subtopic.
- SMS log.
- Clean chat y technical view.
- Influencer/VIP flag.
- Sentiment/attention coloring.
- Operations Priorities.

Fase 2 recomendada:

- Validar consentimiento legal y locucion de grabacion.
- Twilio abandoned/missed callbacks mas completos.
- CSAT post-call via SMS.
- QA score automatico por llamada.
- Export CSV/PDF para reportes semanales.

Fase 3:

- Clasificador LLM dedicado para subtopics/resolution quality.
- Deteccion de root cause por propiedad.
- SLA por tipo de problema.
- Alertas proactivas cuando una propiedad concentra quejas.

## 12. Current System Positioning

Glam Homes Concierge no es solo un bot de llamadas. Es un AI call center
vertical para hospitality:

- Resuelve dudas de huespedes.
- Convierte prospectos.
- Protege informacion sensible.
- Escala a humanos cuando conviene.
- Produce analytics accionables.
- Detecta VIP/influencers.
- Identifica problemas repetidos por cliente, subtopic y propiedad.

La prioridad tecnica no es reescribir el sistema. Es fortalecer la observabilidad
operativa, mejorar clasificacion y cerrar el ciclo entre llamada, SMS, humano y
dashboard.
