import os
import telebot
from flask import Flask
import logging
import random
import time
import requests
from telebot import types

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
bot = telebot.TeleBot(BOT_TOKEN)

# Store for warnings
user_warnings = {}
ROSES = ["🌹", "💐", "🌸", "💮", "🏵️", "🌺", "🌷", "🥀"]

# ==================== PRIVATE CHAT AI SYSTEM ====================

def get_authorized_users():
    """Get authorized user IDs from environment variable"""
    authorized_ids = os.environ.get('AUTHORIZED_USER_IDS', '').strip()
    if not authorized_ids:
        return []
    return [id.strip() for id in authorized_ids.split(',')]

def is_authorized_ai_user(message):
    """Check if user can use AI features"""
    # Private chat only - check authorized users
    if message.chat.type == 'private':
        authorized_users = get_authorized_users()
        return str(message.from_user.id) in authorized_users
    
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
        return user_member.status in ['administrator', 'creator']
    except Exception as e:
        logger.error(f"Admin check error: {e}")
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
            return "❌ Gemini API Key not configured"
        
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        data = {
            "contents": [{
                "parts": [{"text": f"မြန်မာလိုပြန်ဖြေပေးပါ: {question}"}]
            }]
        }
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"❌ API Error: {response.status_code}"
            
    except Exception as e:
        return f"❌ Request failed: {str(e)}"

def generate_image(description):
    """Private image generation for authorized users only"""
    try:
        return f"🎨 **Image Generation:** {description}\n\nThis feature will be available soon! {random.choice(ROSES)}"
    except Exception as e:
        return f"❌ Image generation not available yet: {str(e)}"

# ==================== COMMAND HANDLERS ====================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_name = message.from_user.first_name
    
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
        bot.reply_to(message, f"🧠 *Thinking...* {random.choice(ROSES)}", parse_mode='Markdown')
        
        response = ask_gemini(question)
        bot.reply_to(message, f"🧠 *AI Response:*\n\n{response}", parse_mode='Markdown')
        
    except Exception as e:
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
        response = generate_image(description)
        bot.reply_to(message, response, parse_mode='Markdown')
        
    except Exception as e:
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
        bot.reply_to(message, f"🔇 {random.choice(ROSES)} *{user_name} muted for {time_display}!*", parse_mode='Markdown')
        
    except Exception as e:
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
            bot.reply_to(message, f"🎤 {random.choice(ROSES)} *{user_name} unmuted!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a user to unmute!*", parse_mode='Markdown')
            
    except Exception as e:
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
            
            # Initialize warnings
            if user_id not in user_warnings:
                user_warnings[user_id] = 0
            
            user_warnings[user_id] += 1
            warnings = user_warnings[user_id]
            
            if warnings >= 3:
                bot.reply_to(message, f"🔨 {random.choice(ROSES)} *{user_name} has 3 warnings!*", parse_mode='Markdown')
            else:
                bot.reply_to(message, f"⚠️ {random.choice(ROSES)} *{user_name} warned! ({warnings}/3)*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a user to warn!*", parse_mode='Markdown')
            
    except Exception as e:
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
            bot.reply_to(message, f"⚠️ {random.choice(ROSES)} *{user_name} has {warnings}/3 warnings*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a user to check warnings!*", parse_mode='Markdown')
    except Exception as e:
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
            bot.reply_to(message, f"🔨 {random.choice(ROSES)} *{user_name} would be banned!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a user to ban!*", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ban failed: {str(e)}")

@bot.message_handler(commands=['kick'])
@admin_or_owner_required
def kick_user(message):
    """Kick user - Group admin only"""
    try:
        if message.reply_to_message:
            user_name = message.reply_to_message.from_user.first_name
            bot.reply_to(message, f"👢 {random.choice(ROSES)} *{user_name} would be kicked!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a user to kick!*", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Kick failed: {str(e)}")

# ==================== MESSAGE MANAGEMENT ====================

@bot.message_handler(commands=['del'])
@admin_or_owner_required
def delete_message(message):
    """Delete message - Group admin only"""
    try:
        if message.reply_to_message:
            bot.reply_to(message, f"🗑️ {random.choice(ROSES)} *Message would be deleted!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"{random.choice(ROSES)} *Reply to a message to delete!*", parse_mode='Markdown')
    except Exception as e:
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
            bot.reply_to(message, f"👤 {random.choice(ROSES)} *{user_name}* \n🆔 `{user_id}`", parse_mode='Markdown')
        else:
            user = message.from_user
            user_name = user.first_name or "No Name"
            user_id = user.id
            bot.reply_to(message, f"👤 {random.choice(ROSES)} *{user_name}* \n🆔 `{user_id}`", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ User info failed: {str(e)}")

@bot.message_handler(commands=['admins'])
def list_admins(message):
    """List admins - Available for everyone"""
    try:
        bot.reply_to(message, f"⭐ {random.choice(ROSES)} *Admin list would be shown!*", parse_mode='Markdown')
    except Exception as e:
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

# ==================== KOYEB DEPLOYMENT READY ====================

if __name__ == "__main__":
    if BOT_TOKEN:
        logger.info("🌹 Rose Admin Bot Starting on Koyeb...")
        # Auto-restart if crash for Koyeb deployment
        while True:
            try:
                logger.info("🤖 Bot polling started...")
                bot.infinity_polling(timeout=60, long_polling_timeout=60)
            except Exception as e:
                logger.error(f"❌ Bot error: {e}")
                logger.info("🔄 Restarting bot in 10 seconds...")
                time.sleep(10)  # Wait 10 seconds before restart
    else:
        logger.error("❌ BOT_TOKEN not found in environment variables!")
