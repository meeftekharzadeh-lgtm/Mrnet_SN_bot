# bot_block9_advanced.py

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import pandas as pd
import asyncio

# 📘 بارگذاری داده از اکسل
data = pd.read_excel("Information.xlsx")

# 📱 تعریف شماره‌های مجاز
AUTHORIZED_USERS = ["09125990826", "09021579104"]  # شماره‌ها بدون صفر اول هم قابل چک شدن هستند

# 🧭 تابع بررسی مجوز
def is_authorized(update: Update):
    user_phone = getattr(update.effective_user, 'phone_number', None)
    return user_phone and any(user_phone.endswith(num[-10:]) for num in AUTHORIZED_USERS)

# 🏠 دستور شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📋 جستجوی اطلاعات"), KeyboardButton("ℹ️ راهنما")]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("سلام 👋\nبرای استفاده از امکانات، از منوی زیر انتخاب کن:", reply_markup=markup)

# 🔍 جستجو
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # اگر دسترسی ندارد
    if update.effective_user.id not in [u.id for u in await context.bot.get_chat_administrators(update.effective_chat.id)]:
        await update.message.reply_text("❌ شما مجاز به استفاده از این ربات نیستید.")
        return

    if text == "ℹ️ راهنما":
        await update.message.reply_text("برای دریافت اطلاعات، نام مشترک مورد نظر را بنویس.")
        return

    result = data[data["نام و نام خانوادگی"].str.contains(text, case=False, na=False)]
    if result.empty:
        await update.message.reply_text("❌ اطلاعاتی با این نام پیدا نشد.")
        return

    for _, row in result.iterrows():
        info = (
            f"📋 نام و نام خانوادگی: {row['نام و نام خانوادگی']}\n"
            f"👨‍👩‍👧 نام پدر: {row['نام پدر']}\n"
            f"📞 تلفن: {row['شماره تلفن']}\n"
            f"📱 تلفن همراه: {row['تلفن همراه']}\n"
            f"🏢 واحد: {row['شماره واحد']}\n"
            f"💰 مبلغ: {int(row['مبلغ']) if not pd.isna(row['مبلغ']) else '---'} تومان\n"
            f"📦 نوع مودم: {row.get('نوع مودم', '---')}"
        )
        await update.message.reply_text(info)

if __name__ == "__main__":
    app = ApplicationBuilder().token("8255680535:AAEAwCmAneKCI1FCKWAeQeMI5KcaT14U8jw").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
