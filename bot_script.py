import logging
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# --- تنظیمات اولیه ---
BOT_TOKEN = "YOUR_BOT_TOKEN"  # توکن ربات شما
ADMIN_IDS = set()  # Chat ID های مجاز (پس از /start اولیه، Chat ID شما به اینجا اضافه می شود)

# نام فایل اکسل جدید
DATA_FILE = "Information.xlsx" 

# مراحل مکالمه
SELECT_BUILDING, SELECT_BLOCK, SELECT_UNIT = range(3)

# پیکربندی لاگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- توابع کمکی ---

async def load_data():
    """داده‌ها را از فایل اکسل بارگذاری می‌کند."""
    try:
        df = pd.read_excel(DATA_FILE)
        # فرض می کنیم ستون های کلیدی شما اینها هستند:
        # ساختمان, بلوک, نام و نام خانوادگی, تلفن همراه, شماره تلفن.1, شماره واحد, مبلغ, طبقه
        # ستون هایی که در مدل قبلی استفاده شده بود را چک می کنیم و در صورت نیاز اصلاح می کنیم
        df.columns = [
            "ردیف", "ساختمان", "بلوک", "طریق پرداخت", "اکتیو شده ها", "وضعیت", 
            "درخواست", "ورودی", "طبقه", "شاخه", "تاریخ ثبت نام", "شماره مجازی", 
            "نام و نام خانوادگی", "نام پدر", "شماره ملی", "شماره شناسنامه", 
            "محل صدور", "تاریخ تولد", "شماره تلفن", "شماره تلفن.1", 
            "نام مالک خط", "تلفن همراه", "کد پستی", "شغل", "تحصیلات", 
            "شماره واحد", "مدت دوره", "نوع مودم", "شماره سرویس", "مبلغ"
        ]
        
        # پاکسازی و آماده سازی ستون ها برای جستجو
        # اطمینان از وجود ستون های مورد نیاز
        required_columns = ['ساختمان', 'بلوک', 'شماره واحد', 'نام و نام خانوادگی', 'تلفن همراه', 'شماره تلفن.1', 'مبلغ', 'طبقه']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"ستون مورد نیاز '{col}' در فایل اکسل یافت نشد. ممکن است جستجو با خطا مواجه شود.")
        
        # تبدیل تلفن همراه و شماره تلفن به فرمت قابل جستجو
        df['موبایل'] = df['تلفن همراه'].fillna(df['شماره تلفن.1']).astype(str).str.replace(r'9.12', '912', regex=True).str.replace(r'\.0$', '', regex=True).str.strip()
        # ایجاد ستون ترکیبی برای جستجوی دقیق تر (ساختمان_بلوک_واحد)
        # NaN ها را برای جلوگیری از خطا مدیریت می کنیم
        df['کد_جستجو'] = df['ساختمان'].fillna('') + "_" + df['بلوک'].fillna('').astype(str) + "_" + df['شماره واحد'].fillna('').astype(str)
        
        return df
    except FileNotFoundError:
        logger.error(f"فایل داده پیدا نشد: {DATA_FILE}")
        return None
    except Exception as e:
        logger.error(f"خطا در بارگذاری داده: {e}")
        return None

async def initialize_bot_data(application: Application):
    """داده ها را فقط یک بار بارگذاری و در دیتا بیس اپلیکیشن ذخیره می کند."""
    if not hasattr(application.bot_data, 'df_data') or application.bot_data['df_data'] is None:
        df = await load_data()
        if df is not None:
            application.bot_data['df_data'] = df
            logger.info("داده ها با موفقیت بارگذاری شدند.")
        else:
            logger.warning("داده ای برای بارگذاری وجود ندارد.")

# --- مدیریت دسترسی (Whitelist) ---
async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """بررسی می کند که آیا کاربر مجاز است یا خیر."""
    user_id = update.effective_user.id
    
    if not ADMIN_IDS:
        ADMIN_IDS.add(user_id)
        logger.warning(f"Chat ID {user_id} به عنوان اولین ادمین اضافه شد.")
        await update.message.reply_text(
            f"✅ خوش آمدید! شما به عنوان مدیر سیستم (Chat ID: {user_id}) اضافه شدید.\n"
            f"🤖 حالا می‌توانید با دستور /menu کار با ربات را شروع کنید."
        )
        return True

    if user_id in ADMIN_IDS:
        return True
    else:
        await update.message.reply_text(
            f"❌ دسترسی شما مجاز نیست.\n"
            f"Chat ID شما ({user_id}) در لیست سفید نیست. لطفاً با مدیر سیستم تماس بگیرید."
        )
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع مکالمه و بررسی دسترسی."""
    await initialize_bot_data(context.application)

    if await check_access(update, context):
        # نمایش لوگو و خوش آمدگویی
        logo_url = "https://via.placeholder.com/150/0000FF/FFFFFF?text=Company+Logo" # لوگوی شرکت شما
        
        await update.message.reply_photo(
            photo=logo_url,
            caption=(
                f"👋 سلام کارمند گرامی، **{update.effective_user.full_name}**.\n"
                f"شما با موفقیت احراز هویت شدید.\n\n"
                f"**لطفاً ساختمان مورد نظر برای جستجو را انتخاب کنید:**"
            ),
            parse_mode="Markdown"
        )
        
        # ساخت دکمه های ساختمان ها
        df = context.application.bot_data.get('df_data')
        if df is not None:
            # گرفتن ساختمان های منحصر به فرد و مرتب سازی آنها
            buildings = sorted(df['ساختمان'].dropna().unique())
            
            keyboard = []
            # گروه بندی دکمه ها در ردیف های 2 تایی
            for i in range(0, len(buildings), 2):
                row = [
                    InlineKeyboardButton(name, callback_data=name) 
                    for name in buildings[i:i+2]
                ]
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("انتخاب ساختمان:", reply_markup=reply_markup)
            return SELECT_BUILDING
        else:
            await update.message.reply_text("خطا: لیست ساختمان‌ها در دسترس نیست.")
            return ConversationHandler.END
    
    return ConversationHandler.END

# --- مدیریت انتخاب ساختمان (SELECT_BUILDING) ---
async def select_building(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """انتخاب ساختمان و نمایش بلوک های مربوطه."""
    query = update.callback_query
    await query.answer()
    
    selected_building = query.data
    context.user_data['building'] = selected_building
    
    # دریافت داده ها و فیلتر کردن بر اساس ساختمان انتخاب شده
    df = context.application.bot_data.get('df_data')
    if df is None:
        await query.edit_message_text("خطا: داده‌های مشترکین بارگذاری نشده است.")
        return ConversationHandler.END

    # گرفتن بلوک های منحصر به فرد برای ساختمان انتخاب شده
    blocks = sorted(df[df['ساختمان'] == selected_building]['بلوک'].dropna().unique())
    
    if not blocks:
        await query.edit_message_text(f"ساختمان **{selected_building}** انتخاب شد.\n"
                                      f"متاسفانه بلوکی برای این ساختمان در فایل داده یافت نشد. لطفاً ساختمان دیگری انتخاب کنید.",
                                      parse_mode="Markdown")
        # بازگشت به مرحله انتخاب ساختمان
        buildings = sorted(df['ساختمان'].dropna().unique())
        keyboard = []
        for i in range(0, len(buildings), 2):
            row = [InlineKeyboardButton(name, callback_data=name) for name in buildings[i:i+2]]
            keyboard.append(row)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("لطفاً ساختمان دیگری انتخاب کنید:", reply_markup=reply_markup)
        return SELECT_BUILDING
        
    keyboard = []
    # گروه بندی بلوک ها در ردیف های 2 تایی
    for i in range(0, len(blocks), 2):
        row = [InlineKeyboardButton(f"بلوک {block}", callback_data=str(block)) for block in blocks[i:i+2]]
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"ساختمان **{selected_building}** انتخاب شد.\nلطفاً بلوک مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECT_BLOCK

# --- مدیریت انتخاب بلوک (SELECT_BLOCK) ---
async def select_block(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """انتخاب بلوک و آماده سازی برای ورود واحد."""
    query = update.callback_query
    await query.answer()
    
    selected_block = query.data
    context.user_data['block'] = selected_block
    
    await query.edit_message_text(
        text=f"بلوک **{selected_block}** انتخاب شد.\n"
             f"**حالا شماره واحد مورد نظر را وارد کنید، یا بخشی از نام مشترک را بنویسید:**",
        parse_mode="Markdown"
    )
    return SELECT_UNIT

# --- جستجو و نمایش اطلاعات (SELECT_UNIT) ---
async def search_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """جستجو در اکسل بر اساس ساختمان، بلوک و واحد/نام مشترک."""
    
    df = context.application.bot_data.get('df_data')
    if df is None:
        await update.message.reply_text("خطا: داده‌های مشترکین بارگذاری نشده است.")
        return ConversationHandler.END

    building = context.user_data.get('building')
    block = context.user_data.get('block')
    
    # دریافت ورودی کاربر (شماره واحد یا نام)
    user_input = update.message.text.strip()
    search_term = user_input
    
    if not building or not block:
        await update.message.reply_text("خطا در روند مکالمه. لطفاً مجدداً با /menu شروع کنید.")
        return ConversationHandler.END

    filtered_df = df.copy()

    try:
        # فیلتر بر اساس ساختمان
        filtered_df = filtered_df[filtered_df['ساختمان'].astype(str).str.lower() == building.lower()]
        
        # فیلتر بر اساس بلوک (اگر بلوک عددی بود، تبدیل شود)
        try:
            block_numeric = float(block) if '.' in block else int(block)
            filtered_df = filtered_df[filtered_df['بلوک'].astype(str) == str(block_numeric)]
        except ValueError:
            # اگر بلوک عددی نبود، به صورت متنی فیلتر کن (مثلا برای بلوک های خاص)
            filtered_df = filtered_df[filtered_df['بلوک'].astype(str) == block]

        # فیلتر بر اساس واحد یا نام مشترک
        if search_term.isdigit(): # اگر ورودی عدد بود، آن را واحد در نظر می گیریم
            final_df = filtered_df[filtered_df['شماره واحد'].astype(str).str.strip() == search_term]
        else: # اگر متن بود، نام مشترک را جستجو می کنیم
            final_df = filtered_df[
                filtered_df['نام و نام خانوادگی'].str.contains(search_term, na=False, case=False)
            ]

    except Exception as e:
        logger.error(f"خطا در فیلتر کردن داده‌ها: {e}")
        await update.message.reply_text("خطایی در پردازش داده‌ها رخ داد. مجدداً امتحان کنید.")
        return ConversationHandler.END
    
    if final_df.empty:
        await update.message.reply_text(f"هیچ مشترکی با مشخصات (ساختمان: {building}, بلوک: {block}, جستجو: **{search_term}**) یافت نشد. لطفاً مجدداً تلاش کنید.")
        return SELECT_UNIT
        
    # --- ساخت خروجی ---
    results = final_df.head(5) # محدود کردن خروجی به 5 نتیجه برتر
    
    output_text = f"**نتایج جستجو برای:**\n" \
                  f"**ساختمان:** {building}\n" \
                  f"**بلوک:** {block}\n" \
                  f"**جستجو:** **{search_term}** \n\n"
    
    for index, row in results.iterrows():
        output_text += (
            f"👤 **نام:** {row.get('نام و نام خانوادگی', 'نامشخص')}\n"
            f"📱 **همراه:** `{row.get('تلفن همراه', 'تلفن نامشخص')}`\n"
            f"🚪 **واحد/طبقه:** {row.get('شماره واحد', 'واحد نامشخص')}/{row.get('طبقه', 'طبقه نامشخص')}\n"
            f"💸 **مبلغ:** {row.get('مبلغ', 'مبلغ نامشخص'):,.0f} تومان\n"
            f"---------------------------------\n"
        )
        
    await update.message.reply_text(
        output_text,
        parse_mode="Markdown"
    )
    
    context.user_data.clear() # پاک کردن اطلاعات کاربر پس از نمایش نتیجه
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """مکالمه را لغو می‌کند."""
    await update.message.reply_text(
        "عملیات لغو شد. برای شروع مجدد دستور /menu را ارسال کنید."
    )
    context.user_data.clear()
    return ConversationHandler.END

async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """در صورتی که کاربر در مرحله ورود واحد، عدد یا متن غیرمنتظره‌ای وارد کند."""
    await update.message.reply_text(
        "ورودی نامعتبر است. لطفاً فقط شماره واحد یا بخشی از نام مشترک را وارد کنید."
    )
    return SELECT_UNIT # بازگشت به مرحله انتظار برای ورود واحد/نام

def main() -> None:
    """اجرای ربات."""
    application = Application.builder().token(BOT_TOKEN).bot_data({}).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("menu", start) # دستور /menu برای شروع مجدد مکالمه
        ],
        states={
            SELECT_BUILDING: [
                InlineKeyboardButton.callback_data(lambda query: True, select_building)
            ],
            SELECT_BLOCK: [
                InlineKeyboardButton.callback_data(lambda query: True, select_block) # همه کلیک ها در این مرحله به select_block می روند
            ],
            SELECT_UNIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_data),
                # می توانید دکمه های بیشتری برای لغو یا بازگشت در اینجا اضافه کنید
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.COMMAND, cancel), # اگر کاربر دستور دیگری را وارد کرد
            MessageHandler(filters.ALL, fallback_handler) # برای ورودی های غیرمنتظره
        ],
        name="user_conversation", # نام منحصر به فرد برای ConversationHandler
        persistent=False # فعلا persistence را غیرفعال می کنیم
    )

    application.add_handler(conv_handler)

    logger.info("ربات در حال اجرا است...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
