import asyncio
import json
import sqlite3
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import config

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# تم تحديث الرابط بـ v=10 لضمان مسح الكاش بالكامل
WEB_APP_URL = "https://ji7x1.github.io/membot/?v=10"

def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (order_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id INTEGER, name TEXT, phone TEXT, address TEXT, 
                  receipt TEXT, total INTEGER, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

@dp.message(CommandStart())
async def start_command(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 الدخول إلى متجر ميم", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await message.answer("أهلاً بك في النظام الذكي لـ 📚 **مكتبة ميم**!\nتصفح أقسامنا واطلب الآن:", reply_markup=markup)

@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        name = data.get('customer_name')
        phone = data.get('customer_phone')
        address = data.get('customer_address')
        items = data.get('items')
        total = data.get('total_price')
        user_id = message.from_user.id
        
        items_text = "\n".join([f"▪️ {item['name']} | السعر: {item['price']} د.ع" for item in items])
        
        conn = sqlite3.connect('orders.db')
        c = conn.cursor()
        c.execute("INSERT INTO orders (user_id, name, phone, address, receipt, total, status) VALUES (?,?,?,?,?,?,?)",
                  (user_id, name, phone, address, items_text, total, "قيد المراجعة"))
        order_id = c.lastrowid
        conn.commit()
        conn.close()

        await message.answer(f"✅ **تم استلام طلبك بنجاح!**\nرقم الفاتورة: #{order_id}\nسيتم إشعارك عند التجهيز.")

        admin_receipt = (
            f"🔥 **طلب جديد #{order_id}** 🔥\n"
            f"👤 الاسم: {name}\n"
            f"📱 الهاتف: {phone}\n"
            f"📍 العنوان: {address}\n"
            f"🆔 الزبون: `{user_id}`\n"
            f"━━━━━━━━━━━━\n{items_text}\n━━━━━━━━━━━━\n"
            f"💵 الإجمالي: {total} د.ع"
        )
        
        admin_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ تمت الموافقة", callback_data=f"approve_{order_id}_{user_id}")],
            [InlineKeyboardButton(text="⏳ قيد التجهيز", callback_data=f"process_{order_id}_{user_id}")],
            [InlineKeyboardButton(text="📦 جاهز للتسليم", callback_data=f"ready_{order_id}_{user_id}")]
        ])

        if hasattr(config, 'ADMIN_CHAT_ID') and config.ADMIN_CHAT_ID:
            await bot.send_message(chat_id=config.ADMIN_CHAT_ID, text=admin_receipt, reply_markup=admin_markup)
            
    except Exception as e:
        print(f"Error: {e}")
        await message.answer("⚠️ حدث خطأ، يرجى تحديث التطبيق والمحاولة.")

@dp.callback_query(F.data.startswith('approve_') | F.data.startswith('process_') | F.data.startswith('ready_'))
async def admin_order_action(call: CallbackQuery):
    action, order_id, user_id = call.data.split('_')
    
    if action == 'approve':
        status = "✅ تمت الموافقة"
        user_msg = f"مرحباً! طلبك رقم #{order_id} **تمت الموافقة عليه**."
    elif action == 'process':
        status = "⏳ قيد التجهيز"
        user_msg = f"مرحباً! طلبك رقم #{order_id} الآن **قيد التجهيز**."
    else:
        status = "📦 جاهز للتسليم"
        user_msg = f"🎉 طلبك رقم #{order_id} **جاهز** وفي طريقه إليك."

    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
    conn.commit()
    conn.close()

    try:
        await bot.send_message(chat_id=user_id, text=user_msg)
        await call.message.edit_text(call.message.text + f"\n\nالوضع الحالي: {status}")
    except:
        await call.answer("خطأ: الزبون حظر البوت.", show_alert=True)

async def main():
    print("🚀 System Online: Database & Mini App Ready!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())