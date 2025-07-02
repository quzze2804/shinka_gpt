from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters, ContextTypes
)
import logging

# Включим логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
LANG, MAIN_MENU, BOOKING, MY_BOOKINGS, REVIEWS, FAQ = range(6)

# Здесь твои данные для записи и отзывы (в реале нужно базу)
user_bookings = {}
reviews_channel_id = -1001234567890  # замени на свой ID канала для отзывов
admin_chat_id = 123456789  # сюда будут приходить уведомления о новых записях

# Кнопки меню
def main_menu_keyboard(lang='ru'):
    if lang == 'ru':
        buttons = [
            [InlineKeyboardButton("Записаться", callback_data='book')],
            [InlineKeyboardButton("Мои записи", callback_data='my_bookings')],
            [InlineKeyboardButton("Отзывы", callback_data='reviews')],
            [InlineKeyboardButton("FAQ", callback_data='faq')],
            [InlineKeyboardButton("Локация", callback_data='location')]
        ]
    else:  # en
        buttons = [
            [InlineKeyboardButton("Book appointment", callback_data='book')],
            [InlineKeyboardButton("My bookings", callback_data='my_bookings')],
            [InlineKeyboardButton("Reviews", callback_data='reviews')],
            [InlineKeyboardButton("FAQ", callback_data='faq')],
            [InlineKeyboardButton("Location", callback_data='location')]
        ]
    return InlineKeyboardMarkup(buttons)

# Старт и выбор языка
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data='lang_ru')],
        [InlineKeyboardButton("English", callback_data='lang_en')]
    ]
    await update.message.reply_text(
        "Выберите язык / Choose language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return LANG

async def lang_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    context.user_data['lang'] = lang
    text = "Язык выбран: Русский" if lang == 'ru' else "Language selected: English"
    await query.edit_message_text(text=text)
    # Показать главное меню
    await query.message.reply_text(
        text="Главное меню" if lang == 'ru' else "Main menu",
        reply_markup=main_menu_keyboard(lang)
    )
    return MAIN_MENU

# Обработка выбора в главном меню
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'ru')
    data = query.data

    if data == 'book':
        # Пример: записываем на сегодня 10:00, 11:00 и 12:00
        buttons = [
            [InlineKeyboardButton("10:00", callback_data='book_time_10')],
            [InlineKeyboardButton("11:00", callback_data='book_time_11')],
            [InlineKeyboardButton("12:00", callback_data='book_time_12')],
            [InlineKeyboardButton("Отмена" if lang == 'ru' else "Cancel", callback_data='cancel')]
        ]
        await query.edit_message_text(
            "Выберите время для записи:" if lang == 'ru' else "Choose a time:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return BOOKING

    elif data == 'my_bookings':
        user_id = query.from_user.id
        bookings = user_bookings.get(user_id, [])
        if bookings:
            text = "\n".join(bookings) if lang == 'ru' else "\n".join(bookings)
        else:
            text = "У вас пока нет записей." if lang == 'ru' else "You have no bookings yet."
        await query.edit_message_text(text)
        await query.message.reply_text(
            "Главное меню" if lang == 'ru' else "Main menu",
            reply_markup=main_menu_keyboard(lang)
        )
        return MAIN_MENU

    elif data == 'reviews':
        text = "Пожалуйста, отправьте ваш отзыв." if lang == 'ru' else "Please send your review."
        await query.edit_message_text(text)
        return REVIEWS

    elif data == 'faq':
        faq_text = (
            "Вопросы и ответы:\n"
            "1. Как записаться? - Нажмите 'Записаться'.\n"
            "2. Где находится шиномонтаж? - Мы находимся по адресу ...\n"
            "3. Как отменить запись? - Напишите нам.\n"
        ) if lang == 'ru' else (
            "FAQ:\n"
            "1. How to book? - Click 'Book appointment'.\n"
            "2. Where is the tire service? - We are located at ...\n"
            "3. How to cancel? - Contact us.\n"
        )
        await query.edit_message_text(faq_text)
        await query.message.reply_text(
            "Главное меню" if lang == 'ru' else "Main menu",
            reply_markup=main_menu_keyboard(lang)
        )
        return MAIN_MENU

    elif data == 'location':
        # Можно отправить геолокацию (пример координат)
        await query.edit_message_text(
            "Наш адрес: г. Киев, ул. Примерная, 123" if lang == 'ru' else "Our address: Kyiv, Example St. 123"
        )
        await query.message.reply_location(latitude=50.4501, longitude=30.5234)
        await query.message.reply_text(
            "Главное меню" if lang == 'ru' else "Main menu",
            reply_markup=main_menu_keyboard(lang)
        )
        return MAIN_MENU

    elif data == 'cancel':
        await query.edit_message_text("Отменено" if lang == 'ru' else "Canceled")
        await query.message.reply_text(
            "Главное меню" if lang == 'ru' else "Main menu",
            reply_markup=main_menu_keyboard(lang)
        )
        return MAIN_MENU

    else:
        await query.answer("Неизвестная команда" if lang == 'ru' else "Unknown command", show_alert=True)
        return MAIN_MENU

# Обработка выбора времени записи
async def booking_time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'ru')
    time = query.data.split('_')[-1]

    context.user_data['booking_time'] = time
    text = "Введите ваше имя:" if lang == 'ru' else "Enter your name:"
    await query.edit_message_text(text)
    return BOOKING + 1  # новое состояние для имени

# Ввод имени
async def booking_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    name = update.message.text.strip()
    context.user_data['booking_name'] = name

    text = "Введите ваш телефон:" if lang == 'ru' else "Enter your phone number:"
    await update.message.reply_text(text)
    return BOOKING + 2  # новое состояние для телефона

# Ввод телефона и подтверждение записи
async def booking_phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    phone = update.message.text.strip()
    context.user_data['booking_phone'] = phone

    time = context.user_data.get('booking_time', 'unknown')
    name = context.user_data.get('booking_name', 'unknown')

    booking_info = f"{name} | {phone} | Время: {time}" if lang == 'ru' else f"{name} | {phone} | Time: {time}"

    user_id = update.message.from_user.id
    user_bookings.setdefault(user_id, []).append(booking_info)

    # Отправляем уведомление админу
    await context.bot.send_message(chat_id=admin_chat_id, text=f"Новая запись:\n{booking_info}")

    await update.message.reply_text(
        "Ваша запись подтверждена!\nСпасибо." if lang == 'ru' else "Your booking is confirmed!\nThank you."
    )
    await update.message.reply_text(
        "Главное меню" if lang == 'ru' else "Main menu",
        reply_markup=main_menu_keyboard(lang)
    )
    return MAIN_MENU

# Обработка отзывов
async def reviews_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    text = update.message.text.strip()
    user = update.message.from_user

    # Отправляем отзыв в канал
    await context.bot.send_message(
        chat_id=reviews_channel_id,
        text=f"Отзыв от @{user.username or user.full_name}:\n{text}"
    )
    await update.message.reply_text(
        "Спасибо за ваш отзыв!" if lang == 'ru' else "Thank you for your review!"
    )
    await update.message.reply_text(
        "Главное меню" if lang == 'ru' else "Main menu",
        reply_markup=main_menu_keyboard(lang)
    )
    return MAIN_MENU

# Команда /cancel для выхода из диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    await update.message.reply_text(
        "Отменено." if lang == 'ru' else "Canceled.",
        reply_markup=main_menu_keyboard(lang)
    )
    return MAIN_MENU

def main():
    TOKEN = "ТВОЙ_ТОКЕН_ЗДЕСЬ"

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANG: [CallbackQueryHandler(lang_chosen, pattern='^lang_')],
            MAIN_MENU: [CallbackQueryHandler(main_menu_handler, pattern='^(book|my_bookings|reviews|faq|location|cancel)$')],
            BOOKING: [CallbackQueryHandler(booking_time_handler, pattern='^book_time_')],
            BOOKING + 1: [MessageHandler(filters.TEXT & ~filters.COMMAND, booking_name_handler)],
            BOOKING + 2: [MessageHandler(filters.TEXT & ~filters.COMMAND, booking_phone_handler)],
            REVIEWS: [MessageHandler(filters.TEXT & ~filters.COMMAND, reviews_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == '__main__':
    main()
