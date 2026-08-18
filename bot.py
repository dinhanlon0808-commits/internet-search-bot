import requests
import logging
import html
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# 🔑 API CONFIG
# =========================================================

BOT_TOKEN = "8747823218:AAE5clUs5rSf-bF_MTQkxlnFiWk3LUUS8AY"

TAVILY_API_KEY = "b78786fefbf0a0276f335ff56a2788c97293d01fd8a9371c666bc3f13dc41de1"

# =========================================================
# ⚙️ SETTINGS
# =========================================================

TAVILY_URL = "https://api.tavily.com/search"

MAX_RESULTS = 10


# =========================================================
# LOG
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# =========================================================
# 🌐 TAVILY SEARCH
# =========================================================

def search_internet(query):

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "topic": "general",
        "max_results": MAX_RESULTS,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False
    }

    response = requests.post(
        TAVILY_URL,
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# 📄 FORMAT RESULTS
# =========================================================

def format_results(query, data):

    results = data.get("results", [])

    if not results:
        return (
            "🔎 <b>KẾT QUẢ TÌM KIẾM</b>\n\n"
            f"🔍 Từ khóa: <code>{html.escape(query)}</code>\n\n"
            "❌ Không tìm thấy kết quả."
        ), None

    text = (
        "🔎 <b>KẾT QUẢ TÌM KIẾM INTERNET</b>\n\n"
        f"🔍 <b>Từ khóa:</b> {html.escape(query)}\n"
        f"📊 <b>Số kết quả:</b> {len(results)}\n\n"
    )

    buttons = []

    for i, item in enumerate(results, 1):

        title = item.get(
            "title",
            "Không có tiêu đề"
        )

        url = item.get(
            "url",
            ""
        )

        content = item.get(
            "content",
            ""
        )

        # Làm sạch nội dung
        content = content.replace(
            "\n",
            " "
        ).strip()

        # Giới hạn mô tả
        if len(content) > 400:
            content = content[:400] + "..."

        text += (
            f"<b>{i}. {html.escape(title)}</b>\n"
            f"{html.escape(content)}\n\n"
        )

        if url:

            buttons.append([
                InlineKeyboardButton(
                    f"🌐 MỞ KẾT QUẢ {i}",
                    url=url
                )
            ])

    # Telegram giới hạn độ dài tin nhắn
    if len(text) > 4000:
        text = text[:3950] + "\n\n..."

    keyboard = None

    if buttons:
        keyboard = InlineKeyboardMarkup(
            buttons
        )

    return text, keyboard


# =========================================================
# 🚀 START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = """
🤖 <b>INTERNET SEARCH BOT</b>

━━━━━━━━━━━━━━━━━━

🔎 Tôi có thể tìm kiếm thông tin trên Internet và gửi các đường link liên quan cho bạn.

<b>Cách sử dụng:</b>

/search laptop gaming

/search việc làm online

/search giá vàng hôm nay

Hoặc chỉ cần gửi câu hỏi trực tiếp.

━━━━━━━━━━━━━━━━━━

🌐 <b>Search Engine:</b> Tavily
⚡ <b>Bot:</b> Telegram
"""

    await update.message.reply_text(
        message,
        parse_mode=ParseMode.HTML
    )


# =========================================================
# ❓ HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = """
📚 <b>HƯỚNG DẪN</b>

🔎 Tìm kiếm:

<code>/search từ khóa</code>

Ví dụ:

<code>/search điện thoại Samsung mới nhất</code>

<code>/search laptop gaming giá rẻ</code>

<code>/search việc làm online tại nhà</code>

Hoặc gửi câu hỏi trực tiếp cho bot.
"""

    await update.message.reply_text(
        message,
        parse_mode=ParseMode.HTML
    )


# =========================================================
# 🔎 /SEARCH
# =========================================================

async def search_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(
            "❌ Bạn chưa nhập từ khóa.\n\n"
            "Ví dụ:\n"
            "<code>/search laptop gaming</code>",
            parse_mode=ParseMode.HTML
        )

        return

    query = " ".join(
        context.args
    ).strip()

    await do_search(
        update,
        query
    )


# =========================================================
# 💬 DIRECT MESSAGE
# =========================================================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    query = update.message.text.strip()

    if not query:
        return

    await do_search(
        update,
        query
    )


# =========================================================
# 🔎 SEARCH PROCESS
# =========================================================

async def do_search(
    update: Update,
    query
):

    loading = await update.message.reply_text(
        "🔎 <b>Đang tìm kiếm Internet...</b>\n\n"
        "⏳ Đang thu thập kết quả...",
        parse_mode=ParseMode.HTML
    )

    try:

        logger.info(
            "Searching: %s",
            query
        )

        data = search_internet(
            query
        )

        text, keyboard = format_results(
            query,
            data
        )

        await loading.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

    except requests.exceptions.Timeout:

        await loading.edit_text(
            "⏰ API tìm kiếm phản hồi quá lâu.\n\n"
            "Hãy thử lại sau."
        )

    except requests.exceptions.HTTPError as e:

        logger.error(
            "Tavily HTTP error: %s",
            e
        )

        await loading.edit_text(
            "❌ <b>Tavily API bị lỗi.</b>\n\n"
            "Kiểm tra lại API Key của bạn.",
            parse_mode=ParseMode.HTML
        )

    except Exception as e:

        logger.exception(
            "Search error"
        )

        await loading.edit_text(
            "❌ <b>Bot gặp lỗi.</b>\n\n"
            f"<code>{html.escape(str(e))}</code>",
            parse_mode=ParseMode.HTML
        )


# =========================================================
# ❌ ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Telegram error: %s",
        context.error
    )


# =========================================================
# 🚀 MAIN
# =========================================================

def main():

    # Kiểm tra API
    if (
        BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN"
        or not BOT_TOKEN.strip()
    ):
        raise RuntimeError(
            "❌ Chưa nhập TELEGRAM BOT TOKEN"
        )

    if (
        TAVILY_API_KEY == "YOUR_TAVILY_API_KEY"
        or not TAVILY_API_KEY.strip()
    ):
        raise RuntimeError(
            "❌ Chưa nhập TAVILY API KEY"
        )

    print(
        "========================================"
    )

    print(
        "🤖 INTERNET SEARCH TELEGRAM BOT"
    )

    print(
        "🌐 Tavily Search"
    )

    print(
        "⚡ Bot đang khởi động..."
    )

    print(
        "========================================"
    )

    # Tạo application
    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    application.add_handler(
        CommandHandler(
            "search",
            search_command
        )
    )

    # Tin nhắn thường
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            message_handler
        )
    )

    # Error
    application.add_error_handler(
        error_handler
    )

    print(
        "✅ BOT ĐÃ SẴN SÀNG!"
    )

    # Telegram long polling
    application.run_polling(
        drop_pending_updates=True
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()
