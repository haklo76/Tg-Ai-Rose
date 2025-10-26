import os
import telebot
import logging
import random
import time
import requests
from telebot import types

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not found! Please set BOT_TOKEN environment variable.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
logger.info("✅ Bot instance created successfully")

# Store for warnings
user_warnings = {}
ROSES = ["🌹", "💐", "🌸", "💮", "🏵️", "🌺", "🌷", "🥀"]

# ==================== BASIC COMMANDS ====================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_name = message.from_user.first_name
    logger.info(f"👋 Welcome from {user_name}")
    
    welcome_text = f"""
{random.choice(ROSES)} *Rose Admin Bot* {random.choice(ROSES)}

Hello {user_name}! I'm running on Koyeb cloud.

🤖 *Available Commands:*
/start - Show this message
/help - Show help
/userinfo - Show user information
/status - Check bot status

🌹 *Rose-themed responses activated!*
    """
    
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def status_command(message):
    bot_status = "✅ Running on Koyeb"
    bot.reply_to(message, f"🤖 *Bot Status:* {bot_status}\n🌹 *Server:* Koyeb Cloud", parse_mode='Markdown')

@bot.message_handler(commands=['userinfo'])
def user_info(message):
    user = message.from_user
    user_name = user.first_name or "No Name"
    user_id = user.id
    bot.reply_to(message, f"👤 {random.choice(ROSES)} *{user_name}* \n🆔 `{user_id}`", parse_mode='Markdown')

# ==================== ROSE KEYWORD RESPONSES ====================

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Rose-style auto responses"""
    
    # Skip commands
    if message.text and message.text.startswith('/'):
        return
    
    text = message.text.lower() if message.text else ""
    
    # Rose-style keyword responses
    if 'hello' in text or 'hi' in text or 'hey' in text:
        responses = [
            f"{random.choice(ROSES)} Hello beautiful soul!",
            f"{random.choice(ROSES)} Hi there from Koyeb cloud!",
            f"{random.choice(ROSES)} Hey! Wonderful to see you!"
        ]
        bot.reply_to(message, random.choice(responses))
        
    elif 'thanks' in text or 'thank you' in text or 'ty' in text:
        responses = [
            f"{random.choice(ROSES)} You're welcome!",
            f"{random.choice(ROSES)} My pleasure!",
            f"💐 You're most welcome! {random.choice(ROSES)}"
        ]
        bot.reply_to(message, random.choice(responses))
        
    elif 'koyeb' in text:
        bot.reply_to(message, f"☁️ Yes! I'm running on Koyeb cloud platform! {random.choice(ROSES)}")
        
    elif 'rose' in text or 'flower' in text:
        responses = [
            f"{random.choice(ROSES)} Roses are red, violets are blue!",
            f"🌸 Every flower is unique, just like you!",
            f"{random.choice(ROSES)} Flowers make the world beautiful!"
        ]
        bot.reply_to(message, random.choice(responses))

# ==================== BOT RUNNER ====================

def run_bot():
    """Run Telegram bot with enhanced error handling"""
    logger.info("🌹 Starting Rose Admin Bot on Koyeb...")
    logger.info(f"✅ BOT_TOKEN: {'Set' if BOT_TOKEN else 'Missing'}")
    
    restart_count = 0
    max_restarts = 10
    
    while restart_count < max_restarts:
        try:
            logger.info(f"🤖 Bot polling started (Attempt {restart_count + 1})...")
            bot.infinity_polling(
                timeout=30,
                long_polling_timeout=30,
                logger_level=logging.INFO
            )
            
        except Exception as e:
            restart_count += 1
            logger.error(f"❌ Bot polling error: {e}")
            
            if restart_count < max_restarts:
                wait_time = 5
                logger.info(f"🔄 Restarting bot in {wait_time} seconds... (Restart #{restart_count})")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ Max restarts reached ({max_restarts}). Stopping bot.")
                break

if __name__ == "__main__":
    logger.info("🚀 Starting Bot Service on Koyeb...")
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable is required!")
        logger.info("💡 Please set BOT_TOKEN in Koyeb environment variables")
        exit(1)
        
    run_bot()
