import requests


def send_telegram(message: str, bot_token: str, chat_id: str) -> None:
    """
    Envía un mensaje al chat_id usando el bot_token.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
