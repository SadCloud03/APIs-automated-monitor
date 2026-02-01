import os
import time
import sqlite3
import requests

# =====================
# Rutas y configuración
# =====================

# Ruta raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ruta ABSOLUTA a /DataBase/database.db
DB_PATH = os.path.join(BASE_DIR, "DataBase", "dataBase.db")

APIS = [
    "https://catfact.ninja/fact",
    "https://dog.ceo/api/breeds/image/random"
]

INTERVAL = 10


# =====================
# Inicialización DB
# =====================
def init_db():
    # Asegurar que el directorio DataBase exista
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('UP', 'DOWN')),
            status_code INTEGER,
            latency REAL,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (api_id) REFERENCES apis(id)
        )
    """)

    conn.commit()
    conn.close()


# =====================
# Base de datos helpers
# =====================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_or_create_api(api_url):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM apis WHERE url = ?",
        (api_url,)
    )
    row = cursor.fetchone()

    if row:
        api_id = row["id"]
    else:
        cursor.execute(
            "INSERT INTO apis (name, url) VALUES (?, ?)",
            (api_url, api_url)
        )
        api_id = cursor.lastrowid
        conn.commit()

    conn.close()
    return api_id


def save_log(api_id, result):
    conn = get_db_connection()
    cursor = conn.cursor()

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
        result["status"],
        result["status_code"],
        result["latency"],
        result["response"]
    ))

    conn.commit()
    conn.close()


# =====================
# Core original
# =====================
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


# =====================
# Loop principal
# =====================
def empezar_monitoreo():
    print("🚀 Iniciando API Monitor...\n")

    # 🔑 Inicializar DB y tablas (FIX)
    init_db()

    while True:
        for api_url in APIS:
            api_id = get_or_create_api(api_url)
            result = check_api(api_url)
            save_log(api_id, result)

            print(
                f"{api_url} → {result['status']} "
                f"({result['status_code']}) "
                f"Latency: {result['latency']}s"
            )

        time.sleep(INTERVAL)
