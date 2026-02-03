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
)
from core.checker import check_api
from core.notifier import send_telegram

INTERVAL = 10               # cada cuánto chequea (segundos)
DOWN_COOLDOWN_SECONDS = 10  # re-alerta si sigue DOWN cada X segundos

PY_TZ = ZoneInfo("America/Asuncion")


def _parse_sqlite_ts(ts: str):
    """
    SQLite timestamp => 'YYYY-MM-DD HH:MM:SS'

    En este proyecto guardamos los timestamps ya en hora local (America/Asuncion),
    así que acá solo lo parseamos y le ponemos tzinfo=PY_TZ.
    """




def _cooldown_ok(api_id: int) -> bool:
    ts = get_last_alert_at(api_id)
    last = _parse_sqlite_ts(ts)
    if last is None:
        return True

    now = datetime.now(PY_TZ)
    return (now - last).total_seconds() >= DOWN_COOLDOWN_SECONDS


def empezar_monitoreo():
    print("Iniciando API Monitor...\n")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    telegram_enabled = bool(bot_token and chat_id)

    if telegram_enabled:
        print("Telegram alerts habilitadas.")
    else:
        print("Telegram alerts deshabilitadas (faltan TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).")

    try:
        while True:
            apis = get_all_apis()

            if not apis:
                print("No hay APIs en la DB. Agrega con: python main.py add")
                sleep(INTERVAL)
                continue

            for api_id, api_name, api_url in apis:
                try:
                    result = check_api(api_url)

                    save_log_dataBase(api_id, result)

                    curr_status = result["status"]
                    prev_status = get_last_status(api_id)

                    status_code = result.get("status_code")
                    lat = result.get("latency")
                    lat_txt = f"{lat}s" if lat is not None else "N/A"

                    print(f"{api_name} -> {curr_status} ({status_code}) Latency: {lat_txt}")

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

                    if telegram_enabled and send_alert:
                        if alert_reason == "DOWN":
                            msg = (
                                "API DOWN\n"
                                f"Name: {api_name}\n"
                                f"URL: {api_url}\n"
                                f"Status: {curr_status}\n"
                                f"Code: {status_code}\n"
                                f"Latency: {lat_txt}\n"
                            )
                        else:
                            msg = (
                                "API RECOVERED\n"
                                f"Name: {api_name}\n"
                                f"URL: {api_url}\n"
                                f"Status: {curr_status}\n"
                                f"Code: {status_code}\n"
                                f"Latency: {lat_txt}\n"
                            )

                        try:
                            send_telegram(msg, bot_token, chat_id)
                            touch_alert(api_id)
                            print("Alerta Telegram enviada.")
                        except Exception as e:
                            print(f"No se pudo enviar alerta Telegram: {e}")

                    update_state(api_id, curr_status, status_code, lat)

                except Exception as e:
                    print(f"Error inesperado monitoreando {api_url}: {e}")

            sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\nMonitor detenido por el usuario (Ctrl+C).")
