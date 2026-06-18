# Dashboard Call Analytics Incident Log

## 2026-06-18 - Conversation inbox hidden and analytics over-scrolling

Symptoms:
- Conversation list appeared empty even though transcript files still existed under `transcripts/`.
- Calls & Analytics required excessive vertical scrolling before the inbox was reachable.
- Operators needed direct date/time and phone filters to locate a specific call.

Root causes:
- The conversation thread endpoint only returned grouped calls that had a populated caller phone number. Twilio transcripts with missing or incomplete `from` metadata could be excluded from the inbox even when the transcript existed.
- The analytics panel rendered eight KPI cards plus charts and keywords without a strict desktop height budget, which pushed the conversation inbox too far down/aside.
- The UI only exposed coarse date filters and a generic text search instead of explicit phone and time controls.

Prevention:
- Do not hide stored Twilio conversations solely because phone metadata is missing. Fall back to CallSid threads.
- Keep the Calls & Analytics desktop view height-bounded, with internal scrolling inside analytics rather than long page scrolling.
- Preserve explicit filters for date, time, phone number, and keyword/name whenever changing the conversation inbox.
