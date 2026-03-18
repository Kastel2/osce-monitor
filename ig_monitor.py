import os
import time
import random
import requests
from datetime import datetime

# ─── CONFIGURACIÓN ────────────────────────────────────────────
USUARIOS = [
    "szarelly_",
    # "usuario2",
    # "usuario3",
    # "usuario4",
    # "usuario5",
]

INTERVALO_HORAS_MIN = 20   # mínimo de horas entre consultas
INTERVALO_HORAS_MAX = 28   # máximo de horas entre consultas
# ──────────────────────────────────────────────────────────────

TG_TOKEN   = os.environ.get("TG_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Samsung Galaxy S22) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

PROXIES_GRATUITOS = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=elite",
]

proxy_pool = []

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
            "chat_id":    TG_CHAT_ID,
            "text":       texto,
            "parse_mode": "Markdown"
        }, timeout=10)
        data = r.json()
        if data.get("ok"):
            log("Mensaje Telegram enviado.")
        else:
            log(f"Error Telegram: {data.get('description')}")
    except Exception as e:
        log(f"Error enviando Telegram: {e}")

def cargar_proxies():
    global proxy_pool
    try:
        r = requests.get(PROXIES_GRATUITOS[0], timeout=10)
        proxies = [p.strip() for p in r.text.split("\n") if p.strip()]
        proxy_pool = proxies[:20]
        log(f"Proxies cargados: {len(proxy_pool)}")
    except Exception as e:
        log(f"No se pudieron cargar proxies: {e}. Continuando sin proxies.")
        proxy_pool = []

def obtener_proxy():
    if proxy_pool:
        proxy = random.choice(proxy_pool)
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    return None

def obtener_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": random.choice(["es-PE,es;q=0.9", "es-MX,es;q=0.8", "en-US,en;q=0.7"]),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }

def verificar_perfil(usuario):
    url = f"https://www.instagram.com/{usuario}/"
    intentos = 3

    for intento in range(intentos):
        try:
            proxy = obtener_proxy()
            headers = obtener_headers()

            # Delay aleatorio entre 3 y 8 segundos antes de cada consulta
            espera = random.uniform(3, 8)
            time.sleep(espera)

            r = requests.get(
                url,
                headers=headers,
                proxies=proxy,
                timeout=15,
                allow_redirects=True
            )

            if r.status_code == 429:
                log(f"@{usuario} — bloqueado temporalmente (429). Esperando 2 horas...")
                time.sleep(7200)
                continue

            if r.status_code == 404:
                log(f"@{usuario} — perfil no encontrado.")
                return "no_existe"

            html = r.text
            if "Log in" in html and "followed" not in html:
                log(f"@{usuario} — privado.")
                return "privado"
            else:
                log(f"@{usuario} — PUBLICO detectado.")
                return "publico"

        except Exception as e:
            log(f"@{usuario} — intento {intento+1} fallido: {e}")
            if intento < intentos - 1:
                time.sleep(random.uniform(10, 30))

    log(f"@{usuario} — todos los intentos fallaron.")
    return "error"

def monitor():
    lista = ", ".join([f"@{u}" for u in USUARIOS])
    log(f"Monitor IG iniciado — {lista}")

    cargar_proxies()

    enviar_telegram(
        f"👁 *Monitor Instagram iniciado*\n\n"
        f"Vigilando {len(USUARIOS)} cuenta(s):\n" +
        "\n".join([f"• @{u}" for u in USUARIOS]) +
        f"\n\n🛡 Protecciones activas: proxies, User-Agent rotativo, delay aleatorio.\n"
        f"Intervalo: entre {INTERVALO_HORAS_MIN} y {INTERVALO_HORAS_MAX} horas."
    )

    activos = list(USUARIOS)

    while activos:
        for usuario in activos[:]:
            estado = verificar_perfil(usuario)
            if estado == "publico":
                enviar_telegram(
                    f"🔓 *Perfil publico detectado*\n\n"
                    f"La cuenta [@{usuario}](https://www.instagram.com/{usuario}/) "
                    f"ahora es *publica*.\n\n"
                    f"Entra antes de que la vuelva a poner en privado!"
                )
                activos.remove(usuario)
                log(f"@{usuario} removido — ya es publico.")

        if not activos:
            log("Todos los perfiles son publicos. Monitor detenido.")
            enviar_telegram("✅ *Monitor Instagram detenido*\n\nTodos los perfiles monitoreados son ahora públicos.")
            break

        # Intervalo aleatorio entre INTERVALO_HORAS_MIN y INTERVALO_HORAS_MAX
        horas = random.uniform(INTERVALO_HORAS_MIN, INTERVALO_HORAS_MAX)
        log(f"Quedan {len(activos)} cuenta(s). Proxima consulta en {horas:.1f}h.")
        
        # Recargar proxies frescos en cada ciclo
        cargar_proxies()
        
        time.sleep(horas * 3600)

if __name__ == "__main__":
    monitor()
