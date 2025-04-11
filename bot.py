import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

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

def main() -> None:
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("new10topics", new10topics))
    application.add_handler(CommandHandler("ids", get_ids))

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 