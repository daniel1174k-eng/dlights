import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the bot token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN set in environment variables")

# Welcome message template
WELCOME_MESSAGE = (
    "👋 Welcome to the group, {mention}!\n"
    "We're glad to have you here. Please read the rules and enjoy your stay."
)

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f"Hello {user.mention_html()}! I'm your welcome bot.\n"
        "I'll greet new members when they join this group.\n"
        "Just add me as an admin and I'll take care of the rest.",
        parse_mode="HTML",
    )

# Handler for new chat members
async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message to new members joining the group."""
    # Only react to messages that contain new chat members
    if not update.message.new_chat_members:
        return

    for member in update.message.new_chat_members:
        # Skip if the new member is the bot itself
        if member.id == context.bot.id:
            continue

        # Build a nice mention (if the user has a username, use that; otherwise use first name)
        if member.username:
            mention = f"@{member.username}"
        else:
            mention = member.first_name

        try:
            await update.message.reply_text(
                WELCOME_MESSAGE.format(mention=mention),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")

# Error handler to keep the bot alive
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and prevent the bot from crashing."""
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members)
    )
    application.add_error_handler(error_handler)

    # Start polling (use webhook in production if preferred; polling works on Render)
    logger.info("Bot started and polling for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
