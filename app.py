from flask import Flask, request
import telebot
import os

API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN")
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

# Обработка команды /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, "Привет! Бот запущен через Render и webhook ✅")

# Установка webhook — только при локальном запуске (на всякий случай)
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url="https://flask-bot-7308.onrender.com/webhook")  # заменишь на свой URL
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

