# GLAM HOMES Skill Catalog

This catalog describes the reusable operating skills proven inside the GLAM
HOMES call center project. These are product skills for Orbit / Ai People, not
Codex-installed skills.

## 1. Call Center Concierge

- Purpose: handle booking, support, pre-arrival, in-stay and post-stay calls.
- Inputs: caller speech, caller phone number, optional reservation code, guest
  intent.
- Outputs: concise spoken answer, tool call, SMS, human handoff, transcript.
- Guardrail: one useful question at a time; never invent facts.

## 2. Live Guesty API Operations

- Purpose: use Guesty as the live source of truth for reservations, listings,
  availability and stay details.
- Inputs: confirmation code, guest details, listing ID, dates, guest count.
- Outputs: verified reservation, listing, calendar, availability or stay data.
- Guardrail: read-only Guesty operations unless future approvals are designed.

## 3. Guesty Reservation Confirmation

- Purpose: confirm whether a reservation exists before sharing details.
- Inputs: confirmation code; name/email/phone when needed.
- Outputs: safe reservation summary.
- Guardrail: fuzzy phone transcription requires extra validation.

## 4. Confirmed Stay Details

- Purpose: retrieve and share exact stay facts after reservation validation.
- Inputs: confirmation code and validation context.
- Outputs: address, check-in information, door code, Wi-Fi/StayFi, amenities,
  missing-field diagnostics.
- Guardrail: if Guesty lacks a field, escalate instead of inventing.

## 5. Property Link Routing

- Purpose: recommend and send active public property links.
- Inputs: property query, city, guest count, platform, dates.
- Outputs: Glam Homes direct link, Airbnb, Booking or VRBO link when available.
- Guardrail: only use active public records from the local property database.

## 6. Twilio Calls And SMS Sync

- Purpose: keep voice conversations and SMS follow-ups synchronized.
- Inputs: active call context, caller phone, selected property or stay details.
- Outputs: Twilio SMS, transcript event, operational audit trail.
- Guardrail: offer SMS before sending sensitive or long information.

## 7. Human Handoff And Transfer

- Purpose: route issues to a human advisor when automation should stop.
- Inputs: reason, summary, urgency, reservation, caller number.
- Outputs: advisor SMS, optional caller confirmation, live Twilio transfer.
- Guardrail: hand off immediately for human requests, blocked access, critical
  maintenance, policy exceptions, refunds, payments and upset guests.

## 8. Call Inbox And Analytics

- Purpose: review conversations by caller, not isolated CallSid.
- Inputs: transcript files, call metadata, date filters, search terms.
- Outputs: inbox threads, transcript view, KPIs, charts and relevance sorting.
- Guardrail: dashboard data is admin-only and protected by access key.

## 9. Conversation Knowledge Base

- Purpose: convert historical Guesty conversations into reusable best practices.
- Inputs: raw Guesty conversation exports and post/message data.
- Outputs: use cases, anti-patterns, model cases, property playbooks and runtime
  best practices.
- Guardrail: historical conversations are pattern memory, not current facts.

## 10. Security, Privacy And Export Hygiene

- Purpose: keep code, docs, secrets and private data clearly separated.
- Inputs: project tree, `.gitignore`, `.env.example`, private folders.
- Outputs: export manifest, GitHub-safe boundary, internal-copy guidance.
- Guardrail: never commit `.env`, API keys, raw conversations, transcripts or
  logs.

## Recommended Skill Loading Order

1. Security, Privacy And Export Hygiene
2. Live Guesty API Operations
3. Call Center Concierge
4. Twilio Calls And SMS Sync
5. Human Handoff And Transfer
6. Call Inbox And Analytics
7. Conversation Knowledge Base
