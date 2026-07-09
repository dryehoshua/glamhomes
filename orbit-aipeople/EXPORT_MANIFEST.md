# GLAM HOMES Export Manifest

This manifest defines how the GLAM HOMES project should be copied, shared and
published.

## Internal Complete Copy

Copy the full `GLAM HOMES` folder when the destination is trusted and internal.

The complete local copy may include:

- source code and docs,
- public property exports,
- reports and QA screenshots,
- private Guesty conversation exports,
- generated knowledge base,
- transcripts,
- logs,
- local secret placeholders or private key folders.

Internal recipients must understand that `data/private/`, `transcripts/`,
`logs/`, `.env`, `.cache/` and `API Keys/` contain operational or sensitive
materials.

## GitHub-Safe Copy

GitHub must include code, public docs and public exports only.

Safe for GitHub:

- `README.md`
- `.env.example`
- `apps/`
- `data/guesty-property-links.*`
- `data/glam_homes_property_links.sqlite`
- `docs/`
- `documentacion/`
- `orbit-aipeople/`
- `programas/`
- `reports/`
- `transcripts/.gitkeep`

Not safe for GitHub:

- `.env`
- `.cache/`
- `API Keys/`
- `data/private/`
- `data/emergency_contact.json`
- `data/reservation_validation.json`
- `data/voice_config.json`
- `logs/`
- `transcripts/*`
- `__pycache__/`
- `*.pyc`

## Runtime Integrity Rule

The Orbit / Ai People packaging layer must not change runtime behavior. The
application should continue to run from:

```bash
python3 apps/voice-agent/server.py
```

The full stack should continue to run from:

```bash
apps/voice-agent/run_glam_stack.sh
```

## Validation Checklist

Before sharing a copy:

```bash
git status --short --branch
python3 -m py_compile apps/voice-agent/server.py apps/voice-agent/guesty_client.py apps/voice-agent/tool_bridge.py apps/voice-agent/twilio_realtime_bridge.py
sqlite3 data/glam_homes_property_links.sqlite 'PRAGMA integrity_check;'
python3 -m json.tool data/guesty-property-links.json >/tmp/glam_property_links_checked.json
```

Expected project facts:

- 54 active public properties in SQLite.
- 24,072 structured Guesty conversation cases.
- `knowledge_base_loaded=True` when the voice server imports the runtime best
  practices file.
- Guesty/Twilio/Vapi show configured after `.env` is loaded in the local runtime.
