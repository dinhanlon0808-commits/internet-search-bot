```python
import html
import logging
import os
import requests

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# 🔑 API
# =========================================================

BOT_TOKEN = os.getenv("8747823218:AAE5clUs5rSf-bF_MTQkxlnFiWk3LUUS8AY")
TAVILY_API_KEY = os.getenv("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")

TAVILY_URL = "https://api.tavily.com/search"

MAX_RESULTS = 10
TIMEOUT = 60


# =========================================================
# 📝 LOG
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# 🔎 TAVILY SEARCH
# =========================================================

def search_internet(query):

    if not TAVILY_API_KEY:
        raise RuntimeError(
            "Chưa cấu hình TAVILY_API_KEY trên Railway"
        )

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "topic": "general",
        "max_results": MAX_RESULTS,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False,
    }

    response = requests.post(
        TAVILY_URL,
        json=payload,
        timeout=TIMEOUT,
    )

    # Ghi lỗi chính xác vào Railway Logs
    if not response.ok:
        logger.error(
            "TAVILY HTTP %s: %s",
            response.status_code,
            response.text,
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
            f"🔍 <b>Từ khóa:</b> "
            f"{html.escape(query)}\n\n"
            "❌ Không tìm thấy kết quả."
        ), None

    text = (
        "🔎 <b>KẾT QUẢ TÌM KIẾM INTERNET</b>\n\n"
        f"🔍 <b>Từ khóa:</b> "
        f"{html.escape(query)}\n"
        f"📊 <b>Kết quả:</b> {len(results)}\n\n"
    )

    buttons = []

    for index, result in enumerate(results, 1):

        title = result.get(
            "title",
            "Không có tiêu đề"
        )

        url = result.get(
            "url",
            ""
        )

        content = result.get(
            "content",
            ""
        )

        content = str(content)
        content = content.replace(
            "\n",
            " "
        ).strip()

        if len(content) > 300:
            content = content[:300] + "..."

        text += (
            f"<b>{index}. "
            f"{html.escape(str(title))}</b>\n"
            f"{html.escape(content)}\n\n"
        )

        if url:
            buttons.append([
                InlineKeyboardButton(
                    f"🌐 MỞ KẾT QUẢ {index}",
                    url=url
                )
            ])

    # Telegram giới hạn khoảng 4096 ký tự
    if len(text) > 3900:
        text = text[:3850] + "\n\n..."

    keyboard = (
        InlineKeyboardMarkup(buttons)
        if buttons
        else None
    )

    return text, keyboard


# =========================================================
# 🚀 START
# =========================================================

async def start(update, context):

    message = """
🤖 <b>INTERNET SEARCH BOT</b>

━━━━━━━━━━━━━━━━━━

🔎 Tìm kiếm thông tin trên Internet
🌐 Trả về các website liên quan
🔗 Có nút mở trực tiếp kết quả

<b>Cách sử dụng:</b>

/search laptop gaming

/search việc làm online

/search giá vàng hôm nay

Hoặc gửi câu hỏi trực tiếp cho bot.

━━━━━━━━━━━━━━━━━━

🌐 Search Engine: Tavily
⚡ Telegram
"""

    await update.message.reply_text(
        message,
        parse_mode=ParseMode.HTML
    )


# =========================================================
# ❓ HELP
# =========================================================

async def help_command(update, context):

    await update.message.reply_text(
        """
📚 <b>HƯỚNG DẪN</b>

🔎 Dùng:

<code>/search từ khóa</code>

Ví dụ:

<code>/search laptop gaming giá rẻ</code>

<code>/search điện thoại Samsung mới nhất</code>

<code>/search việc làm online tại nhà</code>

Bạn cũng có thể gửi câu hỏi trực tiếp.
""",
        parse_mode=ParseMode.HTML
    )


# =========================================================
# 🔎 SEARCH COMMAND
# =========================================================

async def search_command(update, context):

    if not context.args:
        await update.message.reply_text(
            "❌ Hãy nhập từ khóa.\n\n"
            "Ví dụ:\n"
            "<code>/search laptop gaming</code>",
            parse_mode=ParseMode.HTML
        )
        return

    query = " ".join(context.args).strip()

    await do_search(
        update,
        query
    )


# =========================================================
# 💬 MESSAGE
# =========================================================

async def message_handler(update, context):

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
# 🔎 DO SEARCH
# =========================================================

async def do_search(update, query):

    loading = await update.message.reply_text(
        "🔎 <b>Đang tìm kiếm Internet...</b>\n\n"
        "⏳ Vui lòng chờ...",
        parse_mode=ParseMode.HTML
    )

    try:

        logger.info(
            "Search query: %s",
            query
        )

        data = search_internet(query)

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
            "⏰ <b>Tavily phản hồi quá lâu.</b>\n\n"
            "Hãy thử lại.",
            parse_mode=ParseMode.HTML
        )

    except requests.exceptions.ConnectionError:

        await loading.edit_text(
            "🌐 <b>Không kết nối được Tavily.</b>\n\n"
            "Kiểm tra kết nối của Railway.",
            parse_mode=ParseMode.HTML
        )

    except requests.exceptions.HTTPError as error:

        response = error.response

        if response is not None:
            status = response.status_code
            detail = response.text
        else:
            status = "UNKNOWN"
            detail = str(error)

        logger.error(
            "Tavily HTTP %s: %s",
            status,
            detail
        )

        if status == 401:

            message = (
                "🔑 <b>Tavily API Key không hợp lệ.</b>\n\n"
                "HTTP 401\n\n"
                "Hãy kiểm tra lại TAVILY_API_KEY "
                "trong Railway Variables."
            )

        elif status == 403:

            message = (
                "🚫 <b>Tavily từ chối yêu cầu.</b>\n\n"
                "HTTP 403"
            )

        elif status == 429:

            message = (
                "⏳ <b>Tavily đang giới hạn request.</b>\n\n"
                "HTTP 429\n\n"
                "Kiểm tra quota/API plan."
            )

        else:

            message = (
                "❌ <b>Tavily API lỗi.</b>\n\n"
                f"HTTP: <code>{status}</code>\n\n"
                f"<code>"
                f"{html.escape(detail[:1000])}"
                f"</code>"
            )

        await loading.edit_text(
            message,
            parse_mode=ParseMode.HTML
        )

    except Exception as error:

        logger.exception(
            "Search error"
        )

        await loading.edit_text(
            "❌ <b>Bot gặp lỗi.</b>\n\n"
            f"<code>"
            f"{html.escape(str(error))}"
            f"</code>",
            parse_mode=ParseMode.HTML
        )


# =========================================================
# ❌ ERROR HANDLER
# =========================================================

async def error_handler(update, context):

    logger.error(
        "Telegram error: %s",
        context.error
    )


# =========================================================
# 🚀 MAIN
# =========================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "❌ Chưa cấu hình BOT_TOKEN trên Railway"
        )

    if not TAVILY_API_KEY:
        raise RuntimeError(
            "❌ Chưa cấu hình TAVILY_API_KEY trên Railway"
        )

    print("========================================")
    print("🤖 INTERNET SEARCH TELEGRAM BOT")
    print("🌐 Tavily Search")
    print("⚡ Railway 24/7")
    print("========================================")

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

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

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    application.add_error_handler(
        error_handler
    )

    print("✅ BOT ĐÃ SẴN SÀNG!")
    print("📡 Đang chờ Telegram...")

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
```
