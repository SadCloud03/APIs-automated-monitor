from core.logic import (
    add_API_database,
    get_id_API,
    save_log_dataBase,
    check_api
)
from time import sleep

# ----- APIS INFORMATION -----
APIS = [
    "https://catfact.ninja/fact",
    "https://dog.ceo/api/breeds/image/random"
]

# ----- MONITORING INTERVAL -----
INTERVAL = 10

# ------ MAIN LOOP -----
def empezar_monitoreo():
    print("🚀 Iniciando API Monitor...\n")

    while True:
        for api_url in APIS:
            api_id = get_id_API(api_url)
            result = check_api(api_url)
            save_log_dataBase(api_id, result)

            print(
                f"{api_url} → {result['status']} "
                f"({result['status_code']}) "
                f"Latency: {result['latency']}s"
            )

        sleep(INTERVAL)
