# Documentacion GLAM HOMES

Este es el punto de entrada para que un nuevo agente retome el proyecto sin
perder contexto.

## Estado actual

- Carpeta principal: `/Users/dryehoshuapython/Desktop/GLAM HOMES`.
- App local: `http://127.0.0.1:3000`.
- Voz por defecto: `ash`.
- Numero Twilio de GLAM HOMES: `+17864813013`.
- No tocar Kim Live ni ningun numero terminado en `7532`.
- Hostname publico previsto: `https://glamhomes.aipeople.app`.
- Transcripciones locales: `transcripts/YYYY-MM-DD/`.
- Guesty Open API ya esta configurado localmente con OAuth y funciona en modo
  lectura.
- El agente puede consultar reservas, listings, disponibilidad y calendario
  minificado desde Guesty.
- El agente carga la knowledge base conversacional privada desde
  `data/private/guesty-conversations/GLAM HOMES KNOWLEDGE BASE`.
- El dashboard incluye inbox por numero, analytics, transcripts, selector de
  voz, contacto de emergencia y modo de validacion de reserva.
- Las acciones de escritura en Guesty, pagos y links de pago siguen bloqueadas
  por diseno hasta definir aprobaciones humanas.

## Secciones de la carpeta

- `documentacion/`: resumen ejecutivo, estado del proyecto y handoff.
- `docs/`: documentacion tecnica y documentos base extraidos de PDFs.
- `programas/`: acceso humano a los programas del proyecto.
- `apps/voice-agent/`: codigo activo del concierge local.
- `data/`: exports operativos, incluyendo links publicos de propiedades.
- `reports/`: capturas de QA visual.

## Archivos clave

- `documentacion/00-handoff-nuevo-agente.md`
- `documentacion/11-twilio-cloudflare-runbook.md`
- `documentacion/15-cierre-exportacion-github.md`
- `docs/09-guesty-api-capabilities-map.md`
- `docs/06-prompt-maestro-concierge-voz.md`
- `data/guesty-property-links.csv`
- `data/guesty-property-links.json`
- `data/guesty-property-links.md`

## Arranque local

Desde la carpeta principal:

```bash
python3 apps/voice-agent/server.py
```

Luego abrir:

```text
http://127.0.0.1:3000
```

## Actualizar links publicos de propiedades

```bash
python3 apps/voice-agent/export_property_links.py
```

El script refresca el inventario visible en:

```text
https://theglamhomes.guestybookings.com/en/properties?minOccupancy=1
```

Al 2026-05-19 devuelve 55 propiedades publicas.

## Cierre y exportacion

La guia final para copiar la carpeta completa, preparar GitHub y saber que datos
son privados esta en:

```text
documentacion/15-cierre-exportacion-github.md
```
