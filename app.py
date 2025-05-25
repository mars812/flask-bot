from flask import Flask, request
import telebot

API_TOKEN = '7671997445:AAEyZlmmYLOeVOD8PalzgUTjdeYhGs3bEfE'
bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)

@app.route('/')
def index():
    return 'Бот работает!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    return '', 200

