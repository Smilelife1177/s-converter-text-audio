import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
import io
from dotenv import load_dotenv
import os

# Завантажуємо змінні оточення з .env файлу
load_dotenv()

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Отримуємо токен бота з змінної оточення
TOKEN = os.getenv("api_tg")
if not TOKEN:
    logger.error("Помилка: api_tg не знайдено в .env файлі")
    raise ValueError("api_tg не встановлено")

# Функція для конвертації тексту в аудіо в пам'яті
def text_to_speech(text, lang='uk'):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        # Створюємо буфер у пам'яті
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        # Задаємо ім'я файлу для Telegram
        audio_buffer.name = 'audio.mp3'
        return audio_buffer
    except Exception as e:
        logger.error(f"Помилка при генерації аудіо: {e}")
        return None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я бот, який перетворює текст у аудіо. Просто надішли мені текст, і я надішлю тобі аудіофайл!"
    )

# Обробка текстових повідомлень
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        await update.message.reply_text("Будь ласка, надішли текст!")
        return

    # Генерація аудіо в пам'яті
    audio_buffer = text_to_speech(text, lang='uk')
    if audio_buffer:
        try:
            await update.message.reply_audio(audio=audio_buffer)
            audio_buffer.close()  # Закриваємо буфер
        except Exception as e:
            logger.error(f"Помилка при надсиланні аудіо: {e}")
            await update.message.reply_text("Вибач, сталася помилка при надсиланні аудіо.")
    else:
        await update.message.reply_text("Вибач, не вдалося згенерувати аудіо. Спробуй ще раз!")

# Обробка помилок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Помилка: {context.error}")
    if update and update.message:
        await update.message.reply_text("Сталася помилка. Спробуй ще раз!")

def main():
    # Створюємо додаток
    application = Application.builder().token(TOKEN).build()

    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)

    # Запускаємо бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()