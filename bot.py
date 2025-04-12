import os
import logging
import json
from dotenv import load_dotenv
from telegram import Update, Message
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from typing import Dict, Optional

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Константы
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
TARGET_GROUP_ID = int(os.getenv('TARGET_GROUP_ID'))
TOPICS_FILE = 'user_topics.json'

# Хранилище тем пользователей (user_id -> topic_id)
user_topics: Dict[int, int] = {}

def load_topics() -> Dict[int, int]:
    """Загрузка тем из файла"""
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, 'r') as f:
            # Преобразуем ключи из строк в int
            return {int(k): v for k, v in json.load(f).items()}
    return {}

def save_topics() -> None:
    """Сохранение тем в файл"""
    with open(TOPICS_FILE, 'w') as f:
        json.dump(user_topics, f)

# Функция создания темы для пользователя
async def create_user_topic(user_id: int, user_name: str, user_last_name: str, username: str, bot) -> Optional[int]:
    try:
        topic_name = f"{user_name} {user_last_name} (@{username}) ID{user_id}"
        result = await bot.create_forum_topic(
            chat_id=TARGET_GROUP_ID,
            name=topic_name
        )
        user_topics[user_id] = result.message_thread_id
        save_topics()  # Сохраняем изменения
        return result.message_thread_id
    except Exception as e:
        logging.error(f"Ошибка при создании темы: {e}")
        return None

async def new10topics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создает 10 тем в целевой группе"""
    
    # Проверяем, что команда от администратора
    if update.effective_user.id != ADMIN_ID:
        return
    
    # Проверяем, что команда из целевой группы
    if update.effective_chat.id != TARGET_GROUP_ID:
        return
        
    try:
        # Создаем 10 тем
        for i in range(1, 11):
            topic_name = f"Тема {i}"
            await context.bot.create_forum_topic(
                chat_id=TARGET_GROUP_ID,
                name=topic_name
            )
        
        await update.message.reply_text("✅ Успешно создано 10 новых тем!")
    except Exception as e:
        logging.error(f"Ошибка при создании тем: {e}")
        await update.message.reply_text("❌ Произошла ошибка при создании тем")

async def get_ids(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Возвращает ID пользователя, группы и темы"""
    
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
    """Обработка сообщений от пользователей"""
    user = update.effective_user
    
    # Проверяем, есть ли у пользователя тема
    if user.id not in user_topics:
        # Создаем новую тему для пользователя
        topic_id = await create_user_topic(
            user.id,
            user.first_name,
            user.last_name,
            user.username or "NoUsername",
            context.bot
        )
        if not topic_id:
            await update.message.reply_text("❌ Не удалось создать тему. Попробуйте позже.")
            return
            
    # Пересылаем сообщение в тему пользователя
    try:
        await context.bot.copy_message(
            chat_id=TARGET_GROUP_ID,
            message_thread_id=user_topics[user.id],
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    except Exception as e:
        logging.error(f"Ошибка при пересылке сообщения: {e}")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ответов администратора в темах"""
    if update.effective_user.id != ADMIN_ID or not update.effective_message.is_topic_message:
        return
        
    # Ищем пользователя по ID темы
    topic_id = update.effective_message.message_thread_id
    user_id = None
    
    for uid, tid in user_topics.items():
        if tid == topic_id:
            user_id = uid
            break
            
    if not user_id:
        await update.message.reply_text("❌ Не удалось найти пользователя для этой темы")
        return
        
    try:
        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке ответа пользователю: {e}")
        await update.message.reply_text("❌ Не удалось отправить сообщение пользователю")

def main() -> None:
    """Запуск бота"""
    # Загружаем темы при старте
    global user_topics
    user_topics = load_topics()
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("new10topics", new10topics))
    application.add_handler(CommandHandler("ids", get_ids))
    
    # Обработчик сообщений от пользователей в личку боту
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & ~filters.COMMAND,
        handle_user_message
    ))
    
    # Обработчик ответов администратора в темах
    application.add_handler(MessageHandler(
        filters.ChatType.SUPERGROUP & filters.IS_TOPIC_MESSAGE & ~filters.COMMAND,
        handle_admin_reply
    ))

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 