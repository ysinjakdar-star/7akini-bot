import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# قاعدة البيانات
conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

waiting_users = []

# ----------------------
# 1️⃣ /start مع القوائم
# ----------------------
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)",
                   (user_id, username))
    conn.commit()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Match", callback_data="match")],
        [InlineKeyboardButton(text="📝 Profile", callback_data="profile")],
        [InlineKeyboardButton(text="💎 VIP", callback_data="vip")],
        [InlineKeyboardButton(text="🛒 Store", callback_data="store")],
        [InlineKeyboardButton(text="🔗 Referral", callback_data="referral")],
        [InlineKeyboardButton(text="🏆 Top", callback_data="top")],
        [InlineKeyboardButton(text="❓ Help", callback_data="help")]
    ])

    await message.answer("🔥 أهلاً بك! اختر من القائمة أدناه:", reply_markup=keyboard)

# ----------------------
# 2️⃣ الأزرار (Callback)
# ----------------------
@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if data == "match":
        if waiting_users:
            partner = waiting_users.pop(0)
            cursor.execute("UPDATE users SET partner=? WHERE user_id=?", (partner, user_id))
            cursor.execute("UPDATE users SET partner=? WHERE user_id=?", (user_id, partner))
            conn.commit()
            await bot.send_message(partner, "🎉 تم العثور على شريك!")
            await callback.message.answer("🎉 تم العثور على شريك!")
        else:
            waiting_users.append(user_id)
            await callback.message.answer("⏳ جاري البحث عن شريك...")
    elif data == "profile":
        cursor.execute("SELECT display_name, vip, points FROM users WHERE user_id=?", (user_id,))
        user = cursor.fetchone()
        display_name = user[0] if user[0] else "لم تحدد"
        vip_status = "نعم" if user[1] else "لا"
        points = user[2]
        await callback.message.answer(
            f"📝 بروفايلك:\nالاسم: {display_name}\nVIP: {vip_status}\nالنقاط: {points}"
        )
    elif data == "vip":
        await callback.message.answer("💎 VIP: هذه ميزة تجريبية حالياً.")
    elif data == "store":
        await callback.message.answer("🛒 Store: يمكنك شراء نقاط أو ترقيات هنا (تجريبية).")
    elif data == "referral":
        await callback.message.answer("🔗 Referral: شارك البوت مع أصدقائك لكسب نقاط.")
    elif data == "top":
        cursor.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 5")
        leaderboard = cursor.fetchall()
        text = "🏆 أفضل 5 مستخدمين:\n"
        for i, (uname, pts) in enumerate(leaderboard, start=1):
            text += f"{i}. @{uname} → {pts} نقاط\n"
        await callback.message.answer(text)
    elif data == "help":
        await callback.message.answer(
            "❓ أوامر البوت:\n"
            "/start - العودة للقائمة الرئيسية\n"
            "🎯 Match - البحث عن شريك\n"
            "📝 Profile - عرض البروفايل\n"
            "💎 VIP - الاشتراك المميز\n"
            "🛒 Store - المتجر\n"
            "🔗 Referral - دعوة أصدقاء\n"
            "🏆 Top - أفضل المستخدمين\n"
            "/leave - الخروج من المحادثة"
        )

# ----------------------
# 3️⃣ /leave للخروج من المحادثة
# ----------------------
@dp.message(Command("leave"))
async def leave_chat(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT partner FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    if result and result[0]:
        partner = result[0]
        cursor.execute("UPDATE users SET partner=NULL WHERE user_id=?", (user_id,))
        cursor.execute("UPDATE users SET partner=NULL WHERE user_id=?", (partner,))
        conn.commit()
        await bot.send_message(partner, "❌ الطرف الآخر خرج.")
        await message.answer("تم الخروج من المحادثة.")
    else:
        await message.answer("أنت لست في محادثة الآن.")

# ----------------------
# 4️⃣ تحويل الرسائل بين المستخدمين
# ----------------------
@dp.message()
async def forward_messages(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT partner FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    if result and result[0]:
        await bot.send_message(result[0], message.text)

# ----------------------
# 5️⃣ تشغيل البوت
# ----------------------
async def main():
    await dp.start_polling(bot)

asyncio.run(main())
