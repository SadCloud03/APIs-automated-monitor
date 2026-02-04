import os
from time import sleep
from datetime import datetime
from zoneinfo import ZoneInfo

from core.logic import (
    get_all_apis,
    save_log_dataBase,
    get_last_status,
    get_last_alert_at,
    update_state,
    touch_alert,
    get_subscribers,
)
from core.checker import check_api
from core.notifier import send_telegram

INTERVAL = 10               # cada cuánto chequea (segundos)
DOWN_COOLDOWN_SECONDS = 10  # re-alerta si sigue DOWN cada X segundos

# Zona horaria Paraguay
PY_TZ = ZoneInfo("America/Asuncion")


def _parse_sqlite_ts(ts: str):
    """
    timestamps en DB ya están ajustados a UTC-3 (datetime('now','-3 hours')).
    """
    if not ts:
        return None
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=PY_TZ)


def _cooldown_ok(api_id: int) -> bool:
    ts = get_last_alert_at(api_id)
    last = _parse_sqlite_ts(ts)
    if last is None:
        return True
    now = datetime.now(PY_TZ)
    return (now - last).total_seconds() >= DOWN_COOLDOWN_SECONDS


def _send_to_all(bot_token: str, msg: str) -> int:
    """
    Envía a todos los chat_id suscritos. Devuelve cuántos intentó.
    """
    subs = get_subscribers()
    for s in subs:
        try:
            send_telegram(msg, bot_token, str(s["chat_id"]))
        except Exception:
            pass
    return len(subs)


def empezar_monitoreo():
    print("🚀 Iniciando API Monitor...\n")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_enabled = bool(bot_token) and os.getenv("RUNNER_TELEGRAM_ENABLED", "0") == "1"


    if telegram_enabled:
        print("✅ Telegram habilitado (TELEGRAM_BOT_TOKEN OK).")
    else:
        print("❌ Telegram deshabilitado (falta TELEGRAM_BOT_TOKEN).")

    try:
        while True:
            apis = get_all_apis()

            if not apis:
                print("⚠️ No hay APIs en la DB. Agrega con el dashboard o con main.py add")
                sleep(INTERVAL)
                continue

            for api_id, api_name, api_url in apis:
                try:
                    result = check_api(api_url)

                    # 1) Guardar log histórico
                    save_log_dataBase(api_id, result)

                    # 2) Estado actual y anterior
                    curr_status = result["status"]
                    prev_status = get_last_status(api_id)  # None la primera vez

                    status_code = result.get("status_code")
                    lat = result.get("latency")
                    lat_txt = f"{lat}s" if lat is not None else "N/A"

                    print(f"{api_name} → {curr_status} ({status_code}) Latency: {lat_txt}")

                    # 3) Reglas alertas:
                    # - DOWN: alertar inmediato y luego cooldown (persistente)
                    # - RECOVERED: alertar solo si venía de DOWN
                    send_alert = False
                    alert_reason = ""

                    if curr_status == "DOWN":
                        if telegram_enabled and _cooldown_ok(api_id):
                            send_alert = True
                            alert_reason = "DOWN"

                    elif curr_status == "UP" and prev_status == "DOWN":
                        if telegram_enabled:
                            send_alert = True
                            alert_reason = "RECOVERED"

                    # 4) Enviar alerta si corresponde (a TODOS los suscritos)
                    if telegram_enabled and send_alert:
                        if alert_reason == "DOWN":
                            msg = (
                                "🚨 API DOWN\n"
                                f"Name: {api_name}\n"
                                f"URL: {api_url}\n"
                                f"Code: {status_code}\n"
                                f"Latency: {lat_txt}\n"
                            )
                        else:
                            msg = (
                                "✅ API RECOVERED\n"
                                f"Name: {api_name}\n"
                                f"URL: {api_url}\n"
                                f"Code: {status_code}\n"
                                f"Latency: {lat_txt}\n"
                            )

                        tried = _send_to_all(bot_token, msg)
                        touch_alert(api_id)  # persistimos last_alert_at
                        print(f"📨 Alerta Telegram enviada a {tried} suscriptores.")

                    # 5) Guardar estado actual (para dashboard)
                    update_state(api_id, curr_status, status_code, lat)

                except Exception as e:
                    print(f"❌ Error inesperado monitoreando {api_url}: {e}")

            sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\n🛑 Monitor detenido por el usuario (Ctrl+C).")
