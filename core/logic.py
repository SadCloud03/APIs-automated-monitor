import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse

DB_PATH = Path(__file__).parent.parent / "DataBase" / "dataBase.db"
SCHEMA_PATH = Path(__file__).parent.parent / "DataBase" / "schema.sql"


def is_valid_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    url = url.strip()
    if not url:
        return False
    if len(url) > 2048:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"No se encontró schema.sql en: {SCHEMA_PATH}")
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    _init_db(conn)
    return conn


def add_API_database(api_name: str, api_url: str) -> None:
    api_name = (api_name or "").strip()
    api_url = (api_url or "").strip()

    if not api_name:
        raise ValueError("El nombre de la API no puede estar vacío.")
    if not is_valid_url(api_url):
        raise ValueError(f"URL inválida: {api_url}")

    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO APIs (name, url)
            VALUES (?, ?);
            """,
            (api_name, api_url),
        )


def get_all_apis() -> List[Tuple[int, str, str]]:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, url FROM APIs ORDER BY id ASC;")
        return cur.fetchall()


def save_log_dataBase(api_id: int, log_data: Dict[str, Any]) -> None:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO logs (api_id, status, status_code, latency, response)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                api_id,
                log_data.get("status"),
                log_data.get("status_code"),
                log_data.get("latency"),
                log_data.get("response"),
            ),
        )


def get_last_status(api_id: int) -> Optional[str]:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT last_status FROM api_state WHERE api_id = ?;", (api_id,))
        row = cur.fetchone()
    return row[0] if row else None


def get_last_alert_at(api_id: int) -> Optional[str]:
    """
    Devuelve last_alert_at como string (ej: '2026-02-02 12:34:56') o None.
    """
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT last_alert_at FROM api_state WHERE api_id = ?;", (api_id,))
        row = cur.fetchone()
    return row[0] if row else None


def update_state(api_id: int, status: str) -> None:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO api_state (api_id, last_status)
            VALUES (?, ?)
            ON CONFLICT(api_id) DO UPDATE SET
                last_status = excluded.last_status;
            """,
            (api_id, status),
        )


def touch_alert(api_id: int) -> None:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO api_state (api_id, last_alert_at)
            VALUES (?, CURRENT_TIMESTAMP)
            ON CONFLICT(api_id) DO UPDATE SET
                last_alert_at = CURRENT_TIMESTAMP;
            """,
            (api_id,),
        )
