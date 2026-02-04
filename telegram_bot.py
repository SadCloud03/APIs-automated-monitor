import os
import sqlite3
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Mismo default que usa core/logic.py
DEFAULT_DB_PATH = Path(__file__).parent / "DataBase" / "dataBase.db"
DB_PATH = Path(os.getenv("DB_PATH", str(DEFAULT_DB_PATH)))

_last_status_by_api_id: dict[int, str] = {}
_bootstrap_sent = False


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables():
    with _db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriber_apis (
              chat_id TEXT NOT NULL,
              api_id INTEGER NOT NULL,
              PRIMARY KEY (chat_id, api_id)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_subapis_api ON subscriber_apis(api_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_subapis_chat ON subscriber_apis(chat_id)")


def ensure_subscriber(chat_id: int):
    with _db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subscribers(chat_id) VALUES (?)",
            (str(chat_id),),
        )


def get_all_subscribers() -> list[int]:
    with _db() as conn:
        rows = conn.execute("SELECT chat_id FROM subscribers").fetchall()
    out = []
    for r in rows:
        try:
            out.append(int(r["chat_id"]))
        except Exception:
            pass
    return out


def get_current_states():
    q = """
    SELECT
      a.id as api_id,
      a.name as name,
      a.url as url,
      COALESCE(s.last_status, 'UNKNOWN') as last_status,
      s.last_status_code as last_status_code,
      s.last_latency as last_latency,
      s.last_checked_at as last_checked_at
    FROM APIs a
    LEFT JOIN api_state s ON s.api_id = a.id
    ORDER BY a.id ASC
    """
    with _db() as conn:
        return conn.execute(q).fetchall()


def get_api_by_id(api_id: int):
    with _db() as conn:
        return conn.execute(
            """
            SELECT a.id as api_id, a.name as name, a.url as url,
                   COALESCE(s.last_status, 'UNKNOWN') as last_status
            FROM APIs a
            LEFT JOIN api_state s ON s.api_id = a.id
            WHERE a.id = ?
            """,
            (api_id,),
        ).fetchone()


def list_apis_brief():
    with _db() as conn:
        return conn.execute("SELECT id, name, url FROM APIs ORDER BY id ASC").fetchall()


def set_follow_all(chat_id: int):
    with _db() as conn:
        conn.execute("DELETE FROM subscriber_apis WHERE chat_id = ?", (str(chat_id),))


def follow_api(chat_id: int, api_id: int):
    with _db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subscriber_apis(chat_id, api_id) VALUES (?, ?)",
            (str(chat_id), api_id),
        )


def unfollow_api(chat_id: int, api_id: int):
    with _db() as conn:
        conn.execute(
            "DELETE FROM subscriber_apis WHERE chat_id = ? AND api_id = ?",
            (str(chat_id), api_id),
        )


def get_followed_api_ids(chat_id: int) -> set[int]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT api_id FROM subscriber_apis WHERE chat_id = ?",
            (str(chat_id),),
        ).fetchall()
    return {int(r["api_id"]) for r in rows}


def get_chat_ids_following_api(api_id: int) -> list[int]:
    with _db() as conn:
        specific = conn.execute(
            "SELECT DISTINCT chat_id FROM subscriber_apis WHERE api_id = ?",
            (api_id,),
        ).fetchall()

        no_filters = conn.execute(
            """
            SELECT s.chat_id
            FROM subscribers s
            LEFT JOIN subscriber_apis sa ON sa.chat_id = s.chat_id
            WHERE sa.chat_id IS NULL
            """
        ).fetchall()

    ids = set()
    for r in specific + no_filters:
        try:
            ids.add(int(r["chat_id"]))
        except Exception:
            pass
    return list(ids)


def _emoji(status: str) -> str:
    return "✅" if status == "UP" else "🚨" if status == "DOWN" else "❔"


def format_snapshot(rows, only_api_ids: set[int] | None = None) -> str:
    if not rows:
        return "📭 No hay APIs cargadas."

    lines = ["📡 *Estado actual de APIs*"]
    shown = 0

    for r in rows:
        api_id = int(r["api_id"])
        if only_api_ids is not None and api_id not in only_api_ids:
            continue

        extra = []
        if r["last_status_code"] is not None:
            extra.append(f"code={r['last_status_code']}")
        if r["last_latency"] is not None:
            extra.append(f"lat={r['last_latency']}s")
        if r["last_checked_at"]:
            extra.append(f"last={r['last_checked_at']}")

        extra_txt = f" ({', '.join(extra)})" if extra else ""

        lines.append(
            f"{_emoji(r['last_status'])} *[{api_id}]* *{r['name']}* — `{r['url']}` → *{r['last_status']}*{extra_txt}"
        )
        shown += 1

    return "\n".join(lines) if shown else "📭 No hay APIs para mostrar (según tus filtros)."


async def send_snapshot_to(chat_id: int, app: Application):
    rows = get_current_states()
    followed = get_followed_api_ids(chat_id)
    only = None if not followed else followed
    msg = format_snapshot(rows, only_api_ids=only)
    await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ensure_subscriber(chat_id)

    tutorial = (
        "👋 *¡Bienvenido al Monitor de APIs!*\n\n"
        "Este bot te avisa automáticamente cuando una API:\n"
        "🚨 se cae (UP → DOWN)\n"
        "✅ vuelve a levantarse (DOWN → UP)\n\n"
        "📌 *Por defecto seguís TODAS las APIs.*\n\n"
        "🛠️ *Comandos:*\n"
        "/status  → ver estado actual\n"
        "/apis    → listar APIs\n"
        "/follow X   → seguir API X\n"
        "/unfollow X → dejar de seguir API X\n"
        "/my      → ver tus APIs\n"
        "/all     → volver a todas\n\n"
        "🔔 *No necesitás escribir nada más:* el bot avisa solo."
    )

    await update.message.reply_text(tutorial, parse_mode="Markdown")
    await send_snapshot_to(chat_id, context.application)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_subscriber(update.effective_chat.id)
    await send_snapshot_to(update.effective_chat.id, context.application)


async def apis_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = list_apis_brief()
    if not rows:
        await update.message.reply_text("📭 No hay APIs cargadas.")
        return

    lines = ["📋 *APIs disponibles:*"]
    for r in rows:
        lines.append(f"*{r['id']}* — *{r['name']}* — `{r['url']}`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def follow_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ensure_subscriber(chat_id)

    if not context.args:
        await update.message.reply_text("Uso: /follow <api_id>")
        return

    try:
        api_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("El api_id tiene que ser un número. Usá /apis.")
        return

    api = get_api_by_id(api_id)
    if not api:
        await update.message.reply_text("API inexistente. Usá /apis.")
        return

    follow_api(chat_id, api_id)
    await update.message.reply_text(f"✅ Ahora seguís *{api['name']}*", parse_mode="Markdown")


async def unfollow_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ensure_subscriber(chat_id)

    if not context.args:
        await update.message.reply_text("Uso: /unfollow <api_id>")
        return

    try:
        api_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("El api_id tiene que ser un número. Usá /apis.")
        return

    followed = get_followed_api_ids(chat_id)
    if not followed:
        await update.message.reply_text("Estás en modo *todas*. Para filtrar, usá /follow X.", parse_mode="Markdown")
        return

    unfollow_api(chat_id, api_id)
    await update.message.reply_text("🧹 Listo.")


async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_follow_all(update.effective_chat.id)
    await update.message.reply_text("🌐 Volviste a seguir todas las APIs.")


async def my_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ensure_subscriber(chat_id)

    followed = get_followed_api_ids(chat_id)
    if not followed:
        await update.message.reply_text("🌐 Seguís todas las APIs.")
        return

    lines = ["🎯 *Tus APIs:*"]
    for api_id in sorted(followed):
        api = get_api_by_id(api_id)
        if api:
            lines.append(f"*[{api_id}]* *{api['name']}* — `{api['url']}`")
        else:
            lines.append(f"*[{api_id}]* (ya no existe)")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def poll_and_notify(app: Application):
    global _bootstrap_sent

    rows = get_current_states()
    if not rows:
        return

    if not _bootstrap_sent:
        for r in rows:
            _last_status_by_api_id[int(r["api_id"])] = r["last_status"]

        for chat_id in get_all_subscribers():
            try:
                await send_snapshot_to(chat_id, app)
            except Exception:
                pass

        _bootstrap_sent = True
        return

    per_chat: dict[int, list[str]] = {}

    for r in rows:
        api_id = int(r["api_id"])
        new = r["last_status"]
        old = _last_status_by_api_id.get(api_id)

        if old is None:
            _last_status_by_api_id[api_id] = new
            continue

        if new != old:
            _last_status_by_api_id[api_id] = new
            line = f"{_emoji(new)} *[{api_id}]* *{r['name']}* — {old} → *{new}*"
            for chat_id in get_chat_ids_following_api(api_id):
                per_chat.setdefault(chat_id, []).append(line)

    for chat_id, lines in per_chat.items():
        try:
            await app.bot.send_message(
                chat_id=chat_id,
                text="🔔 *Cambios detectados*\n" + "\n".join(lines),
                parse_mode="Markdown",
            )
        except Exception:
            pass


async def notifier_loop(app: Application, interval_seconds: int = 10):
    await asyncio.sleep(1)
    while True:
        try:
            await poll_and_notify(app)
        except Exception as e:
            print("Notifier error:", e)
        await asyncio.sleep(interval_seconds)


def main():
    if not TOKEN:
        raise SystemExit("Falta TELEGRAM_BOT_TOKEN en .env")

    if not DB_PATH.exists():
        print(f"⚠️ DB no encontrada en {DB_PATH}. Corré el monitor primero.")

    ensure_tables()

    async def post_init(application: Application):
        # ✅ sin warning: NO usar application.create_task
        asyncio.create_task(notifier_loop(application, interval_seconds=10))

    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("apis", apis_cmd))
    app.add_handler(CommandHandler("follow", follow_cmd))
    app.add_handler(CommandHandler("unfollow", unfollow_cmd))
    app.add_handler(CommandHandler("all", all_cmd))
    app.add_handler(CommandHandler("my", my_cmd))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
