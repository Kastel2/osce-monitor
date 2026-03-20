import os
import time
import requests
from datetime import datetime

RUC     = "10719373076"
KEYWORD = "MES DE FEBRERO DEL 2026"
API_URL = f"https://eap.osce.gob.pe/perfilprov-bus/1.0/ficha/{RUC}/contrataciones?pageNumber=1&searchText=&pageSize=10"

TG_TOKEN   = os.environ.get("TG_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

INTERVALO_MINUTOS = 240


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
            "text": texto,
            "parse_mode": "Markdown"
        }, timeout=10)
        data = r.json()
        if data.get("ok"):
            log("Mensaje Telegram enviado correctamente.")
        else:
            log(f"Error Telegram: {data.get('description', 'desconocido')}")
    except Exception as e:
        log(f"Error enviando Telegram: {e}")


def consultar_osce():
    try:
        r = requests.get(API_URL, headers={"Accept": "application/json"}, timeout=15)
        data = r.json()
        contratos = data.get("contratacionesT01", [])
        log(f"Consultando OSCE... {len(contratos)} contratos encontrados.")

        for contrato in contratos:
            desc = contrato.get("desContProv", "")
            if KEYWORD in desc.upper():
                return True, desc

        return False, ""
    except Exception as e:
        log(f"Error consultando OSCE: {e}")
        return None, ""


def monitor():
    log(f"Monitor iniciado — RUC: {RUC} | Keyword: '{KEYWORD}' | Intervalo: {INTERVALO_MINUTOS} min")
    enviar_telegram(
        f"🟢 *Monitor OSCE iniciado*\n\n"
        f"Vigilando RUC `{RUC}` cada {INTERVALO_MINUTOS} minutos.\n"
        f"Alerta cuando detecte: _{KEYWORD}_"
    )

    while True:
        encontrado, descripcion = consultar_osce()

        if encontrado is True:
            log(f"PAGO DETECTADO: {descripcion[:80]}")
            enviar_telegram(
                f"✅ *Pago detectado — OSCE*\n\n"
                f"Se registró el pago de *MES DE FEBRERO DEL 2026* para RUC {RUC}.\n\n"
                f"📋 _{descripcion[:200]}_\n\n"
                f"🔗 https://apps.osce.gob.pe/perfilprov-ui/ficha/{RUC}/contratos"
            )
            log("Monitor detenido — pago encontrado.")
            break
        elif encontrado is False:
            log(f"Sin pago aún. Próxima consulta en {INTERVALO_MINUTOS} min.")
        else:
            log(f"Error en consulta. Reintentando en {INTERVALO_MINUTOS} min.")

        time.sleep(INTERVALO_MINUTOS * 60)


if __name__ == "__main__":
    monitor()
