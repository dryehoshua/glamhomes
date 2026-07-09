# Guesty Tool For Ai People

Guesty is packaged here as the GLAM HOMES live property-management API tool.
This is a documentation and contract layer for Orbit / Ai People. It does not
create a new runtime and does not change the existing voice agent.

## Runtime Source

- Implementation: `apps/voice-agent/server.py`
- Tool bridge routing: `apps/voice-agent/tool_bridge.py`
- Active Realtime registration: `REALTIME_TOOLS`
- Local property database: `data/glam_homes_property_links.sqlite`

## Tool Scope

Guesty is read-only in this project.

Supported capabilities:

- check Guesty API status,
- search reservations,
- confirm reservations,
- retrieve confirmed stay details,
- retrieve one reservation by ID,
- list listings,
- search available listings,
- inspect listing calendar,
- search active public property links.

Not supported without future approval design:

- creating reservations,
- modifying reservations,
- cancelling reservations,
- charging payments,
- issuing refunds,
- changing fees,
- approving events or policy exceptions.

## Functions

| Function | Purpose | Risk Level |
| --- | --- | --- |
| `guesty_status` | Check API configuration and reachability. | Low |
| `guesty_search_reservation` | Search reservations by code, phone, email or name. | Medium |
| `guesty_confirm_reservation` | Confirm a reservation with validation/fuzzy safeguards. | Medium |
| `guesty_confirmed_stay_details` | Retrieve address, check-in, access and stay details after validation. | High |
| `guesty_get_reservation` | Retrieve one reservation by internal ID. | Medium |
| `guesty_list_listings` | List Guesty listings. | Low |
| `guesty_available_listings` | Search availability by dates and guest count. | Medium |
| `guesty_listing_calendar` | Retrieve minified listing calendar and nightly pricing. | Medium |
| `glam_search_public_property_links` | Search active public Glam Homes property links. | Low |

## Safety Rules

- Guesty is the source of truth for current reservation and property facts.
- Historical conversation knowledge is only pattern memory.
- Never invent prices, codes, Wi-Fi, parking, exact addresses, fees, amenity
  state or policy exceptions.
- Sensitive stay data requires reservation validation.
- Missing Guesty fields should trigger human escalation.
- Money, refunds, cancellations, events, parties, pets, smoking, early check-in
  and late checkout require human confirmation.

## Related Skills

- Live Guesty API Operations
- Guesty Reservation Confirmation
- Confirmed Stay Details
- Property Link Routing
- Conversation Knowledge Base
- Security, Privacy And Export Hygiene
