#!/usr/bin/env python3
"""
Twilio Media Streams bridge for GLAM HOMES Concierge.

This process receives the Twilio <Stream> WebSocket and pipes audio to OpenAI
Realtime. It also lets the model call the same read-only Guesty tools used by
the browser demo and persists call transcripts under ./transcripts.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
from typing import Any

import websockets

import server as glam


glam.load_dotenv()
HOST = "127.0.0.1"
PORT = int(os.environ.get("TWILIO_MEDIA_PORT", "8877"))


def realtime_ws_url() -> str:
    api_base = os.environ.get("OPENAI_API_BASE", glam.OPENAI_API_BASE).rstrip("/")
    if api_base.startswith("https://"):
        api_base = "wss://" + api_base.removeprefix("https://")
    elif api_base.startswith("http://"):
        api_base = "ws://" + api_base.removeprefix("http://")
    model = os.environ.get("OPENAI_REALTIME_MODEL", glam.REALTIME_MODEL)
    return f"{api_base}/realtime?model={model}"


def safety_identifier(call_sid: str) -> str:
    digest = hashlib.sha256(f"glam-homes-twilio:{call_sid}".encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)[:32].decode("ascii")


def session_update(call_sid: str, caller: str, called: str, caller_context: dict[str, Any] | None = None) -> dict[str, Any]:
    voice = glam.active_realtime_voice()
    if caller_context is None:
        caller_context_instruction = "\nCaller ID lookup: pending. Do not wait for it before greeting the caller."
    elif caller_context.get("matched"):
        reservation = caller_context.get("reservation") if isinstance(caller_context.get("reservation"), dict) else {}
        guest_name = str(caller_context.get("guest_name") or "").strip()
        caller_context_instruction = (
            "\nCaller ID lookup: matched a Guesty reservation for this caller phone."
            f"\nRegistered guest name: {guest_name or 'unknown'}."
            f"\nProperty on file: {reservation.get('listing_title') or 'unknown'}."
            "\nGreet the caller by the registered guest first name if available, but do not reveal the stored confirmation code and still validate before sharing sensitive stay details."
            "\nIf the guest later provides a reservation code, repeat it back and ask them to confirm it before using Guesty tools with confirmation_code_confirmed=true."
            "\nWhen validating that confirmed code, you may pass the caller phone as guest_phone because Caller ID matched the Guesty guest phone."
        )
    else:
        caller_context_instruction = "\nCaller ID lookup: no matching Guesty reservation was found for the caller phone."
    instructions = (
        glam.AGENT_INSTRUCTIONS
        + "\n\nCurrent channel: Twilio Media Streams phone call."
        + f"\nCallSid: {call_sid}. Caller: {caller or 'unknown'}. To: {called or os.environ.get('TWILIO_PHONE_NUMBER', glam.TWILIO_PHONE_NUMBER)}."
        + caller_context_instruction
        + "\nUse Guesty tools when you need live reservation, property, or availability data."
        + "\nUse the public property links bridge for shareable links. Always offer SMS delivery for useful links, and send accepted links with twilio_send_property_link_sms."
        + "\nFor validated stay details such as address, door code, check-in instructions, or Wi-Fi, always offer SMS delivery and use twilio_send_stay_details_sms when accepted."
        + f"\n{glam.IMPORTANT_SMS_OFFER_RULE}"
        + "\nFor any matter requiring human attention, including special services, towels, housekeeping, maintenance, access issues, complaints, policy exceptions, or a human request, tell the caller you will notify a human advisor now and use twilio_send_human_handoff_sms with caller number, reservation code if known, and a concise problem summary."
        + "\nIf the caller specifically asks to transfer the call to a human, use twilio_transfer_call_to_human."
    )
    return {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "model": os.environ.get("OPENAI_REALTIME_MODEL", glam.REALTIME_MODEL),
            "output_modalities": ["audio"],
            "instructions": instructions,
            "tools": glam.REALTIME_TOOLS,
            "tool_choice": "auto",
            "audio": {
                "input": {
                    "format": {"type": "audio/pcmu"},
                    "transcription": {
                        "model": os.environ.get("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe"),
                        "language": os.environ.get("OPENAI_TRANSCRIBE_LANGUAGE", "en"),
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.45,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 650,
                    },
                },
                "output": {
                    "format": {"type": "audio/pcmu"},
                    "voice": voice,
                    "speed": 1.0,
                },
            },
        },
    }


def create_user_text(text: str) -> dict[str, Any]:
    return {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": text}],
        },
    }


def create_response(instructions: str) -> dict[str, Any]:
    return {
        "type": "response.create",
        "response": {
            "output_modalities": ["audio"],
            "instructions": instructions,
        },
    }


async def run_function_call(openai_ws: websockets.ClientConnection, call_sid: str, caller: str, called: str, item: dict[str, Any]) -> None:
    name = str(item.get("name") or "")
    call_id = str(item.get("call_id") or item.get("id") or "")
    try:
        arguments = json.loads(item.get("arguments") or "{}")
    except json.JSONDecodeError:
        arguments = {}

    result = glam.run_guesty_tool(name, arguments, context={"call_sid": call_sid, "caller": caller, "called": called})
    glam.append_transcript_event(
        call_sid,
        "Tool Bridge",
        f"{name} -> {json.dumps({'ok': result.get('ok'), 'arguments': arguments}, ensure_ascii=False)}",
        channel="twilio",
        kind="tool",
        metadata={"tool": name, "call_id": call_id, "bridge": result.get("bridge", "")},
    )
    await openai_ws.send(
        json.dumps(
            {
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(result, ensure_ascii=False),
                },
            }
        )
    )
    await openai_ws.send(
        json.dumps(
            create_response(
                "Use the tool result to answer by phone. Keep it brief, natural, and do not reveal sensitive data without validation."
            ),
            ensure_ascii=False,
        )
    )


async def handle_media_stream_openai(twilio_ws: websockets.ServerConnection) -> None:
    api_key = glam.openai_api_key()
    if not api_key:
        await twilio_ws.close(code=1011, reason="Missing OPENAI_API_KEY")
        return

    stream_sid = ""
    call_sid = "twilio-pending"
    caller = ""
    called = ""
    latest_media_timestamp = 0
    response_start_timestamp_twilio: int | None = None
    last_assistant_item: str | None = None
    mark_queue: list[str] = []

    async def append_call_event(speaker: str, text: str, *, kind: str = "message", metadata: dict[str, Any] | None = None) -> None:
        glam.append_transcript_event(call_sid, speaker, text, channel="twilio", kind=kind, metadata=metadata or {})

    async with websockets.connect(
        realtime_ws_url(),
        additional_headers={
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Safety-Identifier": safety_identifier(call_sid),
        },
        ping_interval=20,
        ping_timeout=20,
    ) as openai_ws:

        async def send_mark() -> None:
            if not stream_sid:
                return
            mark_name = f"gh-{len(mark_queue) + 1}"
            await twilio_ws.send(json.dumps({"event": "mark", "streamSid": stream_sid, "mark": {"name": mark_name}}))
            mark_queue.append(mark_name)

        async def truncate_if_needed() -> None:
            nonlocal response_start_timestamp_twilio, last_assistant_item, mark_queue
            if response_start_timestamp_twilio is None or not last_assistant_item:
                return
            elapsed = max(0, latest_media_timestamp - response_start_timestamp_twilio)
            await openai_ws.send(
                json.dumps(
                    {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed,
                    }
                )
            )
            if stream_sid:
                await twilio_ws.send(json.dumps({"event": "clear", "streamSid": stream_sid}))
            mark_queue.clear()
            response_start_timestamp_twilio = None
            last_assistant_item = None

        async def receive_from_twilio() -> None:
            nonlocal stream_sid, call_sid, caller, called, latest_media_timestamp

            async def lookup_and_send_caller_context(start_call_sid: str, start_caller: str, start_called: str) -> None:
                timeout_seconds = float(os.environ.get("GLAM_CALLER_LOOKUP_TIMEOUT_SECONDS", "4"))
                try:
                    context = await asyncio.wait_for(
                        asyncio.to_thread(glam.guesty_caller_reservation_context, start_caller),
                        timeout=timeout_seconds,
                    )
                except asyncio.TimeoutError:
                    context = {"ok": False, "matched": False, "reason": "caller_id_lookup_timeout"}
                except Exception as exc:
                    context = {"ok": False, "matched": False, "reason": "caller_id_lookup_failed", "error": str(exc)}
                try:
                    await openai_ws.send(json.dumps(session_update(start_call_sid, start_caller, start_called, context), ensure_ascii=False))
                    await append_call_event(
                        "System",
                        "Caller ID lookup completed.",
                        kind="caller_id_lookup",
                        metadata=context,
                    )
                except Exception:
                    return

            async for raw_message in twilio_ws:
                data = json.loads(raw_message)
                event = data.get("event")
                if event == "start":
                    start = data.get("start") or {}
                    stream_sid = start.get("streamSid") or data.get("streamSid") or ""
                    call_sid = start.get("callSid") or call_sid
                    custom = start.get("customParameters") or {}
                    call_sid = custom.get("callSid") or call_sid
                    caller = custom.get("from") or caller
                    called = custom.get("to") or called
                    await openai_ws.send(json.dumps(session_update(call_sid, caller, called, None), ensure_ascii=False))
                    asyncio.create_task(lookup_and_send_caller_context(call_sid, caller, called))
                    await openai_ws.send(
                        json.dumps(
                            create_user_text(
                                "Answer this inbound call as GLAM HOMES CONCIERGE. Greet in English by default, ask how you can help, and be ready to use Guesty and property-link tools."
                            ),
                            ensure_ascii=False,
                        )
                    )
                    await openai_ws.send(json.dumps(create_response("Initial phone greeting in English, premium, brief, and natural."), ensure_ascii=False))
                    await append_call_event(
                        "System",
                        "Call connected to OpenAI Realtime.",
                        kind="call_connected",
                        metadata={"stream_sid": stream_sid, "from": caller, "to": called, "caller_context": {"status": "pending"}},
                    )
                elif event == "media":
                    media = data.get("media") or {}
                    latest_media_timestamp = int(media.get("timestamp") or latest_media_timestamp or 0)
                    payload = media.get("payload")
                    if payload:
                        await openai_ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": payload}))
                elif event == "mark":
                    if mark_queue:
                        mark_queue.pop(0)
                elif event == "stop":
                    await append_call_event("System", "Twilio closed the audio stream.", kind="call_stop")
                    await openai_ws.close()
                    break

        async def receive_from_openai() -> None:
            nonlocal response_start_timestamp_twilio, last_assistant_item
            async for raw_message in openai_ws:
                event = json.loads(raw_message)
                event_type = event.get("type")

                if event_type in {"response.output_audio.delta", "response.audio.delta"} and event.get("delta") and stream_sid:
                    await twilio_ws.send(
                        json.dumps(
                            {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {"payload": event["delta"]},
                            }
                        )
                    )
                    if response_start_timestamp_twilio is None:
                        response_start_timestamp_twilio = latest_media_timestamp
                    last_assistant_item = event.get("item_id") or last_assistant_item
                    await send_mark()

                elif event_type == "input_audio_buffer.speech_started":
                    await truncate_if_needed()

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = str(event.get("transcript") or "").strip()
                    if transcript:
                        await append_call_event("Guest", transcript, metadata={"item_id": event.get("item_id")})

                elif event_type in {"response.output_audio_transcript.done", "response.output_text.done"}:
                    transcript = str(event.get("transcript") or event.get("text") or "").strip()
                    if transcript:
                        await append_call_event("Concierge", transcript, metadata={"item_id": event.get("item_id")})

                elif event_type == "response.done":
                    output = ((event.get("response") or {}).get("output") or [])
                    calls = [item for item in output if item.get("type") == "function_call"]
                    for item in calls:
                        await run_function_call(openai_ws, call_sid, caller, called, item)

                elif event_type == "error":
                    detail = (event.get("error") or {}).get("message") or json.dumps(event.get("error") or {}, ensure_ascii=False)
                    await append_call_event("System", f"OpenAI Realtime error: {detail}", kind="error")

        await asyncio.gather(receive_from_twilio(), receive_from_openai())


async def handle_media_stream_vapi(twilio_ws: websockets.ServerConnection) -> None:
    if not glam.vapi_configured():
        await twilio_ws.close(code=1011, reason="Missing Vapi configuration")
        return

    stream_sid = ""
    call_sid = "twilio-vapi-pending"
    caller = ""
    called = ""
    vapi_ws: websockets.ClientConnection | None = None
    receive_vapi_task: asyncio.Task | None = None

    async def append_call_event(speaker: str, text: str, *, kind: str = "message", metadata: dict[str, Any] | None = None) -> None:
        glam.append_transcript_event(call_sid, speaker, text, channel="twilio", kind=kind, metadata=metadata or {})

    async def receive_from_vapi(socket: websockets.ClientConnection) -> None:
        async for message in socket:
            if isinstance(message, (bytes, bytearray)):
                if stream_sid:
                    await twilio_ws.send(
                        json.dumps(
                            {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {"payload": base64.b64encode(bytes(message)).decode("ascii")},
                            }
                        )
                    )
                continue
            try:
                event = json.loads(str(message))
            except json.JSONDecodeError:
                event = {"type": "vapi_message", "message": str(message)[:500]}
            event_type = str(event.get("type") or event.get("message") or "vapi_event")
            transcript = str(event.get("transcript") or event.get("text") or "").strip()
            if transcript:
                await append_call_event("Vapi", transcript, kind="vapi_event", metadata={"event_type": event_type})

    async for raw_message in twilio_ws:
        data = json.loads(raw_message)
        event = data.get("event")
        if event == "start":
            start = data.get("start") or {}
            stream_sid = start.get("streamSid") or data.get("streamSid") or ""
            call_sid = start.get("callSid") or call_sid
            custom = start.get("customParameters") or {}
            call_sid = custom.get("callSid") or call_sid
            caller = custom.get("from") or caller
            called = custom.get("to") or called
            try:
                call = await asyncio.to_thread(glam.vapi_create_websocket_call, glam.active_vapi_assistant_id())
                vapi_ws = await websockets.connect(call["websocket_url"], ping_interval=20, ping_timeout=20)
                receive_vapi_task = asyncio.create_task(receive_from_vapi(vapi_ws))
                await append_call_event(
                    "System",
                    "Call connected to Vapi voice bridge.",
                    kind="call_connected",
                    metadata={
                        "stream_sid": stream_sid,
                        "from": caller,
                        "to": called,
                        "voice_engine": "vapi",
                        "vapi_call_id": call.get("call_id", ""),
                        "vapi_assistant_id": call.get("assistant_id", ""),
                    },
                )
            except Exception as exc:
                await append_call_event("System", f"Vapi bridge error: {exc}", kind="error")
                await twilio_ws.close(code=1011, reason="Vapi bridge error")
                break
        elif event == "media":
            media = data.get("media") or {}
            payload = media.get("payload")
            if payload and vapi_ws:
                await vapi_ws.send(base64.b64decode(payload))
        elif event == "stop":
            await append_call_event("System", "Twilio closed the Vapi audio stream.", kind="call_stop")
            if vapi_ws:
                await vapi_ws.close()
            if receive_vapi_task:
                receive_vapi_task.cancel()
            break


async def handle_media_stream(twilio_ws: websockets.ServerConnection) -> None:
    if glam.active_voice_engine() == "vapi":
        await handle_media_stream_vapi(twilio_ws)
        return
    await handle_media_stream_openai(twilio_ws)


async def main_async() -> None:
    print(f"GLAM HOMES Twilio media bridge listening on ws://{HOST}:{PORT}/twilio/media", flush=True)
    async with websockets.serve(handle_media_stream, HOST, PORT, ping_interval=20, ping_timeout=20):
        await asyncio.Future()


def main() -> int:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
