import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
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

# Доступні мови
LANGUAGES = {
    'uk': 'Українська',
    'en': 'English',
    'ru': 'Я ПІДАРАС-Я ПІДАРАС ХА-ХА Я ЛЮБЛЮ ВЕЛИКІ .'
}

# Функція для створення клавіатури вибору мови
def get_language_keyboard():
    keyboard = [
        [InlineKeyboardButton(LANGUAGES[lang], callback_data=f"lang_{lang}")]
        for lang in LANGUAGES
    ]
    return InlineKeyboardMarkup(keyboard)

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
    user_lang = context.user_data.get('language', 'uk')
    welcome_text = (
        "Привіт! Я бот, який перетворює текст у аудіо. "
        f"Поточна мова: {LANGUAGES[user_lang]}. "
        "Обери мову для аудіо нижче і надішли текст!"
    )
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_language_keyboard()
    )

# Обробка вибору мови
async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Отримуємо код мови з callback_data (наприклад, "lang_uk")
    selected_lang = query.data.split('_')[1]
    if selected_lang in LANGUAGES:
        context.user_data['language'] = selected_lang
        await query.message.reply_text(
            f"Обрано мову: {LANGUAGES[selected_lang]}. Надішли текст для конвертації!"
        )
    else:
        await query.message.reply_text("Невідома мова. Спробуй ще раз!")

# Обробка текстових повідомлень
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        await update.message.reply_text("Будь ласка, надішли текст!")
        return

    # Отримуємо мову з user_data або використовуємо українську за замовчуванням
    lang = context.user_data.get('language', 'uk')

    # Генерація аудіо в пам'яті
    audio_buffer = text_to_speech(text, lang=lang)
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
    application.add_handler(CallbackQueryHandler(handle_language_selection, pattern="^lang_"))
    application.add_error_handler(error_handler)

    # Запускаємо бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()