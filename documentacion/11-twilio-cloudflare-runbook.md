# Twilio + Cloudflare Runbook

Fecha: 2026-05-19
Actualizado: 2026-06-01 America/Mexico_City / 2026-06-02 UTC

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

## Panel de monitoreo Twilio

El dashboard local de GLAM HOMES muestra un panel "Call & SMS Monitor" encima
de la consola Realtime. Abrirlo desde esta Mac:

```text
http://127.0.0.1:3000/
```

El panel consulta `GET /api/twilio/monitor?deep=1`. Este endpoint es local-only:
si alguien intenta abrirlo por `https://glamhomes.aipeople.app`, devuelve 403
para no exponer metadata de llamadas ni SMS.

Checks incluidos:

- Backend local: `127.0.0.1:3000`
- Media bridge Twilio/OpenAI: `127.0.0.1:8877`
- Proxy publico local: `127.0.0.1:8890`
- Salud publica: `https://glamhomes.aipeople.app/twilio/health`
- Numero Twilio de GLAM: `+17864813013`
- Voice webhook: `https://glamhomes.aipeople.app/twilio/voice`
- SMS webhook: `https://glamhomes.aipeople.app/twilio/sms`
- OpenAI Realtime configurado
- Guesty bridge configurado

El panel tambien muestra las ultimas llamadas y SMS vistos por Twilio. No
expone tokens ni secretos. El frontend refresca automaticamente cada 45
segundos y tiene boton manual `Refresh`.

## Transcripciones

Las llamadas y demos web se guardan localmente en:

```text
transcripts/YYYY-MM-DD/<session>.jsonl
transcripts/YYYY-MM-DD/<session>.md
```

La carpeta `transcripts/` esta ignorada por Git porque puede contener datos
personales de huespedes.

## Estado actual

- Twilio esta validado para `+17864813013`.
- Webhooks aplicados y verificados para llamadas, status callback y SMS.
- `http://127.0.0.1:3000/api/twilio/monitor?deep=1` responde con
  `voice_active=true` y `sms_active=true` desde la maquina local.
- GLAM HOMES usa `3000` para app HTTP, `8877` para Media Streams y `8890` para
  proxy publico local.
- Hay supervisor local en ejecucion para reactivar los procesos GLAM si se caen
  mientras la maquina no se reinicie.
- Guesty se mantiene en modo lectura: reservas, propiedades, disponibilidad y
  calendario minificado.
- Escritura en Guesty, pagos, links de pago y cambios de reserva siguen
  bloqueados hasta definir permisos y aprobaciones humanas.
