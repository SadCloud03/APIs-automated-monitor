import requests
import time
from typing import Dict, Any


def check_api(api_url: str) -> Dict[str, Any]:
    """
    GET con timeout. UP si status_code < 400.
    """
    headers = {"User-Agent": "API-Monitor/1.0"}
    start = time.perf_counter()

    try:
        response = requests.get(api_url, timeout=10, headers=headers)
        latency = round(time.perf_counter() - start, 6)

        status = "UP" if response.status_code < 400 else "DOWN"

        return {
            "api_url": api_url,
            "status": status,
            "status_code": response.status_code,
            "latency": latency,
            "response": (response.text or "")[:200],
        }

    except requests.exceptions.Timeout:
        latency = round(time.perf_counter() - start, 6)
        return {
            "api_url": api_url,
            "status": "DOWN",
            "status_code": None,
            "latency": latency,
            "response": "Timeout",
        }

    except Exception as e:
        latency = round(time.perf_counter() - start, 6)
        return {
            "api_url": api_url,
            "status": "DOWN",
            "status_code": None,
            "latency": latency,
            "response": str(e)[:200],
        }
