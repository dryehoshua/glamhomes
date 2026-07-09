# GLAM HOMES Control Panel Analytics Guide

This guide explains how a human operator should use the protected GLAM HOMES
dashboard. It documents the analytics, charts, filters and call inbox without
changing any runtime behavior.

## Purpose

The control panel is the operating console for the AI call center. It is used to:

- review call volume and booking demand;
- identify support, check-in, policy and handoff patterns;
- audit transcripts and tool actions;
- find callers by phone, name or keyword;
- decide what needs human follow-up, data cleanup or knowledge-base improvement.

## Access Model

The Calls and Analytics view is protected because it can expose phone numbers,
literal transcripts and operational context. Operators should unlock it only for
supervision, support, quality review and follow-up.

Do not paste private transcript data into public tools or external prompts.

## Date And Search Scope

Every metric is scoped by the selected filters:

- `Today`: same-day operating view.
- `7 days`: default weekly operating view.
- `30 days`: monthly management view.
- `All`: historical baseline across stored local conversations.
- `Custom`: exact incident, campaign, test or shift window.
- `Phone number`: narrows results to one caller history.
- `Name or keyword`: narrows results to a person, property, issue or concept.

Never compare dashboard numbers without confirming the same date scope.

## KPI Definitions

| KPI | Definition | What To Do With It |
| --- | --- | --- |
| Total calls | Count of calls in the selected scope. | Use as the denominator for every rate and workload discussion. |
| Prospects | Calls where booking intent is detected. | Prioritize sales follow-up, property routing and booking scripts. |
| Transcript coverage | Percent of calls with saved transcript data. | If low, inspect audio/transcript capture before trusting analytics. |
| Human handoffs | Logged escalation events. | Review whether handoff was correct, avoidable or under-staffed. |
| First call resolution | Eligible calls resolved on first contact. | If low, inspect repeated subtopics and missing data. |
| Avg resolution | Time from start to end or transfer. | Use to detect friction and long support flows. |
| Repeat contact | Repeat callers and same-subtopic callbacks. | Fix unresolved loops by property, policy or data source. |
| Issues detected | Issue signals and multi-issue call load. | Identify complex conversations that need better playbooks. |
| Influencers | VIP or influencer caller signals. | Route high-touch opportunities to the right human owner. |
| Needs attention | Calls marked for review; detail includes praise count. | Work the quality queue before routine monitoring. |
| Missed / abandoned | Failed/no-answer/short unresolved call risk. | Review telephony, staffing and callback needs. |
| SMS sent | Guest and advisor SMS actions. | Confirm the voice-to-SMS workflow is being used. |
| Unique callers | Distinct caller phone numbers. | Compare to total calls to find repeated contact or unresolved loops. |
| Tool actions | Guesty, Twilio, SQLite or other tool events. | Healthy tool usage means the agent is grounding answers in systems of truth. |
| Guest turns | Guest-side transcript messages. | Measures customer effort and conversation depth. |
| Avg messages | Total messages divided by calls. | High values may indicate complexity; low values may indicate failed or brief calls. |

## Priority Cards

The deployed Analytics module includes four priority cards:

| Card | Meaning | Action |
| --- | --- | --- |
| Priority queue | Calls needing review. | Open red conversations first. |
| Repeat issue | Same-subtopic callbacks. | Fix the repeated source issue. |
| VIP pipeline | Influencer or VIP signals. | Route to premium human follow-up. |
| Quality signal | Praise or positive guest sentiment. | Preserve or coach the successful behavior. |

## Charts

### Topics By Call Volume

This bar chart counts calls where topic keywords appear in the transcript.

Use it to identify the highest-volume call themes: booking intent, support,
check-in/access, policy questions and other recurring issues. Tall bars should
produce action: update a script, improve property data, adjust SMS templates or
create a new use case.

### Pipeline Mix

This doughnut chart shows the relative mix of:

- prospects;
- support calls;
- human handoffs;
- other calls.

Use it with `Total calls`. The doughnut explains mix, not absolute volume.

### Calls By Day And Hour

This bubble/heatmap chart shows when calls happen by weekday and hour. Use it to
decide staffing windows, campaign timing, and when the system needs closer human
coverage.

### Subtopics And Repeats

This operational table shows recurring issue categories, call counts, repeated
callbacks, escalated counts and timing where available. It is the best table for
root-cause work.

### Escalations By Reason

This table groups human handoffs by reason category. Use it to separate healthy
handoffs from avoidable handoffs caused by missing data, unclear policy or weak
automation.

## Frequent Concepts

The frequent concepts panel combines topic chips with high-frequency transcript
terms. It is useful for discovering repeated issues that may not deserve a
formal topic yet.

Examples of useful patterns:

- property names mentioned repeatedly;
- access, code, address, Wi-Fi or check-in terms;
- refund, party, pet, deposit or policy terms;
- platform or booking-channel confusion.

## Conversation Inbox

The inbox groups call activity by caller/thread. It lets a human review a caller
as a continuous history, not only as isolated call records.

Sorting modes:

- `Recent`: newest caller history first.
- `Relevant`: best match for current search/filter.
- `Most interaction`: deepest or most complex threads first.
- `Least interaction`: short, abandoned or low-content threads first.

Recommended triage:

1. Start with `Today` or `7 days`.
2. Sort by `Most interaction` to find complex cases.
3. Search top terms from the analytics panel.
4. Open threads with handoffs, failed transcripts or repeated issues.
5. Decide whether to update property data, scripts, SMS wording or human follow-up.

## Transcript Panel

The transcript panel is the quality audit surface.

Review:

- guest turns: what the caller actually asked;
- concierge turns: what the AI answered;
- tool turns: whether Guesty, Twilio or SQLite were used before factual claims;
- system turns: protected states, local-only warnings or unavailable states;
- timestamps and event kinds: sequence of actions, SMS and handoffs.

A model conversation should validate live facts, avoid unsupported promises, send
durable SMS when useful and escalate policy or safety risk.

## Daily Operating Cadence

| Cadence | Review | Decision |
| --- | --- | --- |
| Start of day | Yesterday/today volume, unresolved handoffs, transcript coverage. | Who needs human follow-up first? |
| Midday | Prospect calls and property-link activity. | Where should sales attention go? |
| End of day | Top concepts, long threads and handoff rate. | What process or knowledge update is needed? |
| Weekly | 7-day topics, support share and coverage. | Which property or workflow creates repeat work? |
| Monthly | 30-day pipeline mix and handoff trend. | What should be automated, staffed or fixed next? |

## Trigger Matrix

| Signal | Interpretation | Action |
| --- | --- | --- |
| Total calls rises | More demand or campaign effect. | Check staffing, speed and prospect handling. |
| Prospects rise | More booking opportunity. | Review property recommendations and follow-up. |
| Support rises | More operational friction. | Find the recurring issue and fix the source. |
| Transcript coverage drops | Observability problem. | Check Twilio, media stream and transcript capture. |
| Tool actions drop | Agent may be answering from memory. | Audit tool availability and prompt behavior. |
| Handoffs spike | More risk, missing data or policy pressure. | Classify handoffs and improve the escalation playbook. |
| Average messages rises | Conversations are taking longer. | Review long threads and eliminate repeated blockers. |
