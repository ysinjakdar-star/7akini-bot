import asyncio
import sqlite3
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    partner INTEGER DEFAULT NULL
)
""")
conn.commit()

waiting_users = []

@dp.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)",
                   (user_id, username))
    conn.commit()

    await message.answer("🔥 أهلاً بك!\nاستخدم /match للبحث عن شخص.")

@dp.message(Command("match"))
async def match_user(message: Message):
    user_id = message.from_user.id

    if waiting_users:
        partner = waiting_users.pop(0)

        cursor.execute("UPDATE users SET partner=? WHERE user_id=?", (partner, user_id))
        cursor.execute("UPDATE users SET partner=? WHERE user_id=?", (user_id, partner))
        conn.commit()

        await bot.send_message(partner, "🎉 تم العثور على شريك!")
        await message.answer("🎉 تم العثور على شريك!")
    else:
        waiting_users.append(user_id)
        await message.answer("⏳ جاري البحث...")

@dp.message(Command("leave"))
async def leave_chat(message: Message):
    user_id = message.from_user.id

    cursor.execute("SELECT partner FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    if result and result[0]:
        partner = result[0]

        cursor.execute("UPDATE users SET partner=NULL WHERE user_id=?", (user_id,))
        cursor.execute("UPDATE users SET partner=NULL WHERE user_id=?", (partner,))
        conn.commit()

        await bot.send_message(partner, "❌ الطرف الآخر خرج.")
        await message.answer("تم الخروج.")
    else:
        await message.answer("أنت لست في محادثة.")

@dp.message()
async def forward_messages(message: Message):
    user_id = message.from_user.id
    cursor.execute("SELECT partner FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    if result and result[0]:
        await bot.send_message(result[0], message.text)

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
