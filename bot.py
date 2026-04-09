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

def safe_request(url):
    try:
        response = requests.get(url)

        if response.status_code != 200:
            print("Bad response:", response.status_code)
            return []

        if not response.text:
            print("Empty response")
            return []

        return response.json()

    except Exception as e:
        print("Request error:", e)
        return []
        
def get_today_news():
    url = f"https://api.tradingeconomics.com/calendar?c={API_KEY}"
    data = safe_request(url)
    
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
    data = safe_request(url)

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
            url = f"https://api.tradingeconomics.com/calendar?c={API_KEY}"
            data = safe_request(url)

            now = datetime.now(tz)

            for n in data:
                if n.get("Importance") != 3:
                    continue

                # нормальная работа с датой
                event_time = datetime.fromisoformat(n['Date'].replace("Z", ""))
                event_time = event_time.replace(tzinfo=pytz.utc).astimezone(tz)

                # проверяем только сегодняшние
                if event_time.date() != now.date():
                    continue

                # проверяем что уже вышло
                if event_time <= now:
                    key = n['Event'] + str(event_time)

                    if key not in sent and n['Actual'] is not None:
                        msg = (
                            f"📢 *{n['Event']}*\n"
                            f"🌍 {n['Country']}\n"
                            f"🕒 {event_time.strftime('%H:%M')}\n\n"
                            f"Actual: {n['Actual']}\n"
                            f"Forecast: {n['Forecast']}\n"
                            f"Previous: {n['Previous']}"
                        )

                        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                        sent.add(key)

            time.sleep(60)

        except Exception as e:
            print("Error:", e)
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

            time.sleep(60)

        except Exception as e:
            print("Error in scheduler:", e)
            time.sleep(60)


# === ЗАПУСК ===
import threading

print("Bot started...")

threading.Thread(target=check_releases).start()
threading.Thread(target=scheduler).start()

bot.infinity_polling(skip_pending=True)
