import os
import logging
from dotenv import load_dotenv
from math import ceil

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from phase2_search_engine import (
    load_books_dataset,
    search_by_title,
    search_by_author,
    search_by_translator,
    get_random_book,
    format_book,
    format_books_list,
    safe_value,
)


load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)



BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set. Please add it to the .env file.")

ITEMS_PER_PAGE = 5
CATEGORIES_PER_PAGE = 8


BTN_SEARCH_TITLE = "🔍 جستجوی کتاب"
BTN_SEARCH_AUTHOR = "✍️ جستجو بر اساس نویسنده"
BTN_SEARCH_CATEGORY = "🏷 جستجو بر اساس دسته‌بندی"
BTN_SEARCH_TRANSLATOR = "🌐 جستجو بر اساس مترجم"
BTN_TOP_BOOKS = "⭐ کتاب‌های برتر"
BTN_RANDOM_BOOK = "🎲 پیشنهاد تصادفی"
BTN_HELP = "ℹ️ راهنما"
BTN_CANCEL = "❌ لغو"


MODE_TITLE = "search_title"
MODE_AUTHOR = "search_author"
MODE_TRANSLATOR = "search_translator"


books_df = load_books_dataset()

all_categories = sorted(
    [
        str(category).strip()
        for category in books_df["دسته‌بندی"].dropna().unique()
        if str(category).strip()
    ]
)


def main_keyboard():
    
    keyboard = [
        [BTN_SEARCH_TITLE, BTN_SEARCH_AUTHOR],
        [BTN_SEARCH_CATEGORY, BTN_SEARCH_TRANSLATOR],
        [BTN_TOP_BOOKS, BTN_RANDOM_BOOK],
        [BTN_HELP, BTN_CANCEL],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


def get_book_code(book):
    code = book.get("ردیف", "")

    try:
        if str(code).strip() != "":
            return str(int(float(code)))
    except Exception:
        pass

    return str(book.name)


def get_book_title(book):
    return safe_value(book["عنوان کتاب"])


def get_book_rating(book):
    return safe_value(book["امتیاز"])


def get_category_books(category):
    results = books_df[
        books_df["دسته‌بندی"].astype(str).str.strip() == str(category).strip()
    ].copy()

    results = results.sort_values(
        by=["امتیاز", "عنوان کتاب"],
        ascending=[False, True]
    )

    return results


def get_five_star_books():
    results = books_df[
        books_df["امتیاز"].fillna(0) == 5
    ].copy()

    results = results.sort_values(
        by=["دسته‌بندی", "عنوان کتاب"],
        ascending=[True, True]
    )

    return results


def build_categories_keyboard(page=0):
    total_categories = len(all_categories)
    total_pages = max(1, ceil(total_categories / CATEGORIES_PER_PAGE))

    page = max(0, min(page, total_pages - 1))

    start = page * CATEGORIES_PER_PAGE
    end = start + CATEGORIES_PER_PAGE

    keyboard = []

    for index, category in enumerate(all_categories[start:end], start=start):
        keyboard.append([
            InlineKeyboardButton(
                category,
                callback_data=f"cat:{index}"
            )
        ])

    navigation_row = []

    if page > 0:
        navigation_row.append(
            InlineKeyboardButton("⬅️ صفحه قبل", callback_data=f"catlist:{page - 1}")
        )

    navigation_row.append(
        InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="nothing")
    )

    if page < total_pages - 1:
        navigation_row.append(
            InlineKeyboardButton("صفحه بعد ➡️", callback_data=f"catlist:{page + 1}")
        )

    keyboard.append(navigation_row)

    return InlineKeyboardMarkup(keyboard)


def build_category_books_page(results, page, category_name):
    total_books = len(results)

    if total_books == 0:
        return "❌ در این دسته‌بندی کتابی پیدا نشد.", None

    total_pages = max(1, ceil(total_books / ITEMS_PER_PAGE))
    page = max(0, min(page, total_pages - 1))

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE

    page_results = results.iloc[start:end]

    message_parts = [
        f"🏷 دسته‌بندی: {category_name}",
        f"📚 تعداد کتاب‌ها: {total_books}",
        f"📄 صفحه {page + 1} از {total_pages}",
        "",
        "در این بخش فقط عنوان، امتیاز و کد کتاب نمایش داده می‌شود.",
        "برای دیدن مشخصات کامل، دکمه کد کتاب را بزن.",
        "-" * 30,
    ]

    keyboard = []

    for number, (df_index, book) in enumerate(page_results.iterrows(), start=start + 1):
        book_code = get_book_code(book)
        book_title = get_book_title(book)
        book_rating = get_book_rating(book)

        message_parts.append(
            f"{number}. 📚 {book_title}\n"
            f"⭐ امتیاز: {book_rating}\n"
            f"🔢 کد کتاب: {book_code}\n"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"📖 مشاهده اطلاعات کد {book_code}",
                callback_data=f"detail:{df_index}"
            )
        ])

    navigation_row = []

    if page > 0:
        navigation_row.append(
            InlineKeyboardButton("⬅️ صفحه قبل", callback_data=f"catpage:{page - 1}")
        )

    navigation_row.append(
        InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="nothing")
    )

    if page < total_pages - 1:
        navigation_row.append(
            InlineKeyboardButton("صفحه بعد ➡️", callback_data=f"catpage:{page + 1}")
        )

    keyboard.append(navigation_row)

    keyboard.append([
        InlineKeyboardButton("🏷 بازگشت به دسته‌بندی‌ها", callback_data="catlist:0")
    ])

    return "\n".join(message_parts), InlineKeyboardMarkup(keyboard)


def build_top_books_page(results, page):
    total_books = len(results)

    if total_books == 0:
        return "❌ هیچ کتابی با امتیاز 5 پیدا نشد.", None

    total_pages = max(1, ceil(total_books / ITEMS_PER_PAGE))
    page = max(0, min(page, total_pages - 1))

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE

    page_results = results.iloc[start:end]

    message_parts = [
        "⭐ کتاب‌های برتر با امتیاز 5",
        f"📚 تعداد کل: {total_books}",
        f"📄 صفحه {page + 1} از {total_pages}",
        "-" * 30,
    ]

    for number, (_, book) in enumerate(page_results.iterrows(), start=start + 1):
        message_parts.append(f"نتیجه {number}:")
        message_parts.append(format_book(book))
        message_parts.append("-" * 30)

    keyboard = []
    navigation_row = []

    if page > 0:
        navigation_row.append(
            InlineKeyboardButton("⬅️ صفحه قبل", callback_data=f"toppage:{page - 1}")
        )

    navigation_row.append(
        InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="nothing")
    )

    if page < total_pages - 1:
        navigation_row.append(
            InlineKeyboardButton("صفحه بعد ➡️", callback_data=f"toppage:{page + 1}")
        )

    keyboard.append(navigation_row)

    return "\n".join(message_parts), InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    message = (
        "سلام 👋\n"
        "به ربات کتابخانه خوش اومدی.\n\n"
        "از دکمه‌های پایین استفاده کن:\n\n"
        "🔍 جستجوی کتاب: جستجو بر اساس عنوان\n"
        "✍️ جستجو بر اساس نویسنده: جستجو بر اساس نویسنده / مؤلف\n"
        "🏷 جستجو بر اساس دسته‌بندی: انتخاب دسته‌بندی با دکمه\n"
        "🌐 جستجو بر اساس مترجم: جستجو در بهترین ترجمه در ایران\n"
        "⭐ کتاب‌های برتر: نمایش کتاب‌های امتیاز 5\n"
        "🎲 پیشنهاد تصادفی: معرفی یک کتاب تصادفی"
    )

    await update.message.reply_text(
        message,
        reply_markup=main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "راهنمای ربات 📌\n\n"
        "برای جستجو بر اساس عنوان، نویسنده یا مترجم، اول دکمه مربوطه را بزن و بعد متن موردنظرت را ارسال کن.\n\n"
        "برای دسته‌بندی، دکمه 🏷 جستجو بر اساس دسته‌بندی را بزن و بعد از بین دسته‌بندی‌ها انتخاب کن.\n\n"
        "در نتایج دسته‌بندی، فقط عنوان و امتیاز نمایش داده می‌شود. "
        "برای دیدن اطلاعات کامل کتاب، روی دکمه کد همان کتاب بزن.\n\n"
        "در بخش ⭐ کتاب‌های برتر، همه کتاب‌های دارای امتیاز 5، صفحه‌به‌صفحه نمایش داده می‌شوند."
    )

    await update.message.reply_text(
        message,
        reply_markup=main_keyboard()
    )


async def send_random_book(update: Update):
    book = get_random_book(books_df)
    message = "🎲 پیشنهاد تصادفی کتاب:\n\n" + format_book(book)

    await update.message.reply_text(
        message,
        reply_markup=main_keyboard()
    )


async def send_categories(update: Update):
    message = (
        "🏷 لطفاً یکی از دسته‌بندی‌های زیر را انتخاب کن:\n\n"
        "بعد از انتخاب دسته‌بندی، کتاب‌های همان بخش به‌صورت صفحه‌بندی‌شده نمایش داده می‌شوند."
    )

    await update.message.reply_text(
        message,
        reply_markup=build_categories_keyboard(page=0)
    )


async def send_top_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = get_five_star_books()

    context.user_data["top_result_indices"] = results.index.tolist()

    message, keyboard = build_top_books_page(results, page=0)

    await update.message.reply_text(
        message,
        reply_markup=keyboard
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == BTN_SEARCH_TITLE:
        context.user_data.clear()
        context.user_data["mode"] = MODE_TITLE

        await update.message.reply_text(
            "نام کتاب را وارد کن:",
            reply_markup=main_keyboard()
        )
        return

    if text == BTN_SEARCH_AUTHOR:
        context.user_data.clear()
        context.user_data["mode"] = MODE_AUTHOR

        await update.message.reply_text(
            "نام نویسنده / مؤلف را وارد کن:",
            reply_markup=main_keyboard()
        )
        return

    if text == BTN_SEARCH_CATEGORY:
        context.user_data.clear()
        await send_categories(update)
        return

    if text == BTN_SEARCH_TRANSLATOR:
        context.user_data.clear()
        context.user_data["mode"] = MODE_TRANSLATOR

        await update.message.reply_text(
            "نام مترجم را وارد کن:",
            reply_markup=main_keyboard()
        )
        return

    if text == BTN_TOP_BOOKS:
        context.user_data.clear()
        await send_top_books(update, context)
        return

    if text == BTN_RANDOM_BOOK:
        context.user_data.clear()
        await send_random_book(update)
        return

    if text == BTN_HELP:
        await help_command(update, context)
        return

    if text == BTN_CANCEL:
        context.user_data.clear()

        await update.message.reply_text(
            "عملیات لغو شد.",
            reply_markup=main_keyboard()
        )
        return

    mode = context.user_data.get("mode")

    if mode == MODE_TITLE:
        results = search_by_title(books_df, text, limit=5)
        message = format_books_list(results, "🔍 نتایج جستجو بر اساس عنوان")

        context.user_data.clear()

        await update.message.reply_text(
            message,
            reply_markup=main_keyboard()
        )
        return

    if mode == MODE_AUTHOR:
        results = search_by_author(books_df, text, limit=5)
        message = format_books_list(results, "✍️ نتایج جستجو بر اساس نویسنده / مؤلف")

        context.user_data.clear()

        await update.message.reply_text(
            message,
            reply_markup=main_keyboard()
        )
        return

    if mode == MODE_TRANSLATOR:
        results = search_by_translator(books_df, text, limit=5)
        message = format_books_list(results, "🌐 نتایج جستجو بر اساس مترجم")

        context.user_data.clear()

        await update.message.reply_text(
            message,
            reply_markup=main_keyboard()
        )
        return

    await update.message.reply_text(
        "لطفاً اول یکی از دکمه‌های پایین را انتخاب کن.",
        reply_markup=main_keyboard()
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "nothing":
        return

    if data.startswith("catlist:"):
        page = int(data.split(":")[1])

        message = (
            "🏷 لطفاً یکی از دسته‌بندی‌های زیر را انتخاب کن:\n\n"
            "بعد از انتخاب دسته‌بندی، کتاب‌های همان بخش به‌صورت صفحه‌بندی‌شده نمایش داده می‌شوند."
        )

        await query.edit_message_text(
            message,
            reply_markup=build_categories_keyboard(page=page)
        )
        return

    if data.startswith("cat:"):
        category_index = int(data.split(":")[1])
        category_name = all_categories[category_index]

        results = get_category_books(category_name)

        context.user_data["selected_category"] = category_name
        context.user_data["category_result_indices"] = results.index.tolist()

        message, keyboard = build_category_books_page(
            results,
            page=0,
            category_name=category_name
        )

        await query.edit_message_text(
            message,
            reply_markup=keyboard
        )
        return

    if data.startswith("catpage:"):
        page = int(data.split(":")[1])

        category_name = context.user_data.get("selected_category")
        result_indices = context.user_data.get("category_result_indices", [])

        if not category_name or not result_indices:
            await query.edit_message_text(
                "❌ اطلاعات این جستجو منقضی شده. لطفاً دوباره دسته‌بندی را انتخاب کن."
            )
            return

        results = books_df.loc[result_indices]

        message, keyboard = build_category_books_page(
            results,
            page=page,
            category_name=category_name
        )

        await query.edit_message_text(
            message,
            reply_markup=keyboard
        )
        return

    if data.startswith("detail:"):
        df_index = int(data.split(":")[1])

        if df_index not in books_df.index:
            await query.message.reply_text("❌ کتاب موردنظر پیدا نشد.")
            return

        book = books_df.loc[df_index]
        message = "📖 اطلاعات کامل کتاب:\n\n" + format_book(book)

        await query.message.reply_text(
            message,
            reply_markup=main_keyboard()
        )
        return

    if data.startswith("toppage:"):
        page = int(data.split(":")[1])

        result_indices = context.user_data.get("top_result_indices", [])

        if not result_indices:
            results = get_five_star_books()
            context.user_data["top_result_indices"] = results.index.tolist()
        else:
            results = books_df.loc[result_indices]

        message, keyboard = build_top_books_page(results, page=page)

        await query.edit_message_text(
            message,
            reply_markup=keyboard
        )
        return


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)

    try:
        if update and hasattr(update, "message") and update.message:
            await update.message.reply_text(
                "⚠️ یک خطای غیرمنتظره رخ داد. لطفاً دوباره تلاش کن.",
                reply_markup=main_keyboard()
            )

        elif update and hasattr(update, "callback_query") and update.callback_query:
            await update.callback_query.message.reply_text(
                "⚠️ یک خطای غیرمنتظره رخ داد. لطفاً دوباره تلاش کن.",
                reply_markup=main_keyboard()
            )

    except Exception:
        logger.error("Failed to send error message to user.", exc_info=True)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(CallbackQueryHandler(handle_callback))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    app.add_error_handler(error_handler)

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()