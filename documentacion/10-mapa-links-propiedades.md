# Mapa de links de propiedades

El concierge debe compartir links del booking site publico, no links internos de
Guesty.

Fuente publica:

```text
https://theglamhomes.guestybookings.com/en/properties?minOccupancy=1
```

Export actual:

- Total visible publico: 54 propiedades.
- JSON: `data/guesty-property-links.json`
- CSV: `data/guesty-property-links.csv`
- Markdown: `data/guesty-property-links.md`
- SQLite operativo: `data/glam_homes_property_links.sqlite`

Actualizar:

```bash
python3 apps/voice-agent/export_property_links.py
```

Uso esperado:

- Por defecto se comparte el link directo de Glam Homes.
- Si el cliente pide Airbnb, Booking o VRBO, compartir ese link solo si existe
  para la propiedad publica activa.
- Si el cliente esta en llamada telefonica: enviar el link por SMS con Twilio.
- Si el cliente esta en chat web: compartir el link directo en el chat; el
  preview lo genera la app/navegador desde OpenGraph de la pagina.
- Si el cliente pide opciones por fechas: consultar disponibilidad en Guesty
  antes de recomendar.
- Si hay fechas y huespedes, los links directos de Glam Homes se pueden
  precargar con `checkIn=YYYY-MM-DD`, `checkOut=YYYY-MM-DD` y
  `minOccupancy=N`.
- Si solo pide ver una propiedad especifica: usar este mapa publico.

Conteo de links externos en el export actual:

- Airbnb: 52
- Booking.com: 48
- VRBO/HomeAway: 41
- Google Vacation Rentals: 23

El bridge operativo usa `apps/voice-agent/tool_bridge.py` y las herramientas
`glam_search_public_property_links` y `twilio_send_property_link_sms`.
