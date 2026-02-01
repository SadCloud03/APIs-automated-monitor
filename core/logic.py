import sqlite3
import requests
import time 
from pathlib import Path

# ----- path a la base de datos ----
db_path = Path(__file__).parent.parent / 'DataBase' / 'dataBase.db'

# ----- FUNCTIONS ------

# ----- DATABASE FUNCTIONS -----

def add_API_database(api_name, api_url):
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO APIs (
            name,
            url
        ) VALUES (
            ?, ?
        );
    """, (api_name, api_url))

    conexion.commit()
    conexion.close()



def get_id_API(url_api):
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT 
            id
        FROM APIs
        WHERE 
            url = ?
    """, (url_api,))

    id_api = cursor.fetchone()[0]

    conexion.close()
    return id_api

def save_log_dataBase(api_id, new_log):
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO logs (
            api_id,
            status,
            status_code,
            latency,
            response
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        api_id,
        new_log["status"],
        new_log["status_code"],
        new_log["latency"],
        new_log["response"]
    ))

    conexion.commit()
    conexion.close()  


# ----- APIs monitoring -----
def check_api(api_url):
    try:
        start_time = time.perf_counter()
        response = requests.get(api_url, timeout=10)
        latency = round(time.perf_counter() - start_time, 6)

        if response.status_code == 200:
            status = "UP"
        else:
            status = "DOWN"

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
        "api_url": api_url,
        "status": status,
        "status_code": status_code,
        "latency": latency,
        "response": response_text
    }