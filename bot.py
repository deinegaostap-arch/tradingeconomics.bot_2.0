import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import pytz
import telebot

TOKEN = "8628795213:AAFET0_j5JCXzJn7lf1gJ114GVil5vuZtyY"
CHAT_ID = "536264248"

bot = telebot.TeleBot(TOKEN)
tz = pytz.timezone("Europe/Copenhagen")

BASE_URL = "https://www.forexfactory.com/calendar"

# ===== ПАРСИНГ =====

def get_calendar():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(BASE_URL, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("tr.calendar__row")

    events = []
    current_time = None

    for row in rows:
        time_cell = row.select_one(".calendar__time")
        impact = row.select_one(".calendar__impact span")

        if time_cell and time_cell.text.strip():
            current_time = time_cell.text.strip()

        if not impact:
            continue

        impact_class = impact.get("class", [])
        if "high" not in " ".join(impact_class).lower():
            continue

        currency = row.select_one(".calendar__currency")
        event = row.select_one(".calendar__event")
        actual = row.select_one(".calendar__actual")
        forecast = row.select_one(".calendar__forecast")
        previous = row.select_one(".calendar__previous")

        events.append({
            "time": current_time,
            "currency": currency.text.strip() if currency else "",
            "event": event.text.strip() if event else "",
            "actual": actual.text.strip() if actual else "",
            "forecast": forecast.text.strip() if forecast else "",
            "previous": previous.text.strip() if previous else "",
        })

    return events

# ===== УТРО =====

def send_morning():
    print("Morning report...")

    events = get_calendar()

    today = datetime.now(tz)

    message = "🌍 *DAILY MACRO BRIEFING*\n"
    message += today.strftime("%A, %d %B") + "\n\n"

    if today.weekday() >= 5:
        message += "Weekend — no major events."
        bot.send_message(CHAT_ID, message, parse_mode="Markdown")
        return

    if not events:
        message += "✅ No high-impact events today."
    else:
        message += "📊 *High Impact Events:*\n\n"
        for e in events:
            message += f"{e['time']} | {e['currency']}\n{e['event']}\n\n"

    bot.send_message(CHAT_ID, message, parse_mode="Markdown")

# ===== РЕЛИЗЫ =====

def check_news():
    sent = set()

    while True:
        try:
            events = get_calendar()

            for e in events:
                key = e['event'] + e['time']

                if e['actual'] and key not in sent:
                    msg = (
                        f"📢 *{e['event']}*\n"
                        f"🌍 {e['currency']}\n"
                        f"Actual: {e['actual']}\n"
                        f"Forecast: {e['forecast']}\n"
                        f"Previous: {e['previous']}"
                    )

                    bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                    sent.add(key)

            time.sleep(60)

        except Exception as e:
            print("Error:", e)
            time.sleep(120)

# ===== ПЛАНИРОВЩИК =====

def scheduler():
    last_sent = None

    while True:
        now = datetime.now(tz)

        if now.hour == 8 and last_sent != now.date():
            send_morning()
            last_sent = now.date()

        time.sleep(30)

# ===== ТЕСТ =====

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "✅ Bot is running")

# ===== ЗАПУСК =====

import threading

print("Bot started...")

threading.Thread(target=check_news).start()
threading.Thread(target=scheduler).start()

bot.infinity_polling(skip_pending=True)
