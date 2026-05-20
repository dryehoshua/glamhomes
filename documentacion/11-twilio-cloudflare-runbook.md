# Twilio + Cloudflare Runbook

Fecha: 2026-05-19

## Regla de seguridad

No tocar ningun numero de Kim Live. En particular, cualquier numero que termine
en `7532` queda protegido y fuera de este proyecto.

Tambien evitar el puerto local `8766`, porque ya esta ocupado por el bridge de
Kim Live en esta maquina. GLAM HOMES usa `8877` para su Media Stream.

El numero de GLAM HOMES para pruebas es:

- `+17864813013`

## Arquitectura local

Para llamadas telefonicas reales se usan dos procesos locales:

1. App HTTP local:

   ```bash
   cd "/Users/dryehoshuapython/Desktop/GLAM HOMES"
   python3 apps/voice-agent/server.py
   ```

   Expone:

   - `http://127.0.0.1:3000/`
   - `/twilio/voice`
   - `/twilio/sms`
   - `/twilio/status`
   - `/twilio/health`
   - endpoints Guesty de solo lectura
   - guardado de transcripciones en `transcripts/YYYY-MM-DD/`

2. Bridge WebSocket Twilio Media Streams <-> OpenAI Realtime:

   ```bash
   cd "/Users/dryehoshuapython/Desktop/GLAM HOMES"
   apps/voice-agent/run_twilio_bridge.sh
   ```

   Expone localmente:

   - `ws://127.0.0.1:8877/twilio/media`

## Cloudflare Tunnel

El hostname objetivo es:

- `https://glamhomes.aipeople.app`

Si DNS esta activo en IONOS, crear este registro:

- Tipo: `CNAME`
- Host: `glamhomes`
- Target: `bcf63a74-3bc1-4656-ad9c-aaf0c059e003.cfargotunnel.com`

Se necesita un named tunnel, no solo un quick tunnel, porque hay que rutear:

- `/twilio/media*` hacia `http://127.0.0.1:8877` para WebSocket.
- El resto hacia `http://127.0.0.1:3000` para HTTP/TwiML/frontend.

Archivo base:

```bash
apps/voice-agent/cloudflare-tunnel.example.yml
```

Pasos esperados:

```bash
brew install cloudflared
cloudflared tunnel login
cloudflared tunnel create glam-homes
cloudflared tunnel route dns glam-homes glamhomes.aipeople.app
cloudflared tunnel ingress validate apps/voice-agent/cloudflare-tunnel.example.yml
apps/voice-agent/run_cloudflare_tunnel.sh
```

Si el archivo de credenciales queda con otro nombre o ruta, ajustar
`credentials-file` en el YAML o definir:

```bash
export CLOUDFLARE_TUNNEL_CONFIG=/ruta/privada/config.yml
```

## Configurar Twilio

Primero probar en seco:

```bash
cd "/Users/dryehoshuapython/Desktop/GLAM HOMES"
python3 apps/voice-agent/configure_twilio_number.py
```

Esto busca exclusivamente `TWILIO_PHONE_NUMBER`. El script se niega a operar si
el numero termina en `7532`.

Cuando el tunel este arriba y `https://glamhomes.aipeople.app/twilio/health`
responda, aplicar:

```bash
python3 apps/voice-agent/configure_twilio_number.py --apply
```

Webhooks esperados:

- Voice URL: `https://glamhomes.aipeople.app/twilio/voice`
- Status callback: `https://glamhomes.aipeople.app/twilio/status`
- SMS URL: `https://glamhomes.aipeople.app/twilio/sms`

## Transcripciones

Las llamadas y demos web se guardan localmente en:

```text
transcripts/YYYY-MM-DD/<session>.jsonl
transcripts/YYYY-MM-DD/<session>.md
```

La carpeta `transcripts/` esta ignorada por Git porque puede contener datos
personales de huespedes.

## Estado actual

- Twilio esta validado en modo dry-run para `+17864813013`.
- No se aplicaron webhooks todavia.
- `cloudflared` no estaba instalado al preparar este runbook.
- Guesty se mantiene en modo lectura: reservas, propiedades, disponibilidad y
  calendario minificado.
- Escritura en Guesty, pagos, links de pago y cambios de reserva siguen
  bloqueados hasta definir permisos y aprobaciones humanas.
