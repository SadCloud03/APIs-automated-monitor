import requests
import time
import math
from typing import Dict, Any

# ===== PARÁMETROS ONDA SENOIDAL (DEMO) =====
BASE_LATENCY = 0.3     # segundos base
AMPLITUDE = 0.25       # amplitud de la onda
PERIOD = 30.0          # segundos por ciclo completo


def _sine_latency() -> float:
    """
    Genera una latencia senoidal en función del tiempo.
    """
    t = time.time()
    return round(
        BASE_LATENCY + AMPLITUDE * math.sin(2 * math.pi * t / PERIOD),
        6
    )


def check_api(api_url: str) -> Dict[str, Any]:
    """
    GET con timeout.
    Latencia forzada a onda senoidal (modo demo visual).
    """
    headers = {"User-Agent": "API-Monitor/1.0"}

    try:
        response = requests.get(api_url, timeout=10, headers=headers)

        latency = _sine_latency()
        status = "UP" if response.status_code < 400 else "DOWN"

        return {
            "api_url": api_url,
            "status": status,
            "status_code": response.status_code,
            "latency": latency,
            "response": (response.text or "")[:200],
        }

    except requests.exceptions.Timeout:
        return {
            "api_url": api_url,
            "status": "DOWN",
            "status_code": None,
            "latency": _sine_latency(),
            "response": "Timeout",
        }

    except Exception as e:
        return {
            "api_url": api_url,
            "status": "DOWN",
            "status_code": None,
            "latency": _sine_latency(),
            "response": str(e)[:200],
        }
