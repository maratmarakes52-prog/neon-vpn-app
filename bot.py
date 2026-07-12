import telebot
from telebot import types
import json
import time
import sqlite3
from datetime import datetime, timedelta

BOT_TOKEN = "8955469325:AAGVwLndu7SBz5WKyS1yXzFzaAQ0Dg3IRTw"
ADMIN_ID = 7481288398
WEBAPP_URL = "https://neon-vpn-app.vercel.app"

bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect('neon_users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        subscription_end TEXT,
        key TEXT,
        created_at TEXT
    )
''')
conn.commit()

PLANS = {
    "1m": {"name": "1 месяц", "price_stars": 150, "days": 30, "tribute": "https://web.tribute.tg/p/zSp"},
    "3m": {"name": "3 месяца", "price_stars": 400, "days": 90, "tribute": "https://web.tribute.tg/p/zSq"},
    "6m": {"name": "6 месяцев", "price_stars": 650, "days": 180, "tribute": "https://web.tribute.tg/p/zSr"},
    "12m": {"name": "12 месяцев", "price_stars": 950, "days": 365, "tribute": "https://web.tribute.tg/p/zSt"},
}

def add_user(telegram_id, username, key):
    now = datetime.now().isoformat()
    cursor.execute('INSERT OR REPLACE INTO users (telegram_id, username, key, created_at) VALUES (?, ?, ?, ?)',
                   (telegram_id, username, key, now))
    conn.commit()

def set_subscription(telegram_id, days):
    end_date = (datetime.now() + timedelta(days=days)).isoformat()
    cursor.execute('UPDATE users SET subscription_end = ? WHERE telegram_id = ?', (end_date, telegram_id))
    conn.commit()

def get_user(telegram_id):
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    return cursor.fetchone()

def generate_key():
    import random, string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

@bot.message_handler(commands=['start'])
def start(message):
    telegram_id = message.chat.id
    username = message.from_user.username or "unknown"
    user = get_user(telegram_id)
    if not user:
        key = generate_key()
        add_user(telegram_id, username, key)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🌐 ОТКРЫТЬ МАГАЗИН", web_app=types.WebAppInfo(url=WEBAPP_URL)))
    bot.send_message(message.chat.id,
                     "🔐 **NEON VPN**\n\nАнтиглушилка 2.0 — работаем стабильно.\nДоступ к 7 конфигурациям.\n\n📌 Для покупки нажми «ОТКРЫТЬ МАГАЗИН»",
                     reply_markup=keyboard, parse_mode="Markdown")

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return
    users = cursor.execute('SELECT telegram_id FROM users').fetchall()
    active = 0
    for uid in users:
        u = get_user(uid[0])
        if u and u[2]:
            end = datetime.fromisoformat(u[2])
            if end > datetime.now():
                active += 1
    bot.send_message(ADMIN_ID, f"📊 **Статистика**\n👤 Всего: {len(users)}\n🟢 Активных: {active}", parse_mode="Markdown")

@bot.message_handler(commands=['give'])
def give(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return
    args = message.text.split()
    if len(args) < 3:
        bot.send_message(message.chat.id, "❌ /give <tg_id> <plan или unlimited>")
        return
    tg_id = int(args[1])
    plan = args[2]
    if plan == "unlimited":
        set_subscription(tg_id, 36500)
        bot.send_message(message.chat.id, f"✅ Пользователю {tg_id} выдана бесконечная подписка")
    elif plan in PLANS:
        set_subscription(tg_id, PLANS[plan]["days"])
        bot.send_message(message.chat.id, f"✅ Пользователю {tg_id} выдана подписка {PLANS[plan]['name']}")
    else:
        bot.send_message(message.chat.id, "❌ Неверный план")

@bot.message_handler(commands=['status'])
def status(message):
    telegram_id = message.chat.id
    user = get_user(telegram_id)
    if not user or not user[2]:
        bot.send_message(telegram_id, "❌ Подписка не найдена. Купите в магазине → /start")
        return
    end = datetime.fromisoformat(user[2])
    if end > datetime.now():
        days_left = (end - datetime.now()).days
        bot.send_message(telegram_id, f"✅ **Подписка активна**\n⏳ Осталось: {days_left} дней\n🔑 Ключ: `{user[3]}`", parse_mode="Markdown")
    else:
        bot.send_message(telegram_id, "❌ Подписка истекла. Купите новую → /start")

if __name__ == "__main__":
    print("🔐 NEON VPN БОТ ЗАПУЩЕН!")
    bot.polling(non_stop=True)
