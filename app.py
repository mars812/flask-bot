# app.py (Flask + Webhook версия твоего бота)
from flask import Flask, request
import telebot
import json
import datetime
import math
from calendar_handler import generate_calendar, handle_calendar_callback
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
import os

TOKEN = os.environ.get("TELEGRAM_API_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

ADMIN_ID = 374897465
user_data = {}

with open("car_photos.json", "r") as f:
    car_photos = json.load(f)

categories = [
    ("compact", "🚗 Компактные авто\n✅ Идеально для города...", "class_compact"),
    ("sedan", "🚘 Седаны среднего класса\n✅ Комфортные...", "class_sedan"),
    ("crossover", "🚙 Паркетники \n✅ Высокий клиренс...", "class_crossover"),
    ("suv", "🚐 SUV и минивены (7 мест)\n✅ Для семьи...", "class_suv")
]

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid request', 403

@app.route('/')
def index():
    return 'Bot is running ✅'

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'history': []}
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚗 Приступить к бронированию", callback_data="start_booking"))
    msg = bot.send_message(chat_id, "Привет! Давайте начнём бронирование.", reply_markup=markup)
    user_data[chat_id]['history'].append(msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "start_booking")
def handle_start_booking(call):
    chat_id = call.message.chat.id
    clear_history(chat_id)
    markup = InlineKeyboardMarkup()
    for _, caption, callback in categories:
        markup.add(InlineKeyboardButton(caption.split("\n")[0], callback_data=callback))
    bot.send_message(chat_id, "Выберите категорию:", reply_markup=markup)

def clear_history(chat_id):
    for msg_id in user_data.get(chat_id, {}).get('history', []):
        try:
            bot.delete_message(chat_id, msg_id)
        except: pass
    user_data[chat_id]['history'] = []

@bot.callback_query_handler(func=lambda call: call.data.startswith("class_"))
def choose_class(call):
    chat_id = call.message.chat.id
    class_selected = call.data.split("_", 1)[1]
    user_data[chat_id]['selected_class'] = class_selected
    show_cars_by_class(chat_id, class_selected, page=1)

def show_cars_by_class(chat_id, car_class, page=1):
    cars = [name for name, data in car_photos.items() if data['class'] == car_class]
    cars.sort()
    per_page = 3
    start = (page - 1) * per_page
    end = start + per_page
    cars_on_page = cars[start:end]

    for car_name in cars_on_page:
        data = car_photos[car_name]
        caption = f"🚗 {car_name}\n{data['description']}\n💸 800–400฿/сутки"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📅 Выбрать даты", callback_data=f"book_{car_name}"))
        msg = bot.send_message(chat_id, caption, reply_markup=markup)
        user_data[chat_id]['history'].append(msg.message_id)

    total_pages = math.ceil(len(cars) / per_page)
    nav = InlineKeyboardMarkup()
    if page > 1:
        nav.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"cars_{car_class}_page_{page - 1}"))
    if end < len(cars):
        nav.add(InlineKeyboardButton("➡️ Далее", callback_data=f"cars_{car_class}_page_{page + 1}"))
    msg = bot.send_message(chat_id, f"Страница {page} из {total_pages}", reply_markup=nav)
    user_data[chat_id]['history'].append(msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cars_"))
def handle_car_page(call):
    chat_id = call.message.chat.id
    _, car_class, _, page = call.data.split("_")
    page = int(page)
    clear_history(chat_id)
    show_cars_by_class(chat_id, car_class, page)

@bot.callback_query_handler(func=lambda call: call.data.startswith("book_"))
def choose_car(call):
    chat_id = call.message.chat.id
    car_name = call.data.split("_", 1)[1]
    user_data[chat_id]['car'] = car_name
    clear_history(chat_id)
    today = datetime.date.today()
    markup = generate_calendar("start", today.year, today.month, chat_id, user_data)
    msg = bot.send_message(chat_id, "📅 Выбери дату начала аренды:", reply_markup=markup)
    user_data[chat_id]['history'].append(msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cal_") or call.data.startswith("prev") or call.data.startswith("next") or call.data.startswith("delivery"))
def calendar_callbacks(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {}
    handle_calendar_callback(call, user_data, bot)

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url="https://flask-bot-7308.onrender.com/webhook")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
