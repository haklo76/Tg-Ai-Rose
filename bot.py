import os
import telebot
import logging
import time
import sys

# Setup logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 50)
    logger.info("🚀 BOT SERVICE STARTING...")
    logger.info("=" * 50)
    
    # Check environment variables
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    
    logger.info(f"🔍 Environment Check:")
    logger.info(f"   BOT_TOKEN: {'✅ SET' if BOT_TOKEN else '❌ MISSING'}")
    logger.info(f"   Token length: {len(BOT_TOKEN) if BOT_TOKEN else 0}")
    
    if BOT_TOKEN:
        logger.info(f"   Token preview: {BOT_TOKEN[:15]}...")
    
    # Check other env vars
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    AUTHORIZED_USERS = os.environ.get('AUTHORIZED_USER_IDS')
    
    logger.info(f"   GEMINI_API_KEY: {'✅ SET' if GEMINI_API_KEY else '❌ MISSING'}")
    logger.info(f"   AUTHORIZED_USERS: {'✅ SET' if AUTHORIZED_USERS else '❌ MISSING'}")
    
    if not BOT_TOKEN:
        logger.error("❌ CRITICAL: BOT_TOKEN not found!")
        logger.info("💡 Solution: Set BOT_TOKEN in Koyeb environment variables")
        return
    
    try:
        # Initialize bot
        logger.info("🤖 Initializing Telegram Bot...")
        bot = telebot.TeleBot(BOT_TOKEN)
        logger.info("✅ Bot instance created successfully")
        
        # Simple command handlers
        @bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            user_name = message.from_user.first_name
            logger.info(f"👋 /start from {user_name} (ID: {message.from_user.id})")
            
            response = f"""
🌹 *Hello {user_name}!* 🌹

I'm Rose Admin Bot running on Koyeb!

🤖 *Status:* ✅ ACTIVE
☁️ *Host:* Koyeb Cloud
📊 *Uptime:* Running smoothly

💫 *Try these commands:*
/start - This message
/status - Bot status  
/userinfo - Your info

*Bot is working perfectly!* 🎉
            """
            bot.reply_to(message, response, parse_mode='Markdown')
        
        @bot.message_handler(commands=['status'])
        def status_command(message):
            logger.info("📊 /status command")
            bot.reply_to(message, 
                        "🤖 *Bot Status:* ✅ ACTIVE\n"
                        "☁️ *Server:* Koyeb\n" 
                        "🌹 *State:* Running perfectly!",
                        parse_mode='Markdown')
        
        @bot.message_handler(commands=['userinfo'])
        def user_info(message):
            user = message.from_user
            logger.info(f"👤 /userinfo for {user.first_name}")
            bot.reply_to(message, 
                        f"👤 *{user.first_name}*\n"
                        f"🆔 `{user.id}`\n"
                        f"📱 @{user.username}" if user.username else "",
                        parse_mode='Markdown')
        
        @bot.message_handler(func=lambda message: True)
        def echo_all(message):
            if message.text:
                logger.info(f"💬 Message: {message.text[:50]}...")
                bot.reply_to(message, f"🌹 You said: {message.text}")
        
        # Start bot polling
        logger.info("🔄 Starting bot polling...")
        bot.infinity_polling(
            timeout=30,
            long_polling_timeout=30,
            logger_level=logging.INFO
        )
        
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        logger.info("🔄 Restarting in 5 seconds...")
        time.sleep(5)
        main()  # Restart

if __name__ == "__main__":
    main()
