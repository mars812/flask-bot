# app.py — Flask + Telebot Webhook-бот с полной логикой
import os
import json
import datetime
import math
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from calendar_handler import generate_calendar, handle_calendar_callback

API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN") or "<ТОКЕН>"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") or "https://<render-subdomain>.onrender.com/webhook"
ADMIN_ID = 374897465

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

user_data = {}
with open("car_photos.json", "r") as f:
    car_photos = json.load(f)

categories = [
    ("compact.jpg", "🚗 Компактные авто\n✅ Идеально для города. Экономичный расход, малые габариты и удобная парковка.", "class_compact"),
    ("sedan.jpg", "🚘 Седаны среднего класса\n✅ Комфортные, вместительный багажник. Отлично для дальних поездок. Экономичный расход, малые габариты и удобная парковка","class_sedan"),
    ("parket.png", "🚙 Паркетники \n✅ Высокий клиренс. Могут позволить себе немного больше","class_crossover"),
    ("7-seat.jpeg", "🚐 SUV и минивены (7 мест)\n✅ Для семьи и большой компании", "class_suv")
]

def safe_delete(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print("Ошибка при удалении сообщения:", e)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    for msg_id in user_data[chat_id].get('history', []):
        safe_delete(chat_id, msg_id)
    user_data[chat_id]['history'] = []

    with open("1.png", "rb") as step_image:
        msg = bot.send_photo(chat_id, step_image)
        user_data[chat_id]['history'].append(msg.message_id)

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚗 Приступить к бронированию", callback_data="start_booking"))
    msg2 = bot.send_message(chat_id, "Следующим шагом выбираем категорию автомобиля. Готовы начать?", reply_markup=markup)
    user_data[chat_id]['history'].append(msg2.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "start_booking")
def handle_start_booking(call):
    chat_id = call.message.chat.id

    for msg_id in user_data[chat_id].get('history', []):
        safe_delete(chat_id, msg_id)
    user_data[chat_id]['history'] = []

    with open("2.png", "rb") as step_image:
        msg = bot.send_photo(chat_id, step_image)
#        caption = "📍 *Шаг2 из 5*\n\nВыберит интересующий Вас формать из списка ниже.\n⬇️⬇️⬇️"
#        msg = bot.send_photo(chat_id, step_image, caption=caption, parse_mode="Markdown")
        user_data[chat_id]['history'].append(msg.message_id)


    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("⬅️ Назад", callback_data="go_to_step1"),
        InlineKeyboardButton("📋 Открыть список категорий авто", callback_data="categories_page_1")
    )
    msg2 = bot.send_message(chat_id, "Выберите действие", reply_markup=markup)
    user_data[chat_id]['history'].append(msg2.message_id)
    
@bot.callback_query_handler(func=lambda call: call.data == "categories_page_1")
def categories_page_1(call):
    chat_id = call.message.chat.id
    for msg_id in user_data[chat_id].get('history', []):
        safe_delete(chat_id, msg_id)
    user_data[chat_id]['history'] = []

    for i in range(4):  # compact и sedan
        img_path, caption, callback = categories[i]
        with open(img_path, "rb") as photo:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("✅ Выбрать", callback_data=callback))
            msg = bot.send_photo(chat_id, photo, caption=caption, reply_markup=markup)
            user_data[chat_id]['history'].append(msg.message_id)

def generate_summary(chat_id):
    data = user_data.get(chat_id, {})
    lines = []
    if 'car' in data:
        lines.append(f"🚘 *Авто:* {data['car']}")
    if 'start_obj' in data:
        lines.append(f"📅 *С:* {data['start_obj'].strftime('%d.%m.%Y')}")
    if 'end_obj' in data:
        lines.append(f"📅 *По:* {data['end_obj'].strftime('%d.%m.%Y')}")
    if 'delivery' in data:
        delivery = "🏠 Дом / Отель" if data['delivery'] == "home" else "✈️ Аэропорт"
        lines.append(f"📍 *Доставка:* {delivery}")
    if 'contact' in data:
        lines.append(f"📱 *Контакт:* {data['contact']}")
    return "\n".join(lines) if lines else "📭 Пока ничего не выбрано."

@bot.callback_query_handler(func=lambda call: call.data == "go_to_step1")
def go_back_to_step1(call):
    chat_id = call.message.chat.id
    for msg_id in user_data[chat_id].get('history', []):
        safe_delete(chat_id, msg_id)
    user_data[chat_id]['history'] = []

    with open("1.png", "rb") as step_image:
        msg = bot.send_photo(chat_id, step_image)
        user_data[chat_id]['history'].append(msg.message_id)

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚗 Приступить к бронированию", callback_data="start_booking"))
    msg2 = bot.send_message(chat_id, "Следующим шагом выберете категорию автомобиля. Готовы начать?", reply_markup=markup)
    user_data[chat_id]['history'].append(msg2.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("class_"))
def choose_class(call):
    chat_id = call.message.chat.id
    class_selected = call.data.split("_", 1)[1]
    for msg_id in user_data[chat_id].get('history', []):
        safe_delete(chat_id, msg_id)
    user_data[chat_id]['history'] = []
    

    with open("3.png", "rb") as step_image:
        caption = "📍 *Шаг 3 из 5*\n\nВыберите автомобиль из списка ниже.\n⬇️⬇️⬇️"
        msg = bot.send_photo(chat_id, step_image, caption=caption, parse_mode="Markdown")
        user_data[chat_id]['history'].append(msg.message_id)
    show_cars_by_class(chat_id, class_selected, page=1, with_navigation=True)#show step-3 image
    
@bot.callback_query_handler(func=lambda call: call.data.startswith("cars_"))
def handle_car_page(call):
    chat_id = call.message.chat.id
    try:
        _, car_class, _, page = call.data.split("_")
        page = int(page)
    except:
        return  # безопасный выход при некорректных данных

    for msg_id in user_data[chat_id].get('history', []):
        safe_delete(chat_id, msg_id)
    user_data[chat_id]['history'] = []

    show_cars_by_class(chat_id, car_class, page, with_navigation=True)


# 🔇 Вывод машин по классу из JSON
def show_cars_by_class(chat_id, car_class, page, with_navigation=True):
    cars = [name for name, data in car_photos.items() if data['class'] == car_class]
    cars.sort()
    per_page = 3
    start = (page - 1) * per_page
    end = start + per_page
    cars_on_page = cars[start:end]

    for car_name in cars_on_page:
        data = car_photos[car_name]
        with open(data['cover'], 'rb') as photo:
            caption = f"🚗 {car_name}\n{data['description']}\n💸 800–400฿/сутки (чем дольше, тем дешевле)"
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📅 Выбрать даты", callback_data=f"book_{car_name}"))
            msg = bot.send_photo(chat_id, photo, caption=caption, reply_markup=markup)
            user_data[chat_id]['history'].append(msg.message_id)

    if with_navigation:
        total_pages = math.ceil(len(cars) / per_page)
        nav = InlineKeyboardMarkup()
        if page > 1:
            nav.add(InlineKeyboardButton("⬅️ Возврат к прошлому списку", callback_data=f"cars_{car_class}_page_{page - 1}"))
        if end < len(cars):
            nav.add(InlineKeyboardButton("➡️ Еще 3 авто", callback_data=f"cars_{car_class}_page_{page + 1}"))
        nav.add(InlineKeyboardButton("🔙 К выбору категории авто", callback_data="go_to_categories"))
        nav_msg = bot.send_message(chat_id, f"Страница {page} из {total_pages}", reply_markup=nav)
        user_data[chat_id]['history'].append(nav_msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "go_to_categories")
def return_to_categories(call):
    chat_id = call.message.chat.id
    for msg_id in user_data[chat_id].get("history", []):
        safe_delete(chat_id, msg_id)
    user_data[chat_id]["history"] = []

    with open("2.png", "rb") as step_image:
        msg = bot.send_photo(chat_id, step_image)
        user_data[chat_id]["history"].append(msg.message_id)

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📋 Список категорий авто", callback_data="categories_page_1")
    )
    user_data[chat_id]["history"].append(
        bot.send_message(chat_id, "Вернулись к выбору категории авто:", reply_markup=markup).message_id
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("book_"))
def choose_car(call):
    chat_id = call.message.chat.id
    car_name = call.data.split("_", 1)[1]
    user_data[chat_id] = user_data.get(chat_id, {})
    user_data[chat_id]['car'] = car_name

    # Удаляем старые сообщения
    for msg_id in user_data[chat_id].get("history", []):
        safe_delete(chat_id, msg_id)
    user_data[chat_id]['history'] = []
    # Показываем фото + календарь в reply_markup
    with open("calendar_start.png", "rb") as photo:
        today = datetime.date.today()
        markup = generate_calendar("start", today.year, today.month, chat_id, user_data)
        msg = bot.send_photo(
            chat_id,
            photo,
            caption="📅 Выбери дату начала аренды:",
            reply_markup=markup
        )
       
        user_data[chat_id]['history'].append(msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("cal_") or call.data.startswith("prev") or call.data.startswith("next") or call.data.startswith("delivery"))
def handle_all_calendar_callbacks(call):
    chat_id = call.from_user.id
    if chat_id not in user_data:
        user_data[chat_id] = {}
    handle_calendar_callback(call, user_data, bot)

@bot.callback_query_handler(func=lambda call: call.data.startswith("contact_"))
def handle_contact_choice(call):
    chat_id = call.message.chat.id
    contact_type = call.data.split("_", 1)[1]

    if contact_type == "telegram":
        username = call.from_user.username
        if username:
            user_data[chat_id]['contact'] = "@" + username
            finalize_booking(chat_id)
        else:
            bot.edit_message_text(chat_id, call.message.message_id, "❌ Укажи username в Telegram и попробуй снова.")

    elif contact_type == "whatsapp":
        user_data[chat_id]['phone_input'] = ""
        user_data[chat_id]['awaiting_phone'] = True
        user_data[chat_id]['phone_msg_id'] = None

        markup = InlineKeyboardMarkup()
        for row in [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["+", "0", "DEL"], ["✅ Готово"]]:
            markup.row(*[InlineKeyboardButton(btn, callback_data=f"num_{btn}") for btn in row])

        msg = bot.send_message(chat_id, "📞 Введи номер WhatsApp:", reply_markup=markup)
        user_data[chat_id]['phone_msg_id'] = msg.message_id
        user_data[chat_id]['history'].append(msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("num_"))
def handle_inline_number(call):
    chat_id = call.message.chat.id
    digit = call.data.split("_", 1)[1]
    data = user_data[chat_id]

    if digit == "DEL":
        data['phone_input'] = data['phone_input'][:-1]
    elif digit == "✅ Готово":
        final = data.get('phone_input', '')
        if final:
            data['contact'] = final
            data['awaiting_phone'] = False
            for msg_id in data.get('history', []):
                safe_delete(chat_id, msg_id)
            data['history'] = []
            finalize_booking(chat_id)
        else:
            bot.answer_callback_query(call.id, "Номер пуст.")
        return
    else:
        data['phone_input'] += digit

    max_length = 15
    padded = data['phone_input'] + '•' * (max_length - len(data['phone_input']))
    phone_display = f"Номер: {padded}\n\nНажимай кнопки ниже для ввода номера"

    try:
        bot.edit_message_text(phone_display, chat_id, data['phone_msg_id'], reply_markup=call.message.reply_markup)
    except:
        pass

def finalize_booking(chat_id):
    data = user_data[chat_id]
    delivery = "🏠 Отель / Дом / Вилла" if data.get('delivery') == 'home' else "✈️ Аэропорт"
    start = data.get('start_obj')
    end = data.get('end_obj')
    start_str = start.strftime("%d.%m.%Y")
    end_str = end.strftime("%d.%m.%Y")
    deposit = 5000 if "Toyota" in data['car'] or "Honda" in data['car'] else 10000
    delivery_fee = 1000
    total = data['total_price'] + deposit + delivery_fee

    text = f"✅ Новая заявка:\n\n"
    text += f"🚘 Авто: {data['car']}\n"
    text += f"📅 Аренда: с {start_str} по {end_str} ({data['days']} дней)\n"
    text += f"📍 Доставка+Возврат: {delivery}\n"
    text += f"📱 Контакт: {data['contact']}\n\n"
    text += f"💰 Аренда: {data['total_price']} ฿\n"
    text += f"🚕 Доставка: {delivery_fee} ฿\n"
    text += f"🔒 Депозит: {deposit} ฿\n"
    text += f"💳 Итого при получении: {total} ฿\n\n"
    text += "ℹ️ Дополнительно:\n"
    text += "— Страховка включена, франшиза 5,000 ฿ (компакт/седан) или 10,000 ฿ (SUV/паркетник)\n"
    text += "— Передвигаться можно по всему Таиланду, кроме южных границ\n"
    text += "— Управлять могут все, у кого есть права\n"
    text += "— Для брони: фото загранпаспорта и ВУ. Никаких предоплат.\n\n"
    text += "Мы получили вашу заявку и скоро с вами свяжемся для подтверждения."

    bot.send_message(chat_id, text, reply_markup=ReplyKeyboardRemove())
    bot.send_message(ADMIN_ID, f"🔔 Заявка от @{bot.get_chat(chat_id).username or chat_id}:\n\n{text}")

@app.route('/')
def index():
    return 'Bot is alive!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid', 403

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
