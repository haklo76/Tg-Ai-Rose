import os
import telebot
from flask import Flask
import logging
import random
import time
import requests
from telebot import types
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Environment variables for Koyeb
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if BOT_TOKEN:
    bot = telebot.TeleBot(BOT_TOKEN)
    logger.info("✅ Bot instance created successfully")
else:
    bot = None
    logger.error("❌ BOT_TOKEN not found in environment variables!")

# Store for warnings
user_warnings = {}
ROSES = ["🌹", "💐", "🌸", "💮", "🏵️", "🌺", "🌷", "🥀"]

# ==================== PRIVATE CHAT AI SYSTEM ====================

def get_authorized_users():
    """Get authorized user IDs from environment variable"""
    authorized_ids = os.environ.get('AUTHORIZED_USER_IDS', '').strip()
    if not authorized_ids:
        logger.warning("⚠️ No authorized users configured")
        return []
    return [id.strip() for id in authorized_ids.split(',')]

def is_authorized_ai_user(message):
    """Check if user can use AI features"""
    # Private chat only - check authorized users
    if message.chat.type == 'private':
        authorized_users = get_authorized_users()
        is_authorized = str(message.from_user.id) in authorized_users
        logger.info(f"🔐 AI Authorization check: User {message.from_user.id} - {'Authorized' if is_authorized else 'Not Authorized'}")
        return is_authorized
    
    # Group chat - AI disabled
    return False

def ai_authorized_required(func):
    """Decorator for AI commands - Private chat only"""
    def wrapper(message):
        if not is_authorized_ai_user(message):
            if message.chat.type == 'private':
                bot.reply_to(message, f"❌ *You are not authorized to use AI features!* {random.choice(ROSES)}", parse_mode='Markdown')
            else:
                bot.reply_to(message, f"❌ *AI features are disabled in groups!* {random.choice(ROSES)}", parse_mode='Markdown')
            return
        return func(message)
    return wrapper

# ==================== ADMIN SYSTEM ====================

def is_user_admin_or_owner(bot, message):
    """Check if user is admin or owner in the group"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        user_member = bot.get_chat_member(chat_id, user_id)
        is_admin = user_member.status in ['administrator', 'creator']
        logger.info(f"🛡️ Admin check: User {user_id} - {'Admin' if is_admin else 'Not Admin'}")
        return is_admin
    except Exception as e:
        logger.error(f"❌ Admin check error: {e}")
        return False

def admin_or_owner_required(func):
    """Decorator to make commands admin/owner only"""
    def wrapper(message):
        if message.chat.type == 'private':
            bot.reply_to(message, f"{random.choice(ROSES)} *This command works in groups only!*", parse_mode='Markdown')
            return
            
        if not is_user_admin_or_owner(bot, message):
            bot.reply_to(message, f"{random.choice(ROSES)} *This command is for admins and owner only!*", parse_mode='Markdown')
            return
        return func(message)
    return wrapper

# ==================== GEMINI AI FUNCTIONS ====================

def ask_gemini(question):
    """Private AI function for authorized users only"""
    try:
        if not GEMINI_API_KEY:
            logger.error("❌ Gemini API Key not configured")
            return "❌ Gemini API Key not configured"
        
        logger.info(f"🧠 Asking Gemini: {question[:50]}...")
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        data = {
            "contents": [{
                "parts": [{"text": f"မြန်မာလိုပြန်ဖြေပေးပါ: {question}"}]
            }]
        }
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            response_text = result["candidates"][0]["content"]["parts"][0]["text"]
            logger.info("✅ Gemini response received successfully")
            return response_text
        else:
            logger.error(f"❌ Gemini API Error: {response.status_code} - {response.text}")
            return f"❌ API Error: {response.status_code}"
            
    except Exception as e:
        logger.error(f"❌ Gemini request failed: {str(e)}")
        return f"❌ Request failed: {str(e)}"

def generate_image(description):
    """Private image generation for authorized users only"""
    try:
        logger.info(f"🎨 Image generation requested: {description}")
        return f"🎨 **Image Generation:** {description}\n\nThis feature will be available soon! {random.choice(ROSES)}"
    except Exception as e:
        logger.error(f"❌ Image generation error: {str(e)}")
        return f"❌ Image generation not available yet: {str(e)}"

# ==================== COMMAND HANDLERS ====================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_name = message.from_user.first_name
    logger.info(f"👋 Welcome command from {user_name} (ID: {message.from_user.id}) in {message.chat.type}")
    
    if message.chat.type == 'private':
        if is_authorized_ai_user(message):
            # Authorized user in private chat
            welcome_text = f"""
{random.choice(ROSES)} *Rose Admin Bot* {random.choice(ROSES)}

👑 *Welcome Owner!* 👑

🤖 *I work in both private chat and groups!*

🛡️ *Group Admin Commands* (when added to groups):
/mute - Mute user
/unmute - Unmute user  
/warn - Warn user
/ban - Ban user

🧠 *Private AI Commands* (မင်းအတွက်ပဲ):
/ai [question] - Ask AI anything
/image [description] - Generate images

*Add me to your groups and make me admin for moderation features!*
            """
        else:
            # Unauthorized user in private chat
            welcome_text = f"""
{random.choice(ROSES)} *Rose Admin Bot* {random.choice(ROSES)}

Hello {user_name}! I'm a group administration bot.

🔧 *I work in groups only!*

Add me to your group and make me admin to use moderation features.

❌ *AI features are not available for you*
            """
    else:
        # Group chat
        if is_user_admin_or_owner(bot, message):
            # Admin in group
            welcome_text = f"""
{random.choice(ROSES)} *Rose Admin Bot* {random.choice(ROSES)}

🛡️ *Admin Commands:*
/mute - Mute user
/unmute - Unmute user  
/warn - Warn user
/ban - Ban user
/kick - Kick user
/del - Delete message

📊 *Info Commands:*
/userinfo - User info
/admins - List admins

❌ *AI features are disabled in groups*
            """
        else:
            # Regular user in group
            welcome_text = f"""
{random.choice(ROSES)} *Rose Admin Bot* {random.choice(ROSES)}

Hello {user_name}! I'm a group administration bot.

Available commands for everyone:
/userinfo - Check your info
/admins - See group admins

*Admin features are for group administrators only.*
            """
    
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# ==================== AI COMMANDS ====================

@bot.message_handler(commands=['ai'])
@ai_authorized_required
def ai_command(message):
    """AI command - Private chat only for authorized users"""
    try:
        if not message.text or len(message.text.split()) < 2:
            bot.reply_to(message, f"""
🧠 *Private AI Mode* {random.choice(ROSES)}

သုံးနည်း:
/ai [မေးခွန်း]

ဥပမာ:
/ai Python programming သင်ပေးပါ
/ai မြန်မာစာကိုဘယ်လိုတိုးတက်အောင်လုပ်မလဲ
/ai ကမ္ဘာ့သမိုင်းအကြောင်းပြောပါ
            """, parse_mode='Markdown')
            return
        
        question = ' '.join(message.text.split()[1:])
        logger.info(f"🧠 AI question from {message.from_user.id}: {question}")
        
        processing_msg = bot.reply_to(message, f"🧠 *Thinking...* {random.choice(ROSES)}", parse_mode='Markdown')
        
        response = ask_gemini(question)
        
        # Delete the "Thinking..." message
        try:
            bot.delete_message(message.chat.id, processing_msg.message_id)
        except:
            pass
        
        bot.reply_to(message, f"🧠 *AI Response:*\n\n{response}", parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ AI command error: {str(e)}")
        bot.reply_to(message, f"❌ AI Error: {str(e)}")

@bot.message_handler(commands=['image'])
@ai_authorized_required
def image_command(message):
    """Image generation - Private chat only for authorized users"""
    try:
        if not message.text or len(message.text.split()) < 2:
            bot.reply_to(message, f"""
🎨 *Image Generation* {random.choice(ROSES)}

သုံးနည်း:
/image [ပုံအကြောင်းအရာ]

ဥပမာ:
/image မြန်မာ့ရိုးရာဝတ်စုံ
/image နေဝင်ဆည်းဆာ
/image ကလေးတွေကစားနေတဲ့ပုံ
            """, parse_mode='Markdown')
            return
        
        description = ' '.join(message.text.split()[1:])
        logger.info(f"🎨 Image generation from {message.from_user.id}: {description}")
        
        response = generate_image(description)
        bot.reply_to(message, response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ Image command error: {str(e)}")
        bot.reply_to(message, f"❌ Image Error: {str(e)}")

# ==================== ADMIN COMMANDS ====================

@bot.message_handler(commands=['mute'])
@admin_or_owner_required
def mute_user(message):
    """Mute command - Group admin only"""
    try:
        # Check bot admin status
        bot_member = bot.get_chat_member(message.chat.id, bot.get_me().id)
        if bot_member.status not in ['administrator', 'creator']:
            bot.reply_to(message, f"{random.choice(ROSES)} *I need admin permissions to mute!*", parse_mode='Markdown')
            return
            
        if not message.reply_to_message:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a user to mute!*", parse_mode='Markdown')
            return

        user_id = message.reply_to_message.from_user.id
        user_name = message.reply_to_message.from_user.first_name
        chat_id = message.chat.id
        
        logger.info(f"🔇 Mute command for {user_name} (ID: {user_id}) in chat {chat_id}")
        
        # Check if trying to mute admin/owner
        target_member = bot.get_chat_member(chat_id, user_id)
        if target_member.status in ['administrator', 'creator']:
            bot.reply_to(message, f"❌ *Cannot mute other admins or owner!*", parse_mode='Markdown')
            return
        
        # Parse time duration
        command_parts = message.text.split()
        mute_seconds = 3600  # Default 1 hour
        
        if len(command_parts) > 1:
            duration = command_parts[1].lower()
            if duration.endswith('m'):
                minutes = int(duration[:-1])
                mute_seconds = minutes * 60
            elif duration.endswith('h'):
                hours = int(duration[:-1])
                mute_seconds = hours * 3600
            elif duration.endswith('d'):
                days = int(duration[:-1])
                mute_seconds = days * 86400
        
        # Create until_date for mute
        until_date = int(time.time()) + mute_seconds
        
        # Set restrictive permissions
        permissions = types.ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        
        # Execute mute
        bot.restrict_chat_member(
            chat_id=chat_id, 
            user_id=user_id, 
            permissions=permissions, 
            until_date=until_date
        )
        
        # Success message
        time_display = format_duration(mute_seconds)
        logger.info(f"✅ Successfully muted {user_name} for {time_display}")
        bot.reply_to(message, f"🔇 {random.choice(ROSES)} *{user_name} muted for {time_display}!*", parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ Mute failed: {str(e)}")
        bot.reply_to(message, f"❌ Mute failed: {str(e)}")

@bot.message_handler(commands=['unmute'])
@admin_or_owner_required
def unmute_user(message):
    """Unmute command - Group admin only"""
    try:
        bot_member = bot.get_chat_member(message.chat.id, bot.get_me().id)
        if bot_member.status not in ['administrator', 'creator']:
            bot.reply_to(message, f"{random.choice(ROSES)} *I need admin permissions to unmute!*", parse_mode='Markdown')
            return
            
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user_name = message.reply_to_message.from_user.first_name
            chat_id = message.chat.id
            
            logger.info(f"🎤 Unmute command for {user_name} (ID: {user_id})")
            
            # Restore permissions
            permissions = types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
            
            bot.restrict_chat_member(chat_id, user_id, permissions)
            logger.info(f"✅ Successfully unmuted {user_name}")
            bot.reply_to(message, f"🎤 {random.choice(ROSES)} *{user_name} unmuted!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a user to unmute!*", parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"❌ Unmute failed: {str(e)}")
        bot.reply_to(message, f"❌ Unmute failed: {str(e)}")

# ==================== WARNING SYSTEM ====================

@bot.message_handler(commands=['warn'])
@admin_or_owner_required
def warn_user(message):
    """Warn user - Group admin only"""
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user_name = message.reply_to_message.from_user.first_name
            
            logger.info(f"⚠️ Warn command for {user_name} (ID: {user_id})")
            
            # Initialize warnings
            if user_id not in user_warnings:
                user_warnings[user_id] = 0
            
            user_warnings[user_id] += 1
            warnings = user_warnings[user_id]
            
            if warnings >= 3:
                logger.info(f"🔨 {user_name} reached 3 warnings!")
                bot.reply_to(message, f"🔨 {random.choice(ROSES)} *{user_name} has 3 warnings!*", parse_mode='Markdown')
            else:
                logger.info(f"⚠️ {user_name} warned ({warnings}/3)")
                bot.reply_to(message, f"⚠️ {random.choice(ROSES)} *{user_name} warned! ({warnings}/3)*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a user to warn!*", parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"❌ Warn failed: {str(e)}")
        bot.reply_to(message, f"❌ Warn failed: {str(e)}")

@bot.message_handler(commands=['warnings'])
@admin_or_owner_required
def check_warnings(message):
    """Check warnings - Group admin only"""
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user_name = message.reply_to_message.from_user.first_name
            warnings = user_warnings.get(user_id, 0)
            logger.info(f"📊 Warning check for {user_name}: {warnings}/3")
            bot.reply_to(message, f"⚠️ {random.choice(ROSES)} *{user_name} has {warnings}/3 warnings*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a user to check warnings!*", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Check warnings failed: {str(e)}")
        bot.reply_to(message, f"❌ Check warnings failed: {str(e)}")

# ==================== BAN COMMANDS ====================

@bot.message_handler(commands=['ban'])
@admin_or_owner_required
def ban_user(message):
    """Ban user - Group admin only"""
    try:
        bot_member = bot.get_chat_member(message.chat.id, bot.get_me().id)
        if bot_member.status not in ['administrator', 'creator']:
            bot.reply_to(message, f"{random.choice(ROSES)} *I need admin permissions to ban!*", parse_mode='Markdown')
            return
            
        if message.reply_to_message:
            user_name = message.reply_to_message.from_user.first_name
            user_id = message.reply_to_message.from_user.id
            logger.info(f"🔨 Ban command for {user_name} (ID: {user_id})")
            bot.reply_to(message, f"🔨 {random.choice(ROSES)} *{user_name} would be banned!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a user to ban!*", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Ban failed: {str(e)}")
        bot.reply_to(message, f"❌ Ban failed: {str(e)}")

@bot.message_handler(commands=['kick'])
@admin_or_owner_required
def kick_user(message):
    """Kick user - Group admin only"""
    try:
        if message.reply_to_message:
            user_name = message.reply_to_message.from_user.first_name
            user_id = message.reply_to_message.from_user.id
            logger.info(f"👢 Kick command for {user_name} (ID: {user_id})")
            bot.reply_to(message, f"👢 {random.choice(ROSES)} *{user_name} would be kicked!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a user to kick!*", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Kick failed: {str(e)}")
        bot.reply_to(message, f"❌ Kick failed: {str(e)}")

# ==================== MESSAGE MANAGEMENT ====================

@bot.message_handler(commands=['del'])
@admin_or_owner_required
def delete_message(message):
    """Delete message - Group admin only"""
    try:
        if message.reply_to_message:
            logger.info(f"🗑️ Delete message command in chat {message.chat.id}")
            bot.reply_to(message, f"🗑️ {random.choice(ROSES)} *Message would be deleted!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a message to delete!*", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Delete failed: {str(e)}")
        bot.reply_to(message, f"❌ Delete failed: {str(e)}")

# ==================== INFO COMMANDS ====================

@bot.message_handler(commands=['userinfo'])
def user_info(message):
    """User information - Available for everyone"""
    try:
        if message.reply_to_message:
            user = message.reply_to_message.from_user
            user_name = user.first_name or "No Name"
            user_id = user.id
            logger.info(f"👤 User info for {user_name} (ID: {user_id})")
            bot.reply_to(message, f"👤 {random.choice(ROSES)} *{user_name}* \n🆔 `{user_id}`", parse_mode='Markdown')
        else:
            user = message.from_user
            user_name = user.first_name or "No Name"
            user_id = user.id
            logger.info(f"👤 Self user info for {user_name} (ID: {user_id})")
            bot.reply_to(message, f"👤 {random.choice(ROSES)} *{user_name}* \n🆔 `{user_id}`", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ User info failed: {str(e)}")
        bot.reply_to(message, f"❌ User info failed: {str(e)}")

@bot.message_handler(commands=['admins'])
def list_admins(message):
    """List admins - Available for everyone"""
    try:
        logger.info(f"⭐ Admin list command in chat {message.chat.id}")
        bot.reply_to(message, f"⭐ {random.choice(ROSES)} *Admin list would be shown!*", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Admin list failed: {str(e)}")
        bot.reply_to(message, f"❌ Admin list failed: {str(e)}")

# ==================== ROSE KEYWORD RESPONSES ====================

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Rose-style auto responses for everyone"""
    
    # Skip commands
    if message.text and message.text.startswith('/'):
        return
    
    text = message.text.lower() if message.text else ""
    
    # Rose-style keyword responses
    if 'hello' in text or 'hi' in text or 'hey' in text:
        responses = [
            f"{random.choice(ROSES)} Hello beautiful soul!",
            f"{random.choice(ROSES)} Hi there! How can I brighten your day?",
            f"{random.choice(ROSES)} Hey! Wonderful to see you!",
            f"🌸 Hello! {random.choice(ROSES)}"
        ]
        bot.reply_to(message, random.choice(responses))
        
    elif 'thanks' in text or 'thank you' in text or 'ty' in text:
        responses = [
            f"{random.choice(ROSES)} You're welcome!",
            f"{random.choice(ROSES)} My pleasure!",
            f"💐 You're most welcome! {random.choice(ROSES)}",
            f"{random.choice(ROSES)} Anytime!"
        ]
        bot.reply_to(message, random.choice(responses))
        
    elif 'good morning' in text:
        bot.reply_to(message, f"🌅 Good morning! May your day bloom with happiness! {random.choice(ROSES)}")
        
    elif 'good night' in text:
        bot.reply_to(message, f"🌙 Good night! Sweet dreams filled with roses! {random.choice(ROSES)}")
        
    elif 'good bot' in text or 'smart bot' in text:
        responses = [
            f"{random.choice(ROSES)} Thank you! You're a good human!",
            f"🌸 You make me blush! {random.choice(ROSES)}",
            f"{random.choice(ROSES)} Thanks! You're amazing too!"
        ]
        bot.reply_to(message, random.choice(responses))
        
    elif 'love' in text or 'loving' in text:
        responses = [
            f"💖 Love is the most beautiful flower! {random.choice(ROSES)}",
            f"💝 Spread love everywhere! {random.choice(ROSES)}",
            f"{random.choice(ROSES)} Love makes the world beautiful!"
        ]
        bot.reply_to(message, random.choice(responses))
        
    elif 'mingalaba' in text or 'မင်္ဂလာပါ' in text:
        responses = [
            f"{random.choice(ROSES)} Mingalaba! Nay kaung lar?",
            f"🌸 မင်္ဂလာပါ! နေကောင်းလား? {random.choice(ROSES)}",
            f"{random.choice(ROSES)} Mingalaba beautiful soul!"
        ]
        bot.reply_to(message, random.choice(responses))
        
    elif 'kyay zu' in text or 'ကျေးဇူးတင်ပါတယ်' in text:
        responses = [
            f"{random.choice(ROSES)} Ya ba de!",
            f"🌷 ရပါတယ်! {random.choice(ROSES)}",
            f"{random.choice(ROSES)} My pleasure!"
        ]
        bot.reply_to(message, random.choice(responses))
        
    elif 'chit tal' in text or 'ချစ်တယ်' in text:
        responses = [
            f"💖 Chit tal! {random.choice(ROSES)}",
            f"💝 အချစ်ဆိုတာ လှပတဲ့ပန်းတစ်မျိုးပါ! {random.choice(ROSES)}",
            f"{random.choice(ROSES)} Love you too!"
        ]
        bot.reply_to(message, random.choice(responses))
        
    elif 'rose' in text or 'flower' in text or 'ပန်း' in text:
        responses = [
            f"{random.choice(ROSES)} Roses are red, violets are blue, you're amazing, that's true!",
            f"🌸 Every flower is unique, just like you! {random.choice(ROSES)}",
            f"{random.choice(ROSES)} Flowers make the world beautiful!"
        ]
        bot.reply_to(message, random.choice(responses))
        
    elif 'beautiful' in text or 'pretty' in text or 'လှတယ်' in text:
        responses = [
            f"✨ You notice beauty because you have a beautiful heart! {random.choice(ROSES)}",
            f"🌟 You're beautiful inside and out! {random.choice(ROSES)}",
            f"{random.choice(ROSES)} Beauty is all around us!"
        ]
        bot.reply_to(message, random.choice(responses))

# ==================== HELPER FUNCTIONS ====================

def format_duration(seconds):
    """Format seconds to readable time"""
    if seconds >= 86400:
        days = seconds // 86400
        return f"{days} day{'s' if days > 1 else ''}"
    elif seconds >= 3600:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''}"
    else:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''}"

# ==================== FLASK ROUTES FOR KOYEB ====================

@app.route('/')
def home():
    return "🌹 Rose Admin Bot - Combined Service is Running on Koyeb!"

@app.route('/health')
def health():
    return "✅ OK", 200

@app.route('/status')
def status():
    bot_status = "✅ Running" if BOT_TOKEN else "❌ Not Configured"
    gemini_status = "✅ Configured" if GEMINI_API_KEY else "❌ Not Configured"
    return f"""
🤖 Bot Status: {bot_status}
🧠 Gemini API: {gemini_status}
🌹 Service: ✅ Running on Koyeb
"""

# ==================== BOT RUNNER ====================

def run_bot():
    """Run Telegram bot with auto-restart"""
    if not BOT_TOKEN:
        logger.error("❌ Cannot start bot: BOT_TOKEN not found!")
        return
    
    logger.info("🌹 Starting Rose Admin Bot on Koyeb...")
    logger.info(f"✅ BOT_TOKEN: {'Set' if BOT_TOKEN else 'Missing'}")
    logger.info(f"✅ GEMINI_API_KEY: {'Set' if GEMINI_API_KEY else 'Missing'}")
    
    restart_count = 0
    max_restarts = 5
    
    while restart_count < max_restarts:
        try:
            logger.info(f"🤖 Bot polling started (Attempt {restart_count + 1})...")
            bot.infinity_polling(
                timeout=60, 
                long_polling_timeout=60,
                logger_level=logging.INFO
            )
            
        except Exception as e:
            restart_count += 1
            logger.error(f"❌ Bot polling error: {e}")
            
            if restart_count < max_restarts:
                wait_time = 10 * restart_count
                logger.info(f"🔄 Restarting bot in {wait_time} seconds... (Restart #{restart_count})")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ Max restarts reached ({max_restarts}). Stopping bot.")
                break

def run_web():
    """Run Flask web server"""
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"🌐 Starting Flask web server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    logger.info("🚀 Starting Rose Admin Bot Service on Koyeb...")
    
    # Start bot in a separate thread if BOT_TOKEN is available
    if BOT_TOKEN:
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("✅ Bot thread started successfully")
    else:
        logger.warning("⚠️ Bot thread not started - BOT_TOKEN missing")
    
    # Start web server in main thread (required for Koyeb)
    run_web()
