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
    ("compact.jpg", "🚗 Компактные авто\n✅ Идеально для города...", "class_compact"),
    ("sedan.jpg", "🚘 Седаны", "class_sedan"),
    ("parket.png", "🚙 Паркетники", "class_crossover"),
    ("7-seat.jpeg", "🚐 Минивены", "class_suv")
]

def safe_delete(cid, msg_id):
    try: bot.delete_message(cid, msg_id)
    except: pass
        
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

@bot.callback_query_handler(func=lambda c: c.data == "start_booking")
def step2(call):
    cid = call.message.chat.id
    for m in user_data[cid].get('history', []): safe_delete(cid, m)
    user_data[cid]['history'] = []
    with open("2.png", "rb") as photo:
        msg = bot.send_photo(cid, photo)
        user_data[cid]['history'].append(msg.message_id)
    kb = InlineKeyboardMarkup()
    kb.add(*[InlineKeyboardButton(title, callback_data=cb) for _, title, cb in categories])
    bot.send_message(cid, "Выберите категорию авто:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("class_"))
def show_cars(call):
    cid = call.message.chat.id
    for m in user_data[cid].get('history', []): safe_delete(cid, m)
    user_data[cid]['history'] = []
    car_class = call.data.split("_", 1)[1]
    cars = [name for name, data in car_photos.items() if data['class'] == car_class]
    cars.sort()
    per_page = 3
    page = 1
    show_cars_page(cid, car_class, cars, page, per_page)

def show_cars_page(cid, car_class, cars, page, per_page):
    start = (page - 1) * per_page
    end = start + per_page
    cars_on_page = cars[start:end]
    for name in cars_on_page:
        data = car_photos[name]
        with open(data['cover'], 'rb') as img:
            caption = f"🚗 {name}\n{data['description']}"
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🗓️ Выбрать даты", callback_data=f"book_{name}"))
            msg = bot.send_photo(cid, img, caption=caption, reply_markup=kb)
            user_data[cid]['history'].append(msg.message_id)
    nav = InlineKeyboardMarkup()
    if page > 1:
        nav.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"cars_{car_class}_page_{page - 1}"))
    if end < len(cars):
        nav.add(InlineKeyboardButton("➡️ Далее", callback_data=f"cars_{car_class}_page_{page + 1}"))
    nav_msg = bot.send_message(cid, f"Страница {page} из {math.ceil(len(cars)/per_page)}", reply_markup=nav)
    user_data[cid]['history'].append(nav_msg.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cars_"))
def handle_page_nav(call):
    cid = call.message.chat.id
    _, car_class, _, page = call.data.split("_")
    cars = [name for name, data in car_photos.items() if data['class'] == car_class]
    for m in user_data[cid].get('history', []): safe_delete(cid, m)
    user_data[cid]['history'] = []
    show_cars_page(cid, car_class, cars, int(page), 3)

@bot.callback_query_handler(func=lambda c: c.data.startswith("book_"))
def handle_booking(call):
    cid = call.message.chat.id
    car = call.data.split("_", 1)[1]
    user_data[cid]['car'] = car
    for m in user_data[cid].get('history', []): safe_delete(cid, m)
    user_data[cid]['history'] = []
    markup = generate_calendar("start", chat_id=cid, user_data=user_data)
    msg = bot.send_message(cid, "🗓️ Выбери дату начала аренды:", reply_markup=markup)
    user_data[cid]['history'].append(msg.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cal_") or c.data.startswith("prev") or c.data.startswith("next") or c.data.startswith("delivery"))
def calendar_handler(call):
    handle_calendar_callback(call, user_data, bot)

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
