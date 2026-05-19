# Mapa de links de propiedades

El concierge debe compartir links del booking site publico, no links internos de
Guesty.

Fuente publica:

```text
https://theglamhomes.guestybookings.com/en/properties?minOccupancy=1
```

Export actual:

- Total visible publico: 55 propiedades.
- JSON: `data/guesty-property-links.json`
- CSV: `data/guesty-property-links.csv`
- Markdown: `data/guesty-property-links.md`

Actualizar:

```bash
python3 apps/voice-agent/export_property_links.py
```

Uso esperado:

- Si el cliente esta en llamada telefonica: enviar el link por SMS.
- Si el cliente esta en chat web: compartir el link directo en el chat.
- Si el cliente pide opciones por fechas: consultar disponibilidad en Guesty
  antes de recomendar.
- Si solo pide ver una propiedad especifica: usar este mapa publico.

Nota importante: `data/guesty-property-links.csv` contiene tambien `sms_text_es`
con un texto corto listo para enviar.
