# Cierre, exportacion y GitHub

Fecha de auditoria: 2026-07-06

## Objetivo

Dejar el proyecto GLAM HOMES listo para copiarse como carpeta completa y para
mantener una version limpia en GitHub.

La carpeta canonica del proyecto es:

```text
/Users/dryehoshuapython/Desktop/GLAM HOMES
```

Todo lo operativo que se necesita para entender, correr y exportar el proyecto
debe vivir dentro de esa carpeta. Los secretos reales, tokens, transcripts y
exports privados no deben subirse a GitHub.

## Estado funcional final

- App local principal: `apps/voice-agent/server.py`.
- Frontend/dashboard: `apps/voice-agent/public/index.html`.
- URL local: `http://127.0.0.1:3000`.
- Host publico esperado: `https://glamhomes.aipeople.app`.
- Numero Twilio GLAM HOMES: `+17864813013`.
- Voz OpenAI por defecto: `ash`.
- Voz Vapi opcional: `vapi:riley`.
- Guesty: conectado en modo lectura.
- Herramientas activas: reservas, listings, disponibilidad, calendario, links
  publicos de propiedades, SMS, handoff humano, transferencia Twilio y detalles
  confirmados de estancia.
- Dashboard: inbox por numero, analytics, transcripts, monitor Twilio, selector
  de voz, contacto de emergencia y modo de validacion.
- Knowledge base: disponible en `data/private/guesty-conversations/GLAM HOMES
  KNOWLEDGE BASE`.

## Que se copia al exportar la carpeta local

Para una copia interna completa, copiar toda la carpeta `GLAM HOMES`.

Incluye:

- Codigo fuente.
- Documentacion.
- Assets del frontend.
- Exports publicos de propiedades.
- Reports/capturas de QA.
- Knowledge base privada de Guesty, si se copia tambien `data/private/`.
- Transcripts locales, si se copia tambien `transcripts/`.
- Logs locales, si se copia tambien `logs/`.

No asumir que una copia de GitHub incluye datos privados. GitHub debe ser una
version limpia del codigo y la documentacion, no un backup de datos sensibles.

## Que se sube a GitHub

GitHub debe incluir:

- `README.md`
- `.env.example`
- `apps/`
- `docs/`
- `documentacion/`
- `programas/`
- `reports/`
- `data/guesty-property-links.*`
- `data/glam_homes_property_links.sqlite`
- `transcripts/.gitkeep`

GitHub no debe incluir:

- `.env`
- `.cache/`
- `API Keys/`
- `data/private/`
- `data/emergency_contact.json`
- `data/reservation_validation.json`
- `data/voice_config.json`
- `transcripts/*`
- `logs/`
- `__pycache__/`
- `*.pyc`

Estos patrones estan protegidos por `.gitignore`.

## Secretos y configuracion

Crear `.env` local a partir de `.env.example`.

Variables principales:

- `OPENAI_API_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_API_KEY`
- `TWILIO_API_SECRET`
- `TWILIO_PHONE_NUMBER`
- `GUESTY_CLIENT_ID`
- `GUESTY_CLIENT_SECRET`
- `GLAM_DASHBOARD_KEY`
- `GLAM_HUMAN_SUPPORT_PHONE`
- `GLAM_EMERGENCY_CONTACT_PASSWORD`
- `VAPI_API_KEY` si se usa Vapi
- `VAPI_ASSISTANT_ID` si se usa Vapi

Alternativa para Vapi:

- Guardar el archivo privado en `API Keys/vapi keys.rtf`, dentro del proyecto
  local. Esa carpeta esta ignorada por Git.
- O definir `VAPI_KEYS_PATH` con una ruta privada.

Cloudflare:

- El token o credentials file de Cloudflare debe mantenerse privado.
- `apps/voice-agent/cloudflare-tunnel.example.yml` es solo plantilla.
- `run_cloudflare_tunnel.sh` puede usar `CLOUDFLARE_TUNNEL_TOKEN_FILE`.

## Knowledge base de Guesty

La carpeta final esta en:

```text
data/private/guesty-conversations/GLAM HOMES KNOWLEDGE BASE
```

Archivos principales:

- `agent_runtime_best_practices.md`: version compacta para cargar en agentes.
- `use_cases_and_best_practices_final.md`: maestro humano de use cases y buenas
  practicas.
- `quality_review.md`: evaluacion de calidad.
- `property_playbooks.md`: mapa de fricciones por propiedad.
- `anti_patterns.md`: guardrails.
- `case_index.jsonl`: indice estructurado para auditoria/retrieval futuro.

El agente de voz ya carga `agent_runtime_best_practices.md` al iniciar. Esto no
es fine-tuning del modelo; es entrenamiento operativo por instrucciones de
runtime. Guesty sigue siendo la fuente de verdad para precios, disponibilidad,
codigos, Wi-Fi, parking, fees, politicas, direcciones y amenidades actuales.

## Arranque local

Backend y dashboard:

```bash
python3 apps/voice-agent/server.py
```

Stack completo local:

```bash
apps/voice-agent/run_glam_stack.sh
```

Status:

```bash
curl http://127.0.0.1:3000/api/status
curl "http://127.0.0.1:3000/api/guesty/status?live=1"
```

Twilio webhooks:

```bash
python3 apps/voice-agent/configure_twilio_number.py
python3 apps/voice-agent/configure_twilio_number.py --apply
```

El script bloquea cambios sobre numeros de Kim Live terminados en `7532`.

## Verificacion antes de exportar

Ejecutar:

```bash
python3 -m py_compile apps/voice-agent/server.py apps/voice-agent/guesty_client.py apps/voice-agent/tool_bridge.py apps/voice-agent/twilio_realtime_bridge.py
python3 -m json.tool data/guesty-property-links.json >/tmp/glam_property_links_checked.json
git status --short --branch
```

Revisar que no aparezcan secretos staged ni sin trackear para GitHub.

## Notas finales

- La copia local completa puede incluir `data/private/`, `transcripts/` y
  `logs/` si el destino es interno y seguro.
- La version GitHub intencionalmente no incluye esos datos.
- Si otro agente necesita el conocimiento conversacional, copiar
  `data/private/guesty-conversations/GLAM HOMES KNOWLEDGE BASE` o pegar
  `agent_runtime_best_practices.md`.
- El proyecto ya no depende de BIFROST para correr; los documentos de BIFROST
  son referencia historica de implementacion.
