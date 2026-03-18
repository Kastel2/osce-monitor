import os
import time
import random
import requests
from datetime import datetime

# ─── CONFIGURACION ────────────────────────────────────────────
USUARIOS = [
    "szarelly_",
    # "usuario2",
    # "usuario3",
    # "usuario4",
    # "usuario5",
]

INTERVALO_HORAS_MIN = 20
INTERVALO_HORAS_MAX = 28
# ──────────────────────────────────────────────────────────────

TG_TOKEN   = os.environ.get("TG_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

def log(msg):
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{hora}] {msg}", flush=True)

def enviar_telegram(texto):
    if not TG_TOKEN or not TG_CHAT_ID:
        log("ERROR: TG_TOKEN o TG_CHAT_ID no configurados.")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": TG_CHAT_ID,
            "text":    texto,
        }, timeout=10)
        data = r.json()
        if data.get("ok"):
            log("Mensaje Telegram enviado.")
        else:
            log(f"Error Telegram: {data.get('description')}")
    except Exception as e:
        log(f"Error enviando Telegram: {e}")

def obtener_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": random.choice(["es-PE,es;q=0.9", "es-MX,es;q=0.8", "en-US,en;q=0.7"]),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }

def verificar_perfil(usuario):
    # Usar la API publica de Instagram para obtener datos del perfil
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={usuario}"
    headers = obtener_headers()
    headers["X-IG-App-ID"] = "936619743392459"
    headers["X-Requested-With"] = "XMLHttpRequest"
    headers["Referer"] = f"https://www.instagram.com/{usuario}/"

    try:
        espera = random.uniform(3, 8)
        time.sleep(espera)

        r = requests.get(url, headers=headers, timeout=15)
        log(f"@{usuario} status: {r.status_code}")

        if r.status_code == 404:
            log(f"@{usuario} no encontrado.")
            return "no_existe"

        if r.status_code == 401 or r.status_code == 403:
            log(f"@{usuario} requiere login - cuenta privada.")
            return "privado"

        if r.status_code == 200:
            try:
                data = r.json()
                user = data.get("data", {}).get("user", {})
                if not user:
                    log(f"@{usuario} sin datos de usuario - posiblemente privado.")
                    return "privado"

                es_privado = user.get("is_private", True)
                nombre = user.get("full_name", usuario)

                if es_privado:
                    log(f"@{usuario} ({nombre}) - PRIVADO.")
                    return "privado"
                else:
                    log(f"@{usuario} ({nombre}) - PUBLICO.")
                    return "publico"
            except Exception as e:
                log(f"@{usuario} error parseando JSON: {e}")
                return "error"

        log(f"@{usuario} respuesta inesperada: {r.status_code}")
        return "error"

    except Exception as e:
        log(f"@{usuario} error de conexion: {e}")
        return "error"

def monitor():
    log("Monitor IG iniciado")

    lista = "\n".join([f"- @{u}" for u in USUARIOS])
    enviar_telegram(
        f"Monitor Instagram iniciado\n\n"
        f"Vigilando {len(USUARIOS)} cuenta(s):\n{lista}\n\n"
        f"Intervalo: entre {INTERVALO_HORAS_MIN} y {INTERVALO_HORAS_MAX} horas."
    )

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

        if not activos:
            log("Todos los perfiles son publicos. Monitor detenido.")
            enviar_telegram("Monitor Instagram detenido. Todos los perfiles son publicos.")
            break

        horas = random.uniform(INTERVALO_HORAS_MIN, INTERVALO_HORAS_MAX)
        log(f"Quedan {len(activos)} cuenta(s). Proxima consulta en {horas:.1f}h.")
        time.sleep(horas * 3600)

if __name__ == "__main__":
    monitor()
