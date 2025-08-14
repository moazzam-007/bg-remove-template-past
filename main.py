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

# Flask app for Render's web service
app = Flask(__name__)

@app.route('/')
def home():
    """Provides a simple health check endpoint."""
    bot_status = "RUNNING" if 'bot_thread' in globals() and bot_thread.is_alive() else "STOPPED"
    return f"<h1>Bot is {bot_status}</h1>", 200

def run_bot():
    """Initializes and runs the Telegram bot."""
    logger.info("Starting Telegram Bot...")
    
    # Get bot token
    bot_token = Config.BOT_TOKEN
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
        
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Initialize bot handler
    bot_handler = BotHandler()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot_handler.start_command))
    application.add_handler(MessageHandler(filters.PHOTO, bot_handler.handle_photo))
    application.add_handler(MessageHandler(filters.Document.IMAGE, bot_handler.handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handler.handle_text))
    
    # Error handler
    application.add_error_handler(bot_handler.error_handler)

    # Start polling
    application.run_polling(allowed_updates=['message'])

if __name__ == '__main__':
    # Ensure temp directory exists
    os.makedirs(Config.TEMP_DIR, exist_ok=True)
    
    # Run the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Run the Flask app (for Gunicorn)
    # The 'app' object is automatically picked up by Gunicorn
    logger.info("Flask app is ready to be served by Gunicorn.")
    # For local testing, you would run: app.run(host='0.0.0.0', port=5000)
