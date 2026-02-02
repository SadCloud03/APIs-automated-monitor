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


def _ensure_migrations(conn: sqlite3.Connection) -> None:
    """
    Migra DBs existentes (ya creadas) agregando columnas nuevas en api_state.
    SQLite: ALTER TABLE ADD COLUMN ... no rompe datos existentes.
    """
    cur = conn.cursor()

    # api_state puede existir sin columnas nuevas
    cur.execute("PRAGMA table_info(api_state);")
    cols = {row[1] for row in cur.fetchall()}  # row[1] = column name

    # Si la tabla no existe aún, schema.sql la crea. Si existe, agregamos columnas faltantes.
    if cols:
        if "last_status_code" not in cols:
            cur.execute("ALTER TABLE api_state ADD COLUMN last_status_code INTEGER;")
        if "last_latency" not in cols:
            cur.execute("ALTER TABLE api_state ADD COLUMN last_latency REAL;")
        if "last_checked_at" not in cols:
            cur.execute("ALTER TABLE api_state ADD COLUMN last_checked_at DATETIME;")


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"No se encontró schema.sql en: {SCHEMA_PATH}")
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    _ensure_migrations(conn)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


# -------------------------
# Escrituras
# -------------------------

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


def delete_api(api_id: int) -> None:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM APIs WHERE id = ?;", (api_id,))


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


def update_state(api_id: int, status: str, status_code: Optional[int], latency: Optional[float]) -> None:
    """
    Guarda el "estado actual" que consumirá el dashboard.
    """
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO api_state (api_id, last_status, last_status_code, last_latency, last_checked_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(api_id) DO UPDATE SET
                last_status      = excluded.last_status,
                last_status_code = excluded.last_status_code,
                last_latency     = excluded.last_latency,
                last_checked_at  = excluded.last_checked_at;
            """,
            (api_id, status, status_code, latency),
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


# -------------------------
# Lecturas (monitor + dashboard)
# -------------------------

def get_all_apis() -> List[Tuple[int, str, str]]:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, url FROM APIs ORDER BY id ASC;")
        rows = cur.fetchall()
        return [(r["id"], r["name"], r["url"]) for r in rows]


def get_api(api_id: int) -> Optional[Dict[str, Any]]:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, url, created_at FROM APIs WHERE id = ?;", (api_id,))
        r = cur.fetchone()
        return dict(r) if r else None


def get_last_status(api_id: int) -> Optional[str]:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT last_status FROM api_state WHERE api_id = ?;", (api_id,))
        row = cur.fetchone()
    return row["last_status"] if row else None


def get_last_alert_at(api_id: int) -> Optional[str]:
    """
    Devuelve last_alert_at como string (ej: '2026-02-02 12:34:56') o None.
    """
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT last_alert_at FROM api_state WHERE api_id = ?;", (api_id,))
        row = cur.fetchone()
    return row["last_alert_at"] if row else None


def get_apis_with_state() -> List[Dict[str, Any]]:
    """
    Listado principal del dashboard.
    """
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                a.id,
                a.name,
                a.url,
                a.created_at,
                s.last_status,
                s.last_status_code,
                s.last_latency,
                s.last_checked_at,
                s.last_alert_at
            FROM APIs a
            LEFT JOIN api_state s ON s.api_id = a.id
            ORDER BY a.id ASC;
            """
        )
        return [dict(r) for r in cur.fetchall()]


def get_logs(api_id: int, limit: int = 200, since: Optional[str] = None, until: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    since/until: strings tipo 'YYYY-MM-DD HH:MM:SS' (SQLite timestamp)
    """
    limit = max(1, min(int(limit), 2000))

    where = ["api_id = ?"]
    params: List[Any] = [api_id]

    if since:
        where.append("timestamp >= ?")
        params.append(since)
    if until:
        where.append("timestamp <= ?")
        params.append(until)

    where_sql = " AND ".join(where)

    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT id, api_id, status, status_code, latency, response, timestamp
            FROM logs
            WHERE {where_sql}
            ORDER BY timestamp DESC
            LIMIT ?;
            """,
            (*params, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def get_overview_stats() -> Dict[str, Any]:
    """
    KPIs simples para el dashboard (no windowed por ahora).
    """
    with _get_conn() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) AS n FROM APIs;")
        total = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM api_state WHERE last_status = 'UP';")
        up = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM api_state WHERE last_status = 'DOWN';")
        down = cur.fetchone()["n"]

    return {"total": total, "up": up, "down": down}
