import os
import time
import random
import requests
from datetime import datetime

# ─── CONFIGURACION ────────────────────────────────────────────

USUARIOS = [
“szarelly_”,
# “usuario2”,
# “usuario3”,
# “usuario4”,
# “usuario5”,
]

INTERVALO_HORAS_MIN = 20
INTERVALO_HORAS_MAX = 28

# ──────────────────────────────────────────────────────────────

TG_TOKEN   = os.environ.get(“TG_TOKEN”, “”)
TG_CHAT_ID = os.environ.get(“TG_CHAT_ID”, “”)

USER_AGENTS = [
“Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1”,
“Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1”,
“Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36”,
“Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15”,
]

def log(msg):
hora = datetime.now().strftime(”%Y-%m-%d %H:%M:%S”)
print(f”[{hora}] {msg}”, flush=True)

def enviar_telegram(texto):
if not TG_TOKEN or not TG_CHAT_ID:
log(“ERROR: TG_TOKEN o TG_CHAT_ID no configurados.”)
return
url = f”https://api.telegram.org/bot{TG_TOKEN}/sendMessage”
try:
r = requests.post(url, json={
“chat_id”: TG_CHAT_ID,
“text”:    texto,
}, timeout=10)
data = r.json()
if data.get(“ok”):
log(“Mensaje Telegram enviado.”)
else:
log(f”Error Telegram: {data.get(‘description’)}”)
except Exception as e:
log(f”Error enviando Telegram: {e}”)

def verificar_perfil(usuario):
# Intentar con endpoint JSON publico de Instagram
intentos = [
f”https://www.instagram.com/{usuario}/?__a=1&__d=dis”,
f”https://i.instagram.com/api/v1/users/web_profile_info/?username={usuario}”,
]

```
for url in intentos:
    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "es-PE,es;q=0.9",
            "X-IG-App-ID": "936619743392459",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://www.instagram.com/{usuario}/",
        }

        time.sleep(random.uniform(2, 5))
        r = requests.get(url, headers=headers, timeout=15)
        log(f"@{usuario} [{url.split('/')[4]}] status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                # Buscar campo is_private en diferentes estructuras
                user = (
                    data.get("graphql", {}).get("user") or
                    data.get("data", {}).get("user") or
                    data.get("user") or
                    {}
                )
                if user:
                    es_privado = user.get("is_private", None)
                    nombre = user.get("full_name", usuario)
                    log(f"@{usuario} ({nombre}) is_private={es_privado}")
                    if es_privado is True:
                        return "privado"
                    elif es_privado is False:
                        return "publico"
            except Exception as e:
                log(f"@{usuario} error JSON: {e}")

    except Exception as e:
        log(f"@{usuario} error conexion: {e}")

# Si los endpoints JSON fallan, verificar via HTML buscando indicadores precisos
try:
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "es-PE,es;q=0.9",
    }
    time.sleep(random.uniform(2, 5))
    r = requests.get(f"https://www.instagram.com/{usuario}/", headers=headers, timeout=15)
    html = r.text

    log(f"@{usuario} HTML fallback status: {r.status_code}")

    # Indicadores precisos de cuenta privada en el HTML
    privado_indicators = [
        '"is_private":true',
        '"isPrivate":true',
        'This Account is Private',
        'Esta cuenta es privada',
    ]
    publico_indicators = [
        '"is_private":false',
        '"isPrivate":false',
    ]

    for ind in privado_indicators:
        if ind.lower() in html.lower():
            log(f"@{usuario} PRIVADO (indicador HTML: {ind})")
            return "privado"

    for ind in publico_indicators:
        if ind.lower() in html.lower():
            log(f"@{usuario} PUBLICO (indicador HTML: {ind})")
            return "publico"

    log(f"@{usuario} no se pudo determinar estado.")
    return "error"

except Exception as e:
    log(f"@{usuario} error HTML fallback: {e}")
    return "error"
```

def monitor():
log(“Monitor IG iniciado”)
lista = “\n”.join([f”- @{u}” for u in USUARIOS])
enviar_telegram(
f”Monitor Instagram iniciado\n\n”
f”Vigilando {len(USUARIOS)} cuenta(s):\n{lista}\n\n”
f”Intervalo: entre {INTERVALO_HORAS_MIN} y {INTERVALO_HORAS_MAX} horas.”
)

```
activos = list(USUARIOS)

while activos:
    for usuario in activos[:]:
        estado = verificar_perfil(usuario)
        if estado == "publico":
            enviar_telegram(
                f"PERFIL PUBLICO DETECTADO\n\n"
                f"La cuenta @{usuario} ahora es publica.\n"
                f"https://www.instagram.com/{usuario}/\n\n"
                f"Entra antes de que la vuelva a poner en privado!"
            )
            activos.remove(usuario)
            log(f"@{usuario} removido - ya es publico.")
        elif estado == "error":
            log(f"@{usuario} error - se reintentara en el proximo ciclo.")

    if not activos:
        log("Todos los perfiles son publicos. Monitor detenido.")
        enviar_telegram("Monitor Instagram detenido. Todos los perfiles son publicos.")
        break

    horas = random.uniform(INTERVALO_HORAS_MIN, INTERVALO_HORAS_MAX)
    log(f"Quedan {len(activos)} cuenta(s). Proxima consulta en {horas:.1f}h.")
    time.sleep(horas * 3600)
```

if **name** == “**main**”:
monitor()