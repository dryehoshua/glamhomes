# GLAM HOMES Orbit / Ai People Toolkit

This folder packages the GLAM HOMES call center project as an internal Orbit /
Ai People reference implementation.

It does not replace the live application runtime. The working app remains in
`apps/voice-agent/`, the property database remains in `data/`, and private
conversation knowledge remains in `data/private/`.

## Purpose

GLAM HOMES demonstrates how Ai People can build a vertical call center agent
that combines:

- real-time voice conversations,
- live property management APIs,
- synchronized calls and SMS,
- human handoff,
- analytics and transcript review,
- conversation-derived operating knowledge.

## Start Here

- `SKILL_CATALOG.md`: reusable skill list and capability map.
- `CONTROL_PANEL_ANALYTICS_GUIDE.md`: human guide for dashboard KPIs, charts,
  inbox, transcripts and operating cadence.
- `EXPORT_MANIFEST.md`: what is internal, what is private, and what is safe for
  GitHub.
- `tools/guesty/README.md`: Guesty as the Ai People live API tool.
- `tools/guesty/tool-manifest.json`: machine-readable tool contract.
- `reports/glam-homes-engineering-report.pdf`: human-readable engineering
  report.

## Runtime Boundary

This folder is documentation and packaging only. It must not be imported by the
production runtime unless a future Ai People orchestration layer explicitly
chooses to do so.

Current runtime sources of truth:

- Voice app: `apps/voice-agent/server.py`
- Twilio bridge: `apps/voice-agent/twilio_realtime_bridge.py`
- Public property database: `data/glam_homes_property_links.sqlite`
- Guesty conversation knowledge base:
  `data/private/guesty-conversations/GLAM HOMES KNOWLEDGE BASE`

## Private Data Boundary

The internal local copy may include private data. GitHub must not include:

- `.env`
- `.cache/`
- `API Keys/`
- `data/private/`
- `transcripts/*`
- `logs/`

These paths are intentionally protected by `.gitignore`.
