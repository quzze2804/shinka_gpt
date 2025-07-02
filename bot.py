from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)

API_TOKEN = "7939973394:AAHiqYYc5MSsiad1qslZ5rvgSnEEP7XeBfs"
ADMIN_CHAT_ID = 7285220061
REVIEWS_CHANNEL_LINK = "https://t.me/+Qca52HCOurI0MmRi"

users_lang = {}

# --- Тексты на двух языках ---
TEXTS = {
    'start': {
        'ru': "Добро пожаловать в шиномонтаж!\n\nВыберите нужный раздел ниже 👇",
        'uk': "Ласкаво просимо до шиномонтажу!\n\nОберіть потрібний розділ нижче 👇"
    },
    'buttons': {
        'ru': ["🔧 Записаться", "📅 Мои записи", "💬 Отзывы", "❓ FAQ", "📍 Локация"],
        'uk': ["🔧 Записатись", "📅 Мої записи", "💬 Відгуки", "❓ FAQ", "📍 Локація"]
    },
    'faq': {
        'ru': "❓ *Часто задаваемые вопросы:*\n\n1. Какие часы работы?\nОтвет: 8:00 – 20:00 ежедневно.\n\n2. Как записаться?\nОтвет: нажмите на кнопку 'Записаться'.",
        'uk': "❓ *Поширені запитання:*\n\n1. Який графік роботи?\nВідповідь: 8:00 – 20:00 щоденно.\n\n2. Як записатись?\nНатисніть кнопку 'Записатись'."
    },
    'location': {
        'ru': "📍 Мы находимся здесь:",
        'uk': "📍 Ми знаходимось тут:"
    }
}


def get_lang(user_id):
    return users_lang.get(user_id, 'ru')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
        ]
    ]
    await update.message.reply_text("🌐 Выберите язык / Оберіть мову:", reply_markup=InlineKeyboardMarkup(keyboard))


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data.split('_')[1]
    users_lang[query.from_user.id] = lang_code

    lang = get_lang(query.from_user.id)
    buttons = TEXTS['buttons'][lang]
    markup = ReplyKeyboardMarkup.from_column(buttons, resize_keyboard=True)

    await query.message.reply_text(TEXTS['start'][lang], reply_markup=markup)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.message.from_user.id)
    text = update.message.text

    if text.startswith("🔧"):
        await update.message.reply_text("🛠 Пожалуйста, напишите дату и время для записи:")
        return

    elif text.startswith("📅"):
        await update.message.reply_text("📅 У вас пока нет активных записей.")
        return

    elif text.startswith("💬"):
        await update.message.reply_text(f"💬 Оставьте отзыв в нашем канале: {REVIEWS_CHANNEL_LINK}")
        return

    elif text.startswith("❓"):
        await update.message.reply_text(TEXTS['faq'][lang], parse_mode="Markdown")
        return

    elif text.startswith("📍"):
        await update.message.reply_location(latitude=50.4501, longitude=30.5234)
        await update.message.reply_text(TEXTS['location'][lang])
        return

    else:
        # Запись клиента
        name = update.message.from_user.full_name
        msg = f"🆕 Новая запись!\n👤 {name}\n🕒 {text}\n🆔 {update.message.from_user.id}"
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)
        await update.message.reply_text("✅ Запись успешно отправлена! Мы с вами свяжемся.")
        return


if __name__ == '__main__':
    app = ApplicationBuilder().token(API_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Бот запущен...")
    app.run_polling()
