# GLAM HOMES Call Center System

## Executive Engineering Report For Orbit / Ai People

GLAM HOMES is a production-shaped reference implementation for an AI-enabled
hospitality call center. It proves that an agent can operate across live voice,
live property-management APIs, SMS follow-up, human escalation, dashboard
analytics and conversation-derived knowledge without becoming a static FAQ bot.

This report is based on live inspection of `https://glamhomes.aipeople.app`,
desktop/mobile screenshots, the downloaded deployed front-end HTML, local runtime
code, database checks and knowledge-base validation.

## Core Thesis

The strategic value is not simply "an AI answers the phone." The value is that
the call center becomes an orchestrated operating layer:

- live systems provide truth,
- voice captures intent,
- SMS carries durable actions,
- human handoff protects risk,
- analytics turns conversations into management visibility,
- historical conversations become reusable operating policy.

## What The System Solves

The GLAM HOMES operation receives high-friction, high-value guest and prospect
requests: booking intent, pricing questions, property fit, check-in, access,
Wi-Fi, events, refunds, maintenance and human support. These requests cannot be
handled safely by generic scripts because the answer often depends on live data,
property-specific rules or human approval.

The project solves this by splitting work into three layers:

1. The AI handles conversation, qualification and verified answers.
2. Guesty and SQLite provide live operational data.
3. Humans handle exceptions, approvals and urgent support.

## Strategic Capabilities Demonstrated

1. Call center automation with real-time voice.
2. Live Guesty API tool use.
3. Reservation confirmation and sensitive-data gating.
4. Public property-link routing.
5. Twilio voice and SMS synchronization.
6. Human handoff and live transfer.
7. Protected analytics dashboard.
8. Conversation knowledge base derived from historical Guesty messages.
9. Export hygiene for private datasets and GitHub-safe code.

## Operating Architecture

The system uses OpenAI Realtime for voice reasoning and tool calls, Twilio for
calls/SMS, Guesty for live reservation and listing data, SQLite for public
property links, and a local dashboard for review and analytics.

The runtime sources are:

- `apps/voice-agent/server.py`
- `apps/voice-agent/twilio_realtime_bridge.py`
- `apps/voice-agent/tool_bridge.py`
- `apps/voice-agent/public/index.html`

The private intelligence layer is:

- `data/private/guesty-conversations/GLAM HOMES KNOWLEDGE BASE`

## Guesty Tool Model

Guesty is treated as a controlled live API tool. It is read-only in this
implementation and is responsible for current facts: reservations, listings,
availability, calendars, check-in/stay details and missing-field diagnostics.

Sensitive data is protected by validation. Money, events, refunds,
cancellations, late checkout, early check-in, pets, smoking and policy
exceptions require human confirmation.

## Call And SMS Model

The call center treats voice and SMS as one workflow. The agent can speak with
the guest, then send a durable SMS with a property link, stay detail, check-in
instruction, Wi-Fi/StayFi information or human handoff confirmation. Each action
can be reflected in transcripts for review.

## Analytics Model

The deployed front end separates Analytics and Calls. Analytics is a protected
management scorecard; Calls is a protected conversation-memory and transcript
review surface. Analytics are admin-only and should not be disclosed over normal
guest calls.

The control panel is documented as a human operating surface, not only as a
developer artifact. The report defines each metric and chart:

- Total calls: volume in the selected scope.
- Prospects: calls with booking intent.
- Transcript coverage: share of calls with saved transcript evidence.
- Human handoffs: escalation events logged from the transcript/tool stream.
- First call resolution: eligible calls resolved on first contact.
- Average resolution: start-to-end or transfer timing.
- Repeat contact: repeat callers and same-subtopic callbacks.
- Issues detected: issue and multi-issue call load.
- Influencers/VIP pipeline: high-touch caller signals.
- Needs attention: review queue and praise count.
- Missed/abandoned: telephony or short unresolved call risk.
- SMS sent: guest/advisor follow-through volume.
- Unique callers: distinct phone numbers represented in the scope.
- Tool actions: Guesty, Twilio, SQLite or other grounded actions.
- Guest turns and average messages: conversation depth and customer effort.
- Priority queue, Repeat issue, VIP pipeline and Quality signal: daily
  management triage cards.
- Topics by call volume: recurring demand and support themes.
- Pipeline mix: prospect, support, handoff and other call distribution.
- Calls by day and hour: call-timing heatmap for staffing and campaign review.
- Subtopics and repeats: root-cause table for unresolved loops.
- Escalations by reason: handoff categories requiring policy/staffing review.
- Frequent concepts: high-frequency terms that identify repeating issues.
- Conversation Inbox: caller-level memory for audit and follow-up.
- Transcript panel: literal quality review for guest, concierge, tool and
  system events.

The operating cadence is daily and weekly: review volume, prospects, coverage,
handoffs, top concepts and long threads; then decide whether to update property
data, SMS wording, knowledge base, staffing or escalation policy.

## Knowledge Base Model

The historical Guesty export was synthesized into a knowledge base:

- 24,072 structured real conversation cases.
- 22,677 useful/reference cases estimated.
- 1,395 low-value/noise cases estimated.
- 13 high-frequency intent categories.

The agent loads the compact runtime best-practices file, not the raw
conversation corpus. The raw export remains private.

## Orbit / Ai People Relevance

GLAM HOMES is a reference model for vertical AI systems that require live tools,
safe escalation and management visibility. The reusable pattern is:

1. Define the business-critical live API.
2. Wrap it as a controlled tool.
3. Gate sensitive data and risky actions.
4. Synchronize communication channels.
5. Use dashboard analytics to supervise the operation.
6. Convert historical conversations into operating policy.

This is directly reusable for other Orbit / Ai People verticals.

## Engineering Finding

The live deployed front end is ahead of the local checked `public/index.html` in
some dashboard details. Production exposes separate `Analytics` and `Calls` tabs
and a richer analytics module. The recommendation is to reconcile the deployed
front-end artifact back into source control before the next production release.
