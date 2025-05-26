from flask import Flask, request
import telebot


bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot is live!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid request', 403

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, "Привет! Бот запущен через Render и webhook ✅")
