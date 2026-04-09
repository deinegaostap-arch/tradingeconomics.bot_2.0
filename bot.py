import requests
import time
from datetime import datetime
import pytz
import telebot

# === НАСТРОЙКИ ===
TOKEN = "8628795213:AAFET0_j5JCXzJn7lf1gJ114GVil5vuZtyY"
API_KEY = "f6759ba66c1a4d9:0j77bu0f2f7hail"
CHAT_ID = "536264248"

bot = telebot.TeleBot(TOKEN)
tz = pytz.timezone("Europe/Copenhagen")

# === ФУНКЦИИ ===

def get_today_news():
    url = f"https://api.tradingeconomics.com/calendar?c={API_KEY}"
    data = requests.get(url).json()

    today = datetime.now(tz).date()
    news = []

    for item in data:
        if item.get("Importance") != 3:
            continue

        date = datetime.fromisoformat(item['Date'].replace("Z", ""))
        date = date.replace(tzinfo=pytz.utc).astimezone(tz)

        if date.date() == today:
            item["local_time"] = date.strftime("%H:%M")
            news.append(item)

    return news


def get_holidays():
    url = f"https://api.tradingeconomics.com/holiday?c={API_KEY}"
    data = requests.get(url).json()

    today = datetime.now(tz).date()
    holidays = []

    for item in data:
        date = datetime.fromisoformat(item['Date'].replace("Z", ""))
        date = date.date()

        if date == today:
            holidays.append(item['Country'])

    return list(set(holidays))


def send_morning_report():
    print("Sending morning report...")

    news = get_today_news()
    holidays = get_holidays()

    message = "🌍 *Daily Macro Briefing*\n\n"

    # Holidays
    if holidays:
        message += "🏦 *Bank Holidays:*\n"
        for h in holidays:
            message += f"• {h}\n"
        message += "\n"

    # News
    if not news:
        message += "✅ No high-impact economic events scheduled today."
    else:
        message += "📊 *High Impact Events Today:*\n\n"
        for n in news:
            message += f"🕒 {n['local_time']} | {n['Country']}\n{n['Event']}\n\n"

    bot.send_message(CHAT_ID, message, parse_mode="Markdown")


def check_releases():
    sent = set()

    while True:
        try:
            news = get_today_news()
            now = datetime.now(tz)

            for n in news:
                event_time = datetime.strptime(n['local_time'], "%H:%M")
                event_time = event_time.replace(
                    year=now.year, month=now.month, day=now.day, tzinfo=tz
                )

                diff = abs((now - event_time).total_seconds())

                if diff < 90:
                    key = n['Event']

                    if key not in sent:
                        msg = (
                            f"📢 *{n['Event']}*\n"
                            f"🌍 {n['Country']}\n\n"
                            f"Actual: {n['Actual']}\n"
                            f"Forecast: {n['Forecast']}\n"
                            f"Previous: {n['Previous']}"
                        )

                        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                        sent.add(key)

            time.sleep(30)

        except Exception as e:
            print("Error in check_releases:", e)
            time.sleep(60)


def scheduler():
    last_sent = None

    while True:
        try:
            now = datetime.now(tz)

            # только будни
            if now.weekday() < 5:
                if now.hour == 8 and last_sent != now.date():
                    send_morning_report()
                    last_sent = now.date()

            time.sleep(30)

        except Exception as e:
            print("Error in scheduler:", e)
            time.sleep(60)


# === ЗАПУСК ===
import threading

print("Bot started...")

threading.Thread(target=check_releases).start()
threading.Thread(target=scheduler).start()

bot.infinity_polling()