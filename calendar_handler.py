# app.py — Flask + Telebot (webhook) интеграция
import os
import json
import datetime
import math
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from calendar_handler import generate_calendar, handle_calendar_callback

# === НАСТРОЙКИ ===
API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN") or "7671997445:AAEyZlmmYLOeVOD8PalzgUTjdeYhGs3bEfE"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") or "https://flask-bot-xxxx.onrender.com/webhook"
ADMIN_ID = 374897465

# === ИНИЦИАЛИЗАЦИЯ ===
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# === ДАННЫЕ ===
user_data = {}
with open("car_photos.json", "r") as f:
    car_photos = json.load(f)

categories = [
    ("compact.jpg", "🚗 Компактные авто", "class_compact"),
    ("sedan.jpg", "🚘 Седаны", "class_sedan"),
    ("parket.png", "🚙 Паркетники", "class_crossover"),
    ("7-seat.jpeg", "🚐 Минивены", "class_suv")
]

# === ХЕЛПЕР ===
def safe_delete(chat_id, msg_id):
    try:
        bot.delete_message(chat_id, msg_id)
    except: pass

# === ХЭНДЛЕРЫ ===
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'history': []}
    with open("1.png", "rb") as img:
        msg = bot.send_photo(chat_id, img)
        user_data[chat_id]['history'].append(msg.message_id)
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🚗 Начать", callback_data="start_booking"))
    msg = bot.send_message(chat_id, "Готовы выбрать авто?", reply_markup=kb)
    user_data[chat_id]['history'].append(msg.message_id)

@bot.callback_query_handler(func=lambda c: c.data == "start_booking")
def step2(call):
    cid = call.message.chat.id
    for m in user_data[cid].get('history', []): safe_delete(cid, m)
    user_data[cid]['history'] = []
    with open("2.png", "rb") as img:
        msg = bot.send_photo(cid, img)
        user_data[cid]['history'].append(msg.message_id)
    kb = InlineKeyboardMarkup()
    for img, title, cb in categories:
        kb.add(InlineKeyboardButton(title, callback_data=cb))
    bot.send_message(cid, "Выберите категорию авто:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("class_"))
def show_cars(call):
    cid = call.message.chat.id
    for m in user_data[cid].get('history', []): safe_delete(cid, m)
    user_data[cid]['history'] = []
    selected_class = call.data.split("_", 1)[1]
    cars = [name for name, data in car_photos.items() if data['class'] == selected_class]
    cars.sort()
    for name in cars:
        data = car_photos[name]
        with open(data['cover'], 'rb') as img:
            caption = f"🚗 {name}\n{data['description']}"
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("📅 Выбрать даты", callback_data=f"book_{name}"))
            msg = bot.send_photo(cid, img, caption=caption, reply_markup=kb)
            user_data[cid]['history'].append(msg.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("book_"))
def start_date(call):
    cid = call.message.chat.id
    car = call.data.split("_", 1)[1]
    user_data[cid]['car'] = car
    for m in user_data[cid].get('history', []): safe_delete(cid, m)
    user_data[cid]['history'] = []
    markup = generate_calendar("start", chat_id=cid, user_data=user_data)
    msg = bot.send_message(cid, "📅 Выбери дату начала аренды:", reply_markup=markup)
    user_data[cid]['history'].append(msg.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cal_") or c.data.startswith("prev") or c.data.startswith("next") or c.data.startswith("delivery"))
def calendar_handler(call):
    handle_calendar_callback(call, user_data, bot)

# === FLASK ===
@app.route('/')
def index():
    return 'Bot is running.'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid request', 403

# === MAIN ===
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
