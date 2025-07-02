import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import datetime
import pytz

# --- Настройки ---
TOKEN = "7939973394:AAHiqYYc5MSsiad1qslZ5rvgSnEEP7XeBfs"
ADMIN_CHAT_ID = 7285220061
REVIEWS_CHANNEL_LINK = "https://t.me/+Qca52HCOurI0MmRi"
ADMIN_USERNAME_FOR_REVIEWS = "shimontazh_arciz"
TIMEZONE = pytz.timezone('Europe/Kiev')

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

(
    LANG_SELECTION,
    BOOKING_SELECT_DAY,
    BOOKING_SELECT_TIME,
    BOOKING_ASK_NAME,
    BOOKING_ASK_PHONE,
    BOOKING_CONFIRM,
) = range(6)

booked_slots = {}

translations = {
    'ru': {
        'choose_language': "Пожалуйста, выберите язык:",
        'lang_button_ru': "Русский",
        'lang_button_uk': "Українська",
        'welcome_message': (
            "Привет, {user_full_name}! 👋\n\n"
            "Добро пожаловать в шиномонтаж!\n"
            "Выберите действие ниже:"
        ),
        'btn_book_appointment': "🗓️ Записаться на шиномонтаж",
        'btn_my_bookings': "📋 Мои записи",
        'btn_info_and_faq': "ℹ️ Информация и FAQ",
        'btn_our_location': "📍 Наше местоположение",
        'btn_reviews': "⭐ Отзывы",
        'btn_main_menu': "⬅️ Главное меню",
        'select_day_for_booking': "Выберите день для записи:",
        'select_time_for_booking': "Выберите время для записи на {date}:",
        'enter_name': "Введите ваше имя:",
        'enter_phone': "Введите номер телефона (например, +380XXXXXXXXX):",
        'booking_confirmed': "✅ Запись подтверждена на {date} в {time}. Спасибо, {name}!",
        'process_cancelled': "Процесс записи отменён.",
        'cancel': "Отмена",
        'back': "Назад",
        'error_invalid_phone': "Неверный формат номера телефона. Попробуйте снова.",
        'error_invalid_name': "Неверное имя. Попробуйте снова.",
        'info_faq': (
            "Информация и FAQ:\n"
            "- Услуги: монтаж, балансировка, ремонт шин.\n"
            "- Часы работы: Пн-Пт 8:00-17:00.\n"
            "- Адрес: г. Одесса, ул. Успенская, 1."
        ),
        'our_location_address': "Мы находимся по адресу: г. Одесса, ул. Успенская, 1.",
        'no_active_bookings': "У вас пока нет записей.",
    },
    'uk': {
        'choose_language': "Будь ласка, оберіть мову:",
        'lang_button_ru': "Російська",
        'lang_button_uk': "Українська",
        'welcome_message': (
            "Привіт, {user_full_name}! 👋\n\n"
            "Ласкаво просимо до шиномонтажу!\n"
            "Оберіть дію нижче:"
        ),
        'btn_book_appointment': "🗓️ Записатися на шиномонтаж",
        'btn_my_bookings': "📋 Мої записи",
        'btn_info_and_faq': "ℹ️ Інформація та FAQ",
        'btn_our_location': "📍 Наше місцезнаходження",
        'btn_reviews': "⭐ Відгуки",
        'btn_main_menu': "⬅️ Головне меню",
        'select_day_for_booking': "Оберіть день для запису:",
        'select_time_for_booking': "Оберіть час для запису на {date}:",
        'enter_name': "Введіть ваше ім'я:",
        'enter_phone': "Введіть номер телефону (наприклад, +380XXXXXXXXX):",
        'booking_confirmed': "✅ Запис підтверджено на {date} о {time}. Дякуємо, {name}!",
        'process_cancelled': "Процес запису скасовано.",
        'cancel': "Скасувати",
        'back': "Назад",
        'error_invalid_phone': "Неправильний формат номера телефону. Спробуйте ще раз.",
        'error_invalid_name': "Неправильне ім'я. Спробуйте ще раз.",
        'info_faq': (
            "Інформація та FAQ:\n"
            "- Послуги: монтаж, балансування, ремонт шин.\n"
            "- Години роботи: Пн-Пт 8:00-17:00.\n"
            "- Адреса: м. Одеса, вул. Успенська, 1."
        ),
        'our_location_address': "Ми знаходимося за адресою: м. Одеса, вул. Успенська, 1.",
        'no_active_bookings': "У вас поки що немає записів.",
    }
}

def get_text(context: ContextTypes.DEFAULT_TYPE, key: str, **kwargs) -> str:
    lang = context.user_data.get('language', 'ru')
    text = translations.get(lang, translations['ru']).get(key, key)
    return text.format(**kwargs)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = context.user_data.get('language')
    if not user_lang:
        keyboard = [
            [InlineKeyboardButton(translations['ru']['lang_button_ru'], callback_data='lang_ru')],
            [InlineKeyboardButton(translations['uk']['lang_button_uk'], callback_data='lang_uk')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.message:
            await update.message.reply_text(translations['ru']['choose_language'], reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text(translations['ru']['choose_language'], reply_markup=reply_markup)
        return LANG_SELECTION
    else:
        await show_main_menu(update, context)
        return ConversationHandler.END

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data.split('_')[1]
    context.user_data['language'] = lang_code
    await show_main_menu(update, context)
    return ConversationHandler.END

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome = get_text(context, 'welcome_message', user_full_name=user.full_name)
    keyboard = [
        [InlineKeyboardButton(get_text(context, 'btn_book_appointment'), callback_data='book')],
        [InlineKeyboardButton(get_text(context, 'btn_my_bookings'), callback_data='my_bookings')],
        [InlineKeyboardButton(get_text(context, 'btn_info_and_faq'), callback_data='info')],
        [InlineKeyboardButton(get_text(context, 'btn_our_location'), callback_data='location')],
        [InlineKeyboardButton(get_text(context, 'btn_reviews'), url=REVIEWS_CHANNEL_LINK)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(welcome, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome, reply_markup=reply_markup)

async def booking_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = []
    today = datetime.datetime.now(TIMEZONE).date()
    for i in range(7):
        day = today + datetime.timedelta(days=i)
        keyboard.append([InlineKeyboardButton(day.strftime("%d.%m.%Y"), callback_data=f"day_{day.isoformat()}")])
    keyboard.append([InlineKeyboardButton(get_text(context, 'btn_main_menu'), callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(get_text(context, 'select_day_for_booking'), reply_markup=reply_markup)
    return BOOKING_SELECT_DAY

async def select_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day_str = query.data.split('_')[1]
    context.user_data['booking_day'] = day_str
    # Show time slots 8:00 - 17:00 every 30 min
    keyboard = []
    date_obj = datetime.date.fromisoformat(day_str)
    now = datetime.datetime.now(TIMEZONE)
    start = datetime.datetime.combine(date_obj, datetime.time(8,0,tzinfo=TIMEZONE))
    end = datetime.datetime.combine(date_obj, datetime.time(17,0,tzinfo=TIMEZONE))
    slot = start
    while slot <= end:
        time_str = slot.strftime("%H:%M")
        # Check if booked
        booked = booked_slots.get(day_str, {}).get(time_str)
        if booked:
            text = f"{time_str} (Занято)"
        elif slot < now:
            text = f"{time_str} (Минуло)"
        else:
            text = time_str
        keyboard.append([InlineKeyboardButton(text, callback_data=f"time_{time_str}")])
        slot += datetime.timedelta(minutes=30)
    keyboard.append([InlineKeyboardButton(get_text(context, 'btn_main_menu'), callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(get_text(context, 'select_time_for_booking', date=date_obj.strftime("%d.%m.%Y")), reply_markup=reply_markup)
    return BOOKING_SELECT_TIME

async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    time_str = query.data.split('_')[1]
    day_str = context.user_data.get('booking_day')
    if not day_str:
        await query.edit_message_text("Ошибка. Пожалуйста, начните заново /start")
        return ConversationHandler.END
    # Проверка доступности
    if booked_slots.get(day_str, {}).get(time_str):
        await query.answer("Этот слот уже занят", show_alert=True)
        return BOOKING_SELECT_TIME
    # Сохраняем время
    context.user_data['booking_time'] = time_str
    await query.edit_message_text(get_text(context, 'enter_name'))
    return BOOKING_ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isalpha() or len(text) < 2:
        await update.message.reply_text(get_text(context, 'error_invalid_name'))
        return BOOKING_ASK_NAME
    context.user_data['booking_name'] = text
    await update.message.reply_text(get_text(context, 'enter_phone'))
    return BOOKING_ASK_PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.startswith('+') or not text[1:].isdigit() or len(text) < 10:
        await update.message.reply_text(get_text(context, 'error_invalid_phone'))
        return BOOKING_ASK_PHONE
    context.user_data['booking_phone'] = text
    day = context.user_data['booking_day']
    time = context.user_data['booking_time']
    name = context.user_data['booking_name']
    confirm_text = (
        f"Проверьте данные:\nДата: {datetime.date.fromisoformat(day).strftime('%d.%m.%Y')}\n"
        f"Время: {time}\nИмя: {name}\nТелефон: {text}\n\n"
        "Все верно? (да/нет)"
    )
    await update.message.reply_text(confirm_text)
    return BOOKING_CONFIRM

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text not in ['да', 'yes', 'так', 'ага']:
        await update.message.reply_text(get_text(context, 'process_cancelled'))
        return ConversationHandler.END
    day = context.user_data['booking_day']
    time = context.user_data['booking_time']
    name = context.user_data['booking_name']
    phone = context.user_data['booking_phone']
    # Сохраняем бронь
    if day not in booked_slots:
        booked_slots[day] = {}
    booked_slots[day][time] = {
        'name': name,
        'phone': phone,
        'user_id': update.effective_user.id,
    }
    # Отправка уведомления админу
    msg_admin = (
        f"Новая запись:\nКлиент: {name}\n"
        f"Телефон: {phone}\nДата: {datetime.date.fromisoformat(day).strftime('%d.%m.%Y')}\n"
        f"Время: {time}"
    )
    await context.bot.send_message(ADMIN_CHAT_ID, msg_admin)
    await update.message.reply_text(get_text(context, 'booking_confirmed', date=datetime.date.fromisoformat(day).strftime('%d.%m.%Y'), time=time, name=name))
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text(context, 'process_cancelled'))
    return ConversationHandler.END

async def info_and_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(get_text(context, 'info_faq'))

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(get_text(context, 'our_location_address'))

async def my_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_id = update.effective_user.id
    user_bookings = []
    for day, times in booked_slots.items():
        for time, info in times.items():
            if info.get('user_id') == user_id:
                user_bookings.append(f"{day} в {time}")
    if not user_bookings:
        text = get_text(context, 'no_active_bookings')
    else:
        text = "Ваши записи:\n" + "\n".join(user_bookings)
    await update.callback_query.edit_message_text(text)

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_language, pattern='^lang_')],
        states={
            LANG_SELECTION: [CallbackQueryHandler(set_language, pattern='^lang_')],
            BOOKING_SELECT_DAY: [CallbackQueryHandler(select_day, pattern='^day_')],
            BOOKING_SELECT_TIME: [CallbackQueryHandler(select_time, pattern='^time_')],
            BOOKING_ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            BOOKING_ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            BOOKING_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_booking)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(CommandHandler('start', start))  # <- отдельный обработчик /start
    app.add_handler(conv_handler)

    # Меню вне конверсейшена
    app.add_handler(CallbackQueryHandler(booking_start, pattern='^book$'))
    app.add_handler(CallbackQueryHandler(my_bookings, pattern='^my_bookings$'))
    app.add_handler(CallbackQueryHandler(info_and_faq, pattern='^info$'))
    app.add_handler(CallbackQueryHandler(location, pattern='^location$'))
    app.add_handler(CommandHandler('cancel', cancel))

    app.run_polling()

if __name__ == '__main__':
    main()
