# Programas GLAM HOMES

Esta seccion apunta al codigo ejecutable del proyecto.

## Concierge local

Codigo activo:

```text
apps/voice-agent/
```

Arranque:

```bash
python3 apps/voice-agent/server.py
```

URL local:

```text
http://127.0.0.1:3000
```

## Scripts operativos

Actualizar links publicos de propiedades:

```bash
python3 apps/voice-agent/export_property_links.py
```

Configurar credenciales Guesty OAuth:

```bash
python3 apps/voice-agent/setup_guesty_env.py
```

Probar Guesty:

```bash
python3 apps/voice-agent/guesty_client.py auth-check
```
