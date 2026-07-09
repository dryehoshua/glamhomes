# GLAM HOMES Data

This folder contains public operational exports used by the GLAM HOMES voice
agent and dashboard.

Private datasets live under `data/private/` and must not be committed to GitHub.

## Public Property Link Database

Primary database:

```text
data/glam_homes_property_links.sqlite
```

Tables:

- `public_properties`: one row per active public Glam Homes property.
- `property_channel_links`: platform-specific links by listing ID.

Current audited state:

- 54 public properties.
- 54 active public properties.
- SQLite integrity check: `ok`.

The database is used by:

- `glam_search_public_property_links`
- `twilio_send_property_link_sms`
- dashboard/property link search flows

## Public Exports

- `data/guesty-property-links.json`
- `data/guesty-property-links.csv`
- `data/guesty-property-links.md`

These exports mirror the active public booking site inventory and are safe to
keep in GitHub because they contain public listing/link data.

## Refresh Command

```bash
python3 apps/voice-agent/export_property_links.py
```

The refresh command reads the public Glam Homes booking site and updates the
JSON, CSV, Markdown and SQLite artifacts.

## Validation

```bash
sqlite3 data/glam_homes_property_links.sqlite 'PRAGMA integrity_check;'
sqlite3 data/glam_homes_property_links.sqlite 'SELECT COUNT(*), SUM(active_public) FROM public_properties;'
python3 -m json.tool data/guesty-property-links.json >/tmp/glam_property_links_checked.json
```

Expected:

- `PRAGMA integrity_check` returns `ok`.
- count and active count match.
- JSON validates without errors.

## Privacy Boundary

Do not commit:

- `data/private/`
- `data/emergency_contact.json`
- `data/reservation_validation.json`
- `data/voice_config.json`

Those files are intentionally ignored by `.gitignore`.
