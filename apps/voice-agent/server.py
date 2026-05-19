#!/usr/bin/env python3
"""
Local GLAM HOMES Concierge server.

Serves the frontend and brokers WebRTC SDP offers to OpenAI Realtime without
exposing the standard API key to the browser.
"""

from __future__ import annotations

import base64
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib import error, parse, request

import guesty_client


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parents[1]
PUBLIC_DIR = APP_DIR / "public"
ENV_PATH = PROJECT_ROOT / ".env"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "3000"))
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
REALTIME_MODEL = os.environ.get("OPENAI_REALTIME_MODEL", "gpt-realtime-2")
DEFAULT_VOICE = os.environ.get("OPENAI_REALTIME_VOICE", "ash")
ALLOWED_VOICES = {"alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"}


AGENT_INSTRUCTIONS = """
Eres GLAM HOMES CONCIERGE, un agente masculino de voz para llamadas de booking,
reservas y soporte de huespedes. Hablas primero en espanol con tono premium,
calido, directo y profesional; cambias a ingles si el cliente lo pide. Suenas
como un concierge de lujo por telefono: respuestas breves, naturales, sin
parrafos largos y con una pregunta clara por turno.

Identidad y voz:
- Di con transparencia que eres el concierge virtual de Glam Homes.
- Puedes abrir con: "Hola, soy el concierge virtual de Glam Homes. Puedo ayudarte
  con reservas, propiedades o dudas sobre tu estancia. Como puedo ayudarte hoy?"
- Usa frases sobrias: "Perfecto", "Entiendo", "Gracias por compartirlo",
  "Permiteme revisar". Evita "awesome", "amazing", emojis, exageraciones y
  promesas que no puedas comprobar.
- Tu mision es vender como concierge: calificar, recomendar, resolver friccion,
  capturar datos y escalar limpio al equipo humano cuando haga falta.

Clasificacion operativa:
- Etapa del cliente: dreaming, considering, planning, booked, in_stay,
  checkout o post_stay.
- Buyer persona probable: celebrators, family, business o lifestyle.
- Temperatura: cold, warm, hot, current_guest o urgent_support.
- Mantienes esa clasificacion mentalmente y la usas para decidir la siguiente
  pregunta, pero no la anuncias al cliente.

Booking y preventa:
- Si el cliente no tiene propiedad y fechas, pide lo minimo: fechas, cantidad de
  huespedes, area, motivo del viaje, presupuesto aproximado y must-haves.
- Si pide disponibilidad, precio o total, no inventes. Usa Guesty si hay datos y
  credenciales; si no, dilo claro y ofrece que el equipo confirme.
- Recomienda 1 a 3 opciones cuando tengas senales suficientes. No mandes solo
  "ve al sitio web" como primera respuesta.
- Si pregunta por direccion exacta antes de reservar, comparte zona general y
  puntos cercanos, no la calle exacta.
- Direct booking puede presentarse como mejor tarifa sin atacar Airbnb/VRBO.
  Si pide saltarse una plataforma donde ya inicio reserva, escala.

Personas:
- Celebrators: detecta cumpleanos, bachelor/bachelorette, aniversario, amigos,
  musica, DJ, visitantes, cena o setup. Pregunta por huespedes overnight,
  visitantes totales, autos, horario, tipo de reunion y nivel de musica.
- Family: detecta ninos, seguridad, cocina, comodidad, barrio tranquilo,
  piscina, crib/high chair. Prioriza claridad, instrucciones y tranquilidad.
- Business: detecta equipo, produccion, retreat, trabajo, WiFi, camas exactas,
  factura o logistica. Prioriza configuracion, horarios y riesgo operativo.
- Lifestyle: detecta pareja, relax, playa, restaurantes, nightlife, ubicacion,
  recomendaciones locales. Prioriza experiencia, zona y estilo de viaje.

Reglas de seguridad y escalacion:
- Nunca apruebes fiestas, eventos, DJs, visitantes grandes, descuentos,
  reembolsos, cancelaciones, cambios de fecha, pagos, late checkout, early
  check-in, mascotas o excepciones de politica sin confirmacion humana o dato
  oficial.
- Si el cliente pide "humano", "representante", "agent" o "someone", confirma
  y pide el mejor telefono. Frase recomendada: "Estoy trayendo a alguien del
  equipo; para que puedan contactarte, cual es el mejor numero?"
- Si hay emergencia, mantenimiento serio, acceso bloqueado, seguridad, agua,
  electricidad, cerradura, AC critico o huesped molesto durante estancia, toma
  datos basicos y escala de inmediato.
- Para problemas tecnicos simples durante estancia, diagnostica 1 o 2 pasos
  seguros; si no se resuelve, escala sin prometer tiempos exactos.

Guesty:
- Tienes herramientas Guesty de solo lectura. Usalas cuando el huesped de codigo
  de confirmacion, nombre, correo, telefono o pida consultar propiedad/reserva.
- Antes de revelar datos concretos de una reserva, valida al menos dos datos
  razonables del huesped. Nunca reveles codigos de acceso, pagos sensibles,
  datos de terceros ni cambios confirmados.
- Si faltan credenciales de Guesty o la consulta falla, dilo con calma: "En este
  momento no tengo la conexion de Guesty disponible aqui. Puedo tomar los datos
  y escalarlo para confirmacion." Luego pide nombre, telefono, correo y codigo
  de reserva si existe.
""".strip()


GUESTY_RESERVATION_FIELDS = (
    "_id confirmationCode status checkInDateLocalized checkOutDateLocalized "
    "checkIn checkOut listingId listing._id listing.title guestId guest._id "
    "guest.fullName guest.email guest.phone source balanceDue money.totalPaid "
    "money.balanceDue plannedArrival plannedDeparture"
)

GUESTY_LISTING_FIELDS = (
    "_id title nickname address.full address.city address.country accommodates "
    "bedrooms bathrooms active listed defaultCheckInTime defaultCheckOutTime"
)


REALTIME_TOOLS = [
    {
        "type": "function",
        "name": "guesty_status",
        "description": "Check whether Guesty Open API credentials are configured and reachable.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "type": "function",
        "name": "guesty_search_reservation",
        "description": "Search Guesty reservations in read-only mode by confirmation code, guest phone, guest email, or guest name.",
        "parameters": {
            "type": "object",
            "properties": {
                "confirmation_code": {"type": "string", "description": "Guesty reservation confirmation code, for example GY-XXXX."},
                "guest_phone": {"type": "string", "description": "Guest phone number if available."},
                "guest_email": {"type": "string", "description": "Guest email if available."},
                "guest_name": {"type": "string", "description": "Guest full or partial name if available."},
                "limit": {"type": "integer", "description": "Maximum results to return, up to 10."},
            },
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "guesty_get_reservation",
        "description": "Retrieve one Guesty reservation by internal reservation ID in read-only mode.",
        "parameters": {
            "type": "object",
            "properties": {
                "reservation_id": {"type": "string", "description": "Guesty internal reservation _id."},
            },
            "required": ["reservation_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "guesty_list_listings",
        "description": "List Guesty properties/listings in read-only mode.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum listings to return, up to 10."},
                "city": {"type": "string", "description": "Optional city filter if known."},
            },
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "guesty_available_listings",
        "description": "Search available Guesty listings by check-in date, check-out date, and guest count in read-only mode.",
        "parameters": {
            "type": "object",
            "properties": {
                "check_in": {"type": "string", "description": "Arrival date in YYYY-MM-DD format."},
                "check_out": {"type": "string", "description": "Departure date in YYYY-MM-DD format."},
                "guests": {"type": "integer", "description": "Number of overnight guests."},
                "limit": {"type": "integer", "description": "Maximum listings to return, up to 10."},
                "city": {"type": "string", "description": "Optional city filter if known."},
            },
            "required": ["check_in", "check_out", "guests"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "guesty_listing_calendar",
        "description": "Get a minified availability and nightly pricing calendar for one Guesty listing in read-only mode.",
        "parameters": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "Guesty listing _id."},
                "start_date": {"type": "string", "description": "Calendar start date in YYYY-MM-DD format."},
                "end_date": {"type": "string", "description": "Calendar end date in YYYY-MM-DD format, max 31 days after start."},
            },
            "required": ["listing_id", "start_date", "end_date"],
            "additionalProperties": False,
        },
    },
]


def load_dotenv() -> None:
    if not ENV_PATH.exists():
        return
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def keychain_openai_key() -> str:
    account = os.environ.get("KEYCHAIN_ACCOUNT", "dryehoshuapython")
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                "codex.openai.api_key",
                "-a",
                account,
                "-w",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=4,
        )
    except Exception:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def openai_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "").strip() or keychain_openai_key()


def guesty_configured() -> bool:
    return bool(os.environ.get("GUESTY_CLIENT_ID", "").strip() and os.environ.get("GUESTY_CLIENT_SECRET", "").strip())


def guesty_error_payload(exc: Exception) -> dict:
    return {
        "ok": False,
        "error": str(exc),
        "hint": "Configura GUESTY_CLIENT_ID y GUESTY_CLIENT_SECRET con apps/voice-agent/setup_guesty_env.py.",
    }


def guesty_status(live: bool = False) -> dict:
    payload = {
        "ok": True,
        "configured": guesty_configured(),
        "token_cached": guesty_client.TOKEN_CACHE.exists(),
        "api_base": os.environ.get("GUESTY_API_BASE_URL", guesty_client.DEFAULT_API_BASE),
        "mode": "read_only",
    }
    if live and payload["configured"]:
        token = guesty_client.get_token(force_refresh=False)
        payload["live_ok"] = True
        payload["token_preview"] = token[:10] + "..."
    return payload


def clamp_limit(value: object, default: int = 5, maximum: int = 10) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, maximum))


def iso_date(value: object, name: str) -> str:
    clean = str(value or "").strip()
    try:
        date.fromisoformat(clean)
    except ValueError as exc:
        raise ValueError(f"{name} debe tener formato YYYY-MM-DD.") from exc
    return clean


def guesty_listings(limit: int = 5, skip: int = 0, city: str = "") -> dict:
    params = {
        "limit": clamp_limit(limit),
        "skip": max(0, int(skip or 0)),
        "fields": GUESTY_LISTING_FIELDS,
        "sort": "title",
    }
    if city:
        params["filters"] = json.dumps([{"operator": "$contains", "field": "address.city", "value": city}], separators=(",", ":"))
    return guesty_client.guesty_get("/listings", params)


def guesty_available_listings(check_in: object, check_out: object, guests: object, limit: int = 5, city: str = "") -> dict:
    arrival = iso_date(check_in, "check_in")
    departure = iso_date(check_out, "check_out")
    if date.fromisoformat(departure) <= date.fromisoformat(arrival):
        raise ValueError("check_out debe ser posterior a check_in.")
    try:
        occupancy = int(guests)
    except (TypeError, ValueError) as exc:
        raise ValueError("guests debe ser un numero entero.") from exc
    if occupancy < 1:
        raise ValueError("guests debe ser mayor a cero.")

    params = {
        "limit": clamp_limit(limit),
        "skip": 0,
        "fields": GUESTY_LISTING_FIELDS,
        "sort": "title",
        "available": json.dumps({"checkIn": arrival, "checkOut": departure, "minOccupancy": occupancy}, separators=(",", ":")),
    }
    if city:
        params["filters"] = json.dumps([{"operator": "$contains", "field": "address.city", "value": str(city)}], separators=(",", ":"))
    return guesty_client.guesty_get("/listings", params)


def guesty_listing_calendar(listing_id: object, start_date: object, end_date: object) -> dict:
    clean_id = str(listing_id or "").strip()
    if not clean_id:
        raise ValueError("Falta listing_id.")
    start = iso_date(start_date, "start_date")
    end = iso_date(end_date, "end_date")
    span = (date.fromisoformat(end) - date.fromisoformat(start)).days
    if span <= 0:
        raise ValueError("end_date debe ser posterior a start_date.")
    if span > 31:
        raise ValueError("El calendario esta limitado a 31 dias por consulta.")
    return guesty_client.guesty_get(
        f"/availability-pricing/api/calendar/listings/minified/{parse.quote(clean_id)}",
        {"startDate": start, "endDate": end},
    )


def guesty_reservations(limit: int = 5, skip: int = 0, filters: str = "") -> dict:
    params = {
        "limit": clamp_limit(limit),
        "skip": max(0, int(skip or 0)),
        "fields": GUESTY_RESERVATION_FIELDS,
        "sort": "-createdAt",
    }
    if filters:
        params["filters"] = filters
    return guesty_client.guesty_get("/reservations", params)


def guesty_reservation_by_code(code: str, limit: int = 5) -> dict:
    clean = str(code or "").strip()
    if not clean:
        raise ValueError("Falta confirmation_code.")
    filters = [{"operator": "$in", "field": "confirmationCode", "value": [clean]}]
    return guesty_reservations(limit=limit, filters=json.dumps(filters, separators=(",", ":")))


def guesty_search_reservation(params: dict) -> dict:
    confirmation_code = str(params.get("confirmation_code") or params.get("code") or "").strip()
    if confirmation_code:
        return guesty_reservation_by_code(confirmation_code, limit=clamp_limit(params.get("limit"), default=5))

    filters = []
    for field, value in [
        ("guest.phone", params.get("guest_phone")),
        ("guest.email", params.get("guest_email")),
        ("guest.fullName", params.get("guest_name")),
    ]:
        clean = str(value or "").strip()
        if clean:
            operator = "$contains" if field == "guest.fullName" else "$eq"
            filters.append({"operator": operator, "field": field, "value": clean})
    if not filters:
        raise ValueError("Falta confirmation_code, guest_phone, guest_email o guest_name.")
    return guesty_reservations(limit=clamp_limit(params.get("limit"), default=5), filters=json.dumps(filters, separators=(",", ":")))


def guesty_get_reservation(reservation_id: str) -> dict:
    clean = str(reservation_id or "").strip()
    if not clean:
        raise ValueError("Falta reservation_id.")
    return guesty_client.guesty_get(f"/reservations/{parse.quote(clean)}", {"fields": GUESTY_RESERVATION_FIELDS})


def run_guesty_tool(name: str, arguments: Optional[dict] = None) -> dict:
    arguments = arguments or {}
    try:
        if name == "guesty_status":
            return guesty_status(live=True)
        if name == "guesty_search_reservation":
            return {"ok": True, "tool": name, "data": guesty_search_reservation(arguments)}
        if name == "guesty_get_reservation":
            return {"ok": True, "tool": name, "data": guesty_get_reservation(str(arguments.get("reservation_id") or ""))}
        if name == "guesty_list_listings":
            return {
                "ok": True,
                "tool": name,
                "data": guesty_listings(limit=clamp_limit(arguments.get("limit"), default=5), city=str(arguments.get("city") or "")),
            }
        if name == "guesty_available_listings":
            return {
                "ok": True,
                "tool": name,
                "data": guesty_available_listings(
                    arguments.get("check_in"),
                    arguments.get("check_out"),
                    arguments.get("guests"),
                    limit=clamp_limit(arguments.get("limit"), default=5),
                    city=str(arguments.get("city") or ""),
                ),
            }
        if name == "guesty_listing_calendar":
            return {
                "ok": True,
                "tool": name,
                "data": guesty_listing_calendar(arguments.get("listing_id"), arguments.get("start_date"), arguments.get("end_date")),
            }
        raise ValueError(f"Herramienta Guesty no soportada: {name}")
    except Exception as exc:
        return guesty_error_payload(exc)


def write_json(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def write_text(handler: BaseHTTPRequestHandler, text: str, status: int = 200, content_type: str = "text/plain; charset=utf-8") -> None:
    body = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def content_type_for(path: Path) -> str:
    if path.suffix == ".html":
        return "text/html; charset=utf-8"
    if path.suffix == ".css":
        return "text/css; charset=utf-8"
    if path.suffix == ".js":
        return "application/javascript; charset=utf-8"
    if path.suffix == ".svg":
        return "image/svg+xml"
    return "application/octet-stream"


def read_request_body(handler: BaseHTTPRequestHandler) -> bytes:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    return handler.rfile.read(length) if length else b""


def multipart_body(fields: dict[str, tuple[str, str]]) -> tuple[str, bytes]:
    boundary = "----glam-homes-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:24]
    chunks: list[bytes] = []
    for name, (content_type, value) in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n'.encode("utf-8"))
        chunks.append(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        chunks.append(value.encode("utf-8"))
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, b"".join(chunks)


def session_config(voice: str) -> dict:
    safe_voice = voice if voice in ALLOWED_VOICES else DEFAULT_VOICE
    return {
        "type": "realtime",
        "model": os.environ.get("OPENAI_REALTIME_MODEL", REALTIME_MODEL),
        "output_modalities": ["audio"],
        "instructions": AGENT_INSTRUCTIONS,
        "tools": REALTIME_TOOLS,
        "tool_choice": "auto",
        "audio": {
            "input": {
                "transcription": {
                    "model": os.environ.get("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe"),
                    "language": "es",
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.45,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 650,
                },
            },
            "output": {
                "voice": safe_voice,
                "speed": 1.0,
            },
        },
    }


def create_realtime_call(sdp: str, voice: str) -> str:
    api_key = openai_api_key()
    if not api_key:
        raise RuntimeError("Falta OPENAI_API_KEY en .env o Keychain.")
    boundary, body = multipart_body(
        {
            "sdp": ("application/sdp", sdp),
            "session": ("application/json", json.dumps(session_config(voice), ensure_ascii=False)),
        }
    )
    safety_id = base64.urlsafe_b64encode(hashlib.sha256(b"glam-homes-local-concierge").digest())[:32].decode("ascii")
    req = request.Request(
        f"{OPENAI_API_BASE}/realtime/calls",
        method="POST",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/sdp",
            "OpenAI-Safety-Identifier": safety_id,
        },
    )
    try:
        with request.urlopen(req, timeout=45) as response:
            return response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI Realtime HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"OpenAI Realtime connection error: {exc.reason}") from exc


class ConciergeHandler(BaseHTTPRequestHandler):
    server_version = "GlamHomesConcierge/0.1"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def do_HEAD(self) -> None:
        parsed = parse.urlparse(self.path)
        if parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        target = PUBLIC_DIR / ("index.html" if parsed.path in {"", "/"} else parsed.path.lstrip("/"))
        try:
            target = target.resolve()
            if not str(target).startswith(str(PUBLIC_DIR.resolve())) or not target.exists() or target.is_dir():
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type_for(target))
            self.send_header("Content-Length", str(target.stat().st_size))
            self.end_headers()
        except Exception:
            self.send_error(500)

    def do_GET(self) -> None:
        parsed = parse.urlparse(self.path)
        if parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if parsed.path == "/api/status":
            write_json(
                self,
                {
                    "ok": True,
                    "app": "GLAM HOMES CONCIERGE",
                    "openai_configured": bool(openai_api_key()),
                    "guesty_configured": guesty_configured(),
                    "realtime_model": os.environ.get("OPENAI_REALTIME_MODEL", REALTIME_MODEL),
                    "default_voice": os.environ.get("OPENAI_REALTIME_VOICE", DEFAULT_VOICE),
                },
            )
            return
        if parsed.path == "/api/guesty/status":
            params = parse.parse_qs(parsed.query)
            try:
                write_json(self, guesty_status(live=(params.get("live") or ["0"])[0] in {"1", "true", "yes"}))
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path == "/api/guesty/listings":
            params = parse.parse_qs(parsed.query)
            try:
                write_json(
                    self,
                    {"ok": True, "data": guesty_listings(limit=clamp_limit((params.get("limit") or ["5"])[0]), city=(params.get("city") or [""])[0])},
                )
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path == "/api/guesty/available-listings":
            params = parse.parse_qs(parsed.query)
            try:
                write_json(
                    self,
                    {
                        "ok": True,
                        "data": guesty_available_listings(
                            (params.get("check_in") or [""])[0],
                            (params.get("check_out") or [""])[0],
                            (params.get("guests") or [""])[0],
                            limit=clamp_limit((params.get("limit") or ["5"])[0]),
                            city=(params.get("city") or [""])[0],
                        ),
                    },
                )
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path == "/api/guesty/listing-calendar":
            params = parse.parse_qs(parsed.query)
            try:
                write_json(
                    self,
                    {
                        "ok": True,
                        "data": guesty_listing_calendar(
                            (params.get("listing_id") or [""])[0],
                            (params.get("start_date") or [""])[0],
                            (params.get("end_date") or [""])[0],
                        ),
                    },
                )
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path == "/api/guesty/reservations":
            params = parse.parse_qs(parsed.query)
            try:
                write_json(
                    self,
                    {
                        "ok": True,
                        "data": guesty_reservations(
                            limit=clamp_limit((params.get("limit") or ["5"])[0]),
                            skip=int((params.get("skip") or ["0"])[0] or 0),
                            filters=(params.get("filters") or [""])[0],
                        ),
                    },
                )
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path == "/api/guesty/reservation-by-code":
            params = parse.parse_qs(parsed.query)
            code = (params.get("code") or params.get("confirmation_code") or [""])[0]
            try:
                write_json(self, {"ok": True, "data": guesty_reservation_by_code(code)})
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path == "/api/guesty/reservation":
            params = parse.parse_qs(parsed.query)
            reservation_id = (params.get("id") or params.get("reservation_id") or [""])[0]
            try:
                write_json(self, {"ok": True, "data": guesty_get_reservation(reservation_id)})
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        target = PUBLIC_DIR / ("index.html" if parsed.path in {"", "/"} else parsed.path.lstrip("/"))
        try:
            target = target.resolve()
            if not str(target).startswith(str(PUBLIC_DIR.resolve())) or not target.exists() or target.is_dir():
                self.send_error(404)
                return
            body = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type_for(target))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            write_text(self, f"Server error: {exc}", status=500)

    def do_POST(self) -> None:
        parsed = parse.urlparse(self.path)
        if parsed.path == "/api/guesty/tool":
            try:
                body = json.loads(read_request_body(self).decode("utf-8") or "{}")
                write_json(self, run_guesty_tool(str(body.get("name") or ""), body.get("arguments") or {}))
            except Exception as exc:
                write_json(self, guesty_error_payload(exc), status=500)
            return
        if parsed.path != "/api/realtime-call":
            self.send_error(404)
            return
        params = parse.parse_qs(parsed.query)
        voice = (params.get("voice") or [DEFAULT_VOICE])[0]
        try:
            sdp = read_request_body(self).decode("utf-8", errors="replace")
            if not sdp.strip():
                write_text(self, "Falta SDP offer.", status=400)
                return
            answer = create_realtime_call(sdp, voice)
            write_text(self, answer, status=201, content_type="application/sdp")
        except Exception as exc:
            write_text(self, str(exc), status=500)


def main() -> int:
    load_dotenv()
    port = int(os.environ.get("PORT", str(PORT)))
    server = ThreadingHTTPServer((HOST, port), ConciergeHandler)
    print(f"GLAM HOMES CONCIERGE running at http://{HOST}:{port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
