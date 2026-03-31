import os
import time
import random
import requests
from datetime import datetime

USUARIOS = [
    "szarelly_",
]

INTERVALO_HORAS_MIN = 20
INTERVALO_HORAS_MAX = 28

TG_TOKEN   = os.environ.get("TG_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

PRIVADO_TAG = '"is_private":true'
PUBLICO_TAG = '"is_private":false'

def log(msg):
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[" + hora + "] " + msg, flush=True)

def enviar_telegram(texto):
    if not TG_TOKEN or not TG_CHAT_ID:
        log("ERROR: credenciales no configuradas.")
        return
    url = "https://api.telegram.org/bot" + TG_TOKEN + "/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": texto}, timeout=10)
        data = r.json()
        if data.get("ok"):
            log("Telegram OK")
        else:
            log("Error Telegram: " + str(data.get("description")))
    except Exception as e:
        log("Error Telegram: " + str(e))

def verificar_perfil(usuario):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-PE,es;q=0.9",
    }
    time.sleep(random.uniform(2, 5))
    try:
        url = "https://www.instagram.com/" + usuario + "/"
        r = requests.get(url, headers=headers, timeout=15)
        html = r.text
        log("@" + usuario + " status: " + str(r.status_code))

        if r.status_code == 404:
            log("@" + usuario + " no encontrado.")
            return "no_existe"

        if PUBLICO_TAG in html:
            log("@" + usuario + " PUBLICO detectado.")
            return "publico"

        if PRIVADO_TAG in html:
            log("@" + usuario + " PRIVADO.")
            return "privado"

        log("@" + usuario + " estado no determinado.")
        return "error"

    except Exception as e:
        log("@" + usuario + " error: " + str(e))
        return "error"

def monitor():
    log("Monitor IG iniciado")
    lista = ", ".join(["@" + u for u in USUARIOS])
    enviar_telegram(
        "Monitor Instagram iniciado\n\n"
        "Vigilando: " + lista + "\n"
        "Intervalo: " + str(INTERVALO_HORAS_MIN) + "-" + str(INTERVALO_HORAS_MAX) + " horas."
    )

    activos = list(USUARIOS)

    while activos:
        for usuario in activos[:]:
            estado = verificar_perfil(usuario)
            if estado == "publico":
                enviar_telegram(
                    "PERFIL PUBLICO DETECTADO\n\n"
                    "@" + usuario + " ahora es publica.\n"
                    "https://www.instagram.com/" + usuario + "/\n\n"
                    "Entra antes de que lo vuelva a poner en privado!"
                )
                activos.remove(usuario)
                log("@" + usuario + " removido - ya es publico.")

        if not activos:
            log("Todos publicos. Monitor detenido.")
            enviar_telegram("Monitor Instagram detenido. Todos los perfiles son publicos.")
            break

        horas = random.uniform(INTERVALO_HORAS_MIN, INTERVALO_HORAS_MAX)
        log("Proxima consulta en " + str(round(horas, 1)) + "h.")
        time.sleep(horas * 3600)

if __name__ == "__main__":
    monitor()
