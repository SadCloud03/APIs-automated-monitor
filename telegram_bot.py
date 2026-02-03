import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from core.logic import add_subscriber, DB_PATH

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    add_subscriber(
        chat_id=chat.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    await update.message.reply_text(
        f"✅ Suscripto!\nchat_id={chat.id}\nDB={DB_PATH}"
    )

def main():
    if not TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))

    print("🤖 Bot corriendo (polling). Probá /start...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
