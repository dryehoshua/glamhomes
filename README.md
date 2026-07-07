# GLAM HOMES Call Center Agent

Proyecto para construir un agente telefonico de booking y soporte para Glam Homes.

## Objetivo

Crear un agente capaz de atender llamadas entrantes y salientes relacionadas con reservas, clientes, propiedades y problemas operativos de Glam Homes, usando Twilio para telefonia y Guesty para gestion de reservas.

## Numero Twilio inicial

- Numero asignado: +17864813013

## Fases iniciales

1. Documentar el funcionamiento esperado del agente.
2. Definir flujos de llamada para booking, cambios de reserva, dudas frecuentes y soporte.
3. Conectar Twilio en modo prueba.
4. Conectar Guesty para consultar reservas, huespedes, propiedades y estados.
5. Crear un primer agente conversacional con herramientas controladas.
6. Ejecutar pruebas internas con llamadas reales.
7. Activar progresivamente por etapa de reserva.

## Estructura

- `documentacion/`: punto de entrada y handoff para nuevos agentes.
- `docs/`: documentacion funcional y tecnica.
- `programas/`: seccion de programas y comandos operativos.
- `apps/`: codigo de aplicaciones y servicios.
- `data/`: exports operativos, como links publicos de propiedades.
- `.env.example`: plantilla de variables de entorno.
- `apps/voice-agent/`: backend inicial y cliente Guesty de prueba.

## Estado final y exportacion

La guia de cierre del proyecto, exportacion de carpeta y politica GitHub esta en
`documentacion/15-cierre-exportacion-github.md`.

Para copiar el proyecto a otro entorno interno, copiar la carpeta completa
`GLAM HOMES`. Para GitHub, mantener fuera los datos privados y secretos que ya
estan cubiertos por `.gitignore`: `.env`, `.cache/`, `API Keys/`,
`data/private/`, `transcripts/*` y `logs/`.

La knowledge base conversacional de Guesty vive dentro de:

```text
data/private/guesty-conversations/GLAM HOMES KNOWLEDGE BASE
```

El agente de voz carga al iniciar el archivo
`agent_runtime_best_practices.md` de esa knowledge base como entrenamiento
operativo de runtime.

## Referencia Kim Live / BIFROST

Se reviso la carpeta `/Users/dryehoshuapython/Documents/BIFROST`, especialmente el sistema `Kim Live`, porque ya contiene funciones de llamadas con Twilio que pueden ahorrar trabajo.

El plan es reutilizar patrones y piezas tecnicas, no copiar todo BIFROST:

- Bridge Twilio Media Streams <-> OpenAI Realtime.
- Endpoints `/twilio/voice`, `/twilio/status`, `/twilio/sms` y `/twilio/health`.
- Registro de llamadas y transcripts.

## Twilio + Cloudflare

El numero de Glam Homes configurado localmente es `+17864813013`. No tocar los
webhooks ni numeros de Kim Live, especialmente el numero que termina en `7532`.

El runbook actualizado para levantar `glamhomes.aipeople.app`, abrir el bridge de
Twilio Media Streams y aplicar los webhooks cuando el tunel este listo esta en
`documentacion/11-twilio-cloudflare-runbook.md`.

Las transcripciones se guardan localmente en `transcripts/` y esa carpeta esta
ignorada por Git porque puede contener datos personales.
- Confirmacion antes de acciones externas.
- Politica de privacidad para llamadas entrantes.

Ver detalles en `docs/02-reuso-kim-live-bifrost.md`.

## Prompt y buyer personas

La guia de comportamiento del concierge de voz quedo en `docs/06-prompt-maestro-concierge-voz.md`.

La clasificacion inicial de perfiles quedo en `docs/07-buyer-persona-classification.md`.

El plan de acceso Guesty, booking flow y ticket de soporte quedo en
`docs/08-guesty-access-ticket-and-booking-flow.md`.

El mapa de capacidades reales probadas con Guesty quedo en
`docs/09-guesty-api-capabilities-map.md`.

El mapa actualizable de links publicos de propiedades quedo en
`documentacion/10-mapa-links-propiedades.md` y los exports estan en `data/`.

## Guesty Open API

Para crear las credenciales de Guesty:

```text
https://app.guesty.com/main/integrations/open-api/applications
```

Guesty entrega `Client ID` y `Client Secret`, no una API key simple. Ver el estudio en `docs/05-guesty-open-api-estudio.md`.

## Principio de seguridad

No guardar credenciales reales en documentos ni codigo. Las llaves de Twilio, Guesty y cualquier proveedor de IA deben vivir en variables de entorno locales o en un gestor seguro de secretos.
