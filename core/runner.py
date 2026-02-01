import requests
import time

APIS = [
    "https://catfact.ninja/fact",
    "https://dog.ceo/api/breeds/image/random"
]

INTERVAL = 30

def check_api(api_url):
    try:
        start_time = time.perf_counter()
        response = requests.get(api_url, timeout=10)
        latency = round(time.perf_counter() - start_time, 6)

        if response.status_code == 200:
            status = "UP" 
        else:
            status ="DOWN"
        response_text = response.text[:200]
        status_code = response.status_code
    except requests.exceptions.Timeout:
        status = "DOWN"
        latency = None
        response_text = "Timeout"
        status_code = None
    except Exception as e:
        status = "DOWN"
        latency = None
        response_text = str(e)
        status_code = None

    return {
        "api_name": api_url,
        "status": status,
        "status_code": status_code,
        "latency": latency,
        "response": response_text
    }

def empezar_monitoreo():
    while True:
        for api in APIS:
            result = check_api(api)
            print(f"{result['api_name']} → {result['status']} ({result['status_code']}) Latency: {result['latency']}s")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    empezar_monitoreo()
