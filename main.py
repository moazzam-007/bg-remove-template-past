# main.py

import logging
import os
import threading
from flask import Flask
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot_handler import BotHandler
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -- Bot ko start karne ka function --
def run_bot():
    """Initializes and runs the Telegram bot in polling mode."""
    logger.info("Attempting to start the Telegram Bot...")
    
    # Bot token check
    bot_token = Config.BOT_TOKEN
    if not bot_token:
        logger.error("FATAL: TELEGRAM_BOT_TOKEN environment variable not set!")
        return
        
    # Application setup
    application = Application.builder().token(bot_token).build()
    
    # Handler setup
    bot_handler = BotHandler()
    application.add_handler(CommandHandler("start", bot_handler.start_command))
    application.add_handler(MessageHandler(filters.PHOTO, bot_handler.handle_photo))
    application.add_handler(MessageHandler(filters.Document.IMAGE, bot_handler.handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handler.handle_text))
    application.add_error_handler(bot_handler.error_handler)

    # Bot ko start karo
    logger.info("Bot polling is starting now...")
    application.run_polling(allowed_updates=['message'])
    logger.info("Bot polling has stopped.")


# -- Ye code ab Gunicorn ke import karte hi chalega --
# 1. Temp directory banao
os.makedirs(Config.TEMP_DIR, exist_ok=True)

# 2. Bot ko ek alag thread me chalao
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()
logger.info("Bot thread has been created and started.")


# -- Flask App (Render ke health check ke liye) --
app = Flask(__name__)

@app.route('/')
def home():
    """Provides a simple health check endpoint."""
    # Check if the bot thread is alive
    is_running = bot_thread.is_alive()
    bot_status = "RUNNING" if is_running else "STOPPED"
    status_code = 200 if is_running else 503
    
    logger.info(f"Health check endpoint hit. Bot status: {bot_status}")
    
    return f"<h1>Bot status: {bot_status}</h1>", status_code
