import os
import logging
import json
from dotenv import load_dotenv
from telegram import Update, Message
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from typing import Dict, Optional

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Constants
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
PROXY_CHAT_GROUP_ID = int(os.getenv('PROXY_CHAT_GROUP_ID'))
TOPICS_FILE = 'user_topics.json'

# User topics storage (user_id -> topic_id)
user_topics: Dict[int, int] = {}

def load_topics() -> Dict[int, int]:
    """Load topics from file"""
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, 'r') as f:
            # Convert keys from strings to int
            return {int(k): v for k, v in json.load(f).items()}
    return {}

def save_topics() -> None:
    """Save topics to file"""
    with open(TOPICS_FILE, 'w') as f:
        json.dump(user_topics, f)

# Function to create topic for user
async def create_user_topic(user_id: int, user_name: str, user_last_name: str, username: str, bot) -> Optional[int]:
    try:
        topic_name = f"{user_name} {user_last_name} (@{username}) ID{user_id}"
        result = await bot.create_forum_topic(
            chat_id=PROXY_CHAT_GROUP_ID,
            name=topic_name
        )
        user_topics[user_id] = result.message_thread_id
        save_topics()  # Save changes
        return result.message_thread_id
    except Exception as e:
        logging.error(f"Error creating topic: {e}")
        return None

async def get_ids(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Returns user, group and topic IDs"""
    
    if update.effective_user.id != ADMIN_ID:
        return
        
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_thread_id = update.effective_message.message_thread_id if update.effective_message.is_topic_message else None
    
    response = f"👤 User ID: `{user_id}`\n💭 Chat ID: `{chat_id}`"
    if message_thread_id:
        response += f"\n📌 Topic ID: `{message_thread_id}`"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages from users"""
    user = update.effective_user
    
    # Check if user has a topic
    if user.id not in user_topics:
        # Create new topic for user
        topic_id = await create_user_topic(
            user.id,
            user.first_name,
            user.last_name,
            user.username or "NoUsername",
            context.bot
        )
        if not topic_id:
            await update.message.reply_text("❌ Failed to create topic. Try again later.")
            return
            
    # Forward message to user's topic
    try:
        await context.bot.copy_message(
            chat_id=PROXY_CHAT_GROUP_ID,
            message_thread_id=user_topics[user.id],
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    except Exception as e:
        logging.error(f"Error forwarding message: {e}")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin replies in topics"""
    if update.effective_user.id != ADMIN_ID or not update.effective_message.is_topic_message:
        return
        
    # Find user by topic ID
    topic_id = update.effective_message.message_thread_id
    user_id = None
    
    for uid, tid in user_topics.items():
        if tid == topic_id:
            user_id = uid
            break
            
    if not user_id:
        await update.message.reply_text("❌ Could not find user for this topic")
        return
        
    try:
        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    except Exception as e:
        logging.error(f"Error sending reply to user: {e}")
        await update.message.reply_text("❌ Failed to send message to user")

def main() -> None:
    """Start the bot"""
    # Load topics on startup
    global user_topics
    user_topics = load_topics()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("ids", get_ids))
    
    # Handler for user messages in private chat with bot
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & ~filters.COMMAND,
        handle_user_message
    ))
    
    # Handler for admin replies in topics
    application.add_handler(MessageHandler(
        filters.ChatType.SUPERGROUP & filters.IS_TOPIC_MESSAGE & ~filters.COMMAND,
        handle_admin_reply
    ))

    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 