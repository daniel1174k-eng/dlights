import logging
import os
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ No TELEGRAM_BOT_TOKEN set in environment variables!")

WELCOME_MESSAGE = (
    "👋 Welcome to the group, {mention}!\n"
    "We're glad to have you here. Please read the rules and enjoy your stay."
)

# ============================================================
# 🌐 FLASK - Keeps Render alive
# ============================================================
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "🤖 Welcome Bot is running!", 200

# ============================================================
# 🤖 BOT HANDLERS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"Hello {user.mention_html()}! I'm your welcome bot.\n"
        "Add me as an admin to a group and I'll greet new members!",
        parse_mode="HTML",
    )

async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message.new_chat_members:
        return
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
        mention = f"@{member.username}" if member.username else member.first_name
        try:
            await update.message.reply_text(
                WELCOME_MESSAGE.format(mention=mention),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")

# ============================================================
# 🚀 BOT STARTUP - Avoids signal handler issue on Python 3.14
# ============================================================
async def run_bot_async():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    app.add_error_handler(error_handler)

    await app.initialize()
    await app.start()
    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

    logger.info("✅ Welcome Bot is polling and ready!")

    while True:
        await asyncio.sleep(1)

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot_async())

# Start bot thread when Gunicorn loads this module
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
