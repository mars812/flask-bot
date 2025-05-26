import calendar
import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def generate_calendar(state, year=None, month=None, chat_id=None, user_data=None):
    today = datetime.date.today()
    year = year or today.year
    month = month or today.month

    markup = InlineKeyboardMarkup(row_width=7)

    prev_btn = InlineKeyboardButton(" " if (year < today.year or (year == today.year and month <= today.month)) else "<",
                                     callback_data="ignore" if (year < today.year or (year == today.year and month <= today.month)) else f"prev_{month}_{year}_{state}")
    next_btn = InlineKeyboardButton(">", callback_data=f"next_{month}_{year}_{state}")
    title_btn = InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data="ignore")
    markup.row(prev_btn, title_btn, next_btn)

    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    markup.add(*[InlineKeyboardButton(day, callback_data="ignore") for day in week_days])

    for week in calendar.monthcalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                date_obj = datetime.date(year, month, day)
                date_str = date_obj.strftime("%Y-%m-%d")
                if state == "start" and date_obj < today:
                    row.append(InlineKeyboardButton(" ", callback_data="ignore"))
                elif state == "end" and user_data and chat_id in user_data and 'start_date' in user_data[chat_id]:
                    if date_obj <= datetime.datetime.strptime(user_data[chat_id]['start_date'], "%Y-%m-%d").date():
                        row.append(InlineKeyboardButton(" ", callback_data="ignore"))
                    else:
                        row.append(InlineKeyboardButton(str(day), callback_data=f"cal_{date_str}_{state}"))
                else:
                    row.append(InlineKeyboardButton(str(day), callback_data=f"cal_{date_str}_{state}"))
        markup.add(*row)
    return markup


def handle_calendar_callback(call, user_data, bot):
    chat_id = call.message.chat.id
    data = call.data.split("_")

    if data[0] == "cal" and len(data) == 3:
        selected_date, state = data[1], data[2]

        if state == "start":
            user_data[chat_id] = user_data.get(chat_id, {})
            user_data[chat_id]['start_date'] = selected_date
            start_dt = datetime.datetime.strptime(selected_date, "%Y-%m-%d")

            for msg_id in user_data[chat_id].get("history", []):
                try:
                    bot.delete_message(chat_id, msg_id)
                except:
                    pass
            user_data[chat_id]['history'] = []

            bot.send_message(chat_id, f"📅 Дата начала аренды выбрана: *{selected_date}*", parse_mode="Markdown")

            markup = generate_calendar("end", start_dt.year, start_dt.month, chat_id, user_data)
            msg_calendar = bot.send_message(chat_id, "📅 Теперь выбери дату окончания аренды:", reply_markup=markup)
            user_data[chat_id]['history'].append(msg_calendar.message_id)

        elif state == "end":
            user_data[chat_id]['end_date'] = selected_date
            start_date = datetime.datetime.strptime(user_data[chat_id]['start_date'], "%Y-%m-%d")
            end_date = datetime.datetime.strptime(user_data[chat_id]['end_date'], "%Y-%m-%d")
            delta_days = (end_date - start_date).days

            if delta_days <= 0:
                bot.answer_callback_query(call.id, "❌ Дата окончания должна быть позже даты начала.")
                return

            if delta_days <= 4:
                price_per_day = 800
            elif delta_days <= 14:
                price_per_day = 750
            elif delta_days <= 30:
                price_per_day = 700
            else:
                price_per_day = 400

            total_price = delta_days * price_per_day

            user_data[chat_id]['days'] = delta_days
            user_data[chat_id]['price_per_day'] = price_per_day
            user_data[chat_id]['total_price'] = total_price
            user_data[chat_id]['start_obj'] = start_date
            user_data[chat_id]['end_obj'] = end_date

            for msg_id in user_data[chat_id].get("history", []):
                try:
                    bot.delete_message(chat_id, msg_id)
                except:
                    pass
            user_data[chat_id]['history'] = []

            msg = bot.send_message(chat_id,
                f"📦 Куда доставить авто?\n\n"
                "Нажми одну из кнопок ниже 👇",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🚗 По городу", callback_data="delivery_home"),
                    InlineKeyboardButton("✈️ Аэропорт", callback_data="delivery_airport")
                )
            )
            user_data[chat_id]['history'].append(msg.message_id)

    elif data[0] in ["prev", "next"] and len(data) == 4:
        month, year, state = int(data[1]), int(data[2]), data[3]
        delta = -1 if data[0] == "prev" else 1
        new_month = month + delta
        new_year = year + (new_month - 1) // 12 if new_month > 12 else year - 1 if new_month < 1 else year
        new_month = 1 if new_month > 12 else 12 if new_month < 1 else new_month

        markup = generate_calendar(state, new_year, new_month, chat_id, user_data)
        try:
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)
        except:
            pass

    elif call.data in ["delivery_home", "delivery_airport"]:
        delivery_type = "home" if call.data == "delivery_home" else "airport"
        user_data[chat_id]['delivery'] = delivery_type

        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass

        msg = bot.send_message(chat_id,
            "📞 Как с тобой связаться?\n\nВыбери удобный мессенджер:",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("📱 Telegram", callback_data="contact_telegram"),
                InlineKeyboardButton("📞 WhatsApp", callback_data="contact_whatsapp")
            )
        )
        user_data[chat_id]['history'].append(msg.message_id)
