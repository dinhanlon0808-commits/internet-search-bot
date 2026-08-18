```python
import html
import logging
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
# 🔑 API CONFIG
# =========================================================

# THAY 2 GIÁ TRỊ NÀY BẰNG KEY MỚI CỦA BẠN
BOT_TOKEN = "8747823218:AAE5clUs5rSf-bF_MTQkxlnFiWk3LUUS8AY"

TAVILY_API_KEY = "0c1395317ffa5ae9665f09caab089985a66ec1a599c4811f7b55f5429453af95"


# =========================================================
# ⚙️ SETTINGS
# =========================================================

TAVILY_URL = "https://api.tavily.com/search"

MAX_RESULTS = 10

REQUEST_TIMEOUT = 60


# =========================================================
# 📝 LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# 🌐 TAVILY SEARCH
# =========================================================

def search_internet(query: str):

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
        timeout=REQUEST_TIMEOUT,
    )

    # In lỗi API ra Railway Logs
    if not response.ok:

        print("========================================")
        print("TAVILY API ERROR")
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)
        print("========================================")

        response.raise_for_status()

    return response.json()


# =========================================================
# 📄 FORMAT RESULTS
# =========================================================

def format_results(query: str, data: dict):

    results = data.get("results", [])

    if not results:

        text = (
            "🔎 <b>KẾT QUẢ TÌM KIẾM</b>\n\n"
            f"🔍 <b>Từ khóa:</b> "
            f"{html.escape(query)}\n\n"
            "❌ Không tìm thấy kết quả."
        )

        return text, None

    text = (
        "🔎 <b>KẾT QUẢ TÌM KIẾM INTERNET</b>\n\n"
        f"🔍 <b>Từ khóa:</b> "
        f"{html.escape(query)}\n"
        f"📊 <b>Số kết quả:</b> "
        f"{len(results)}\n\n"
    )

    buttons = []

    for index, item in enumerate(results, start=1):

        title = item.get(
            "title",
            "Không có tiêu đề",
        )

        url = item.get(
            "url",
            "",
        )

        content = item.get(
            "content",
            "",
        )

        # Làm sạch mô tả
        content = str(content)
        content = content.replace(
            "\n",
            " ",
        ).strip()

        # Giới hạn mô tả
        if len(content) > 300:
            content = content[:300] + "..."

        text += (
            f"<b>{index}. "
            f"{html.escape(str(title))}</b>\n"
            f"{html.escape(content)}\n\n"
        )

        if url:

            buttons.append(
                [
                    InlineKeyboardButton(
                        f"🌐 MỞ KẾT QUẢ {index}",
                        url=url,
                    )
                ]
            )

    # Telegram giới hạn khoảng 4096 ký tự
    if len(text) > 3900:

        text = text[:3850]

        text += (
            "\n\n"
            "⚠️ Nội dung đã được rút gọn."
        )

    keyboard = None

    if buttons:
        keyboard = InlineKeyboardMarkup(
            buttons
        )

    return text, keyboard


# =========================================================
# 🚀 /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = """
🤖 <b>INTERNET SEARCH BOT</b>

━━━━━━━━━━━━━━━━━━

🔎 Tôi có thể tìm kiếm thông tin trên Internet và gửi các đường link liên quan.

<b>Cách sử dụng:</b>

<code>/search laptop gaming</code>

<code>/search việc làm online</code>

<code>/search giá vàng hôm nay</code>

Hoặc chỉ cần gửi câu hỏi trực tiếp cho bot.

━━━━━━━━━━━━━━━━━━

🌐 Search: Tavily
⚡ Telegram Bot
"""

    await update.message.reply_text(
        message,
        parse_mode=ParseMode.HTML,
    )


# =========================================================
# ❓ /HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = """
📚 <b>HƯỚNG DẪN SỬ DỤNG</b>

🔎 Tìm kiếm:

<code>/search từ khóa</code>

Ví dụ:

<code>/search điện thoại Samsung mới nhất</code>

<code>/search laptop gaming giá rẻ</code>

<code>/search việc làm online tại nhà</code>

Bạn cũng có thể gửi câu hỏi trực tiếp.
"""

    await update.message.reply_text(
        message,
        parse_mode=ParseMode.HTML,
    )


# =========================================================
# 🔎 /SEARCH
# =========================================================

async def search_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not context.args:

        await update.message.reply_text(
            "❌ Bạn chưa nhập từ khóa.\n\n"
            "Ví dụ:\n"
            "<code>/search laptop gaming</code>",
            parse_mode=ParseMode.HTML,
        )

        return

    query = " ".join(
        context.args
    ).strip()

    await do_search(
        update,
        query,
    )


# =========================================================
# 💬 MESSAGE
# =========================================================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
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
        query,
    )


# =========================================================
# 🔎 SEARCH PROCESS
# =========================================================

async def do_search(
    update: Update,
    query: str,
):

    loading = await update.message.reply_text(
        "🔎 <b>Đang tìm kiếm Internet...</b>\n\n"
        "⏳ Đang thu thập kết quả...",
        parse_mode=ParseMode.HTML,
    )

    try:

        logger.info(
            "Searching: %s",
            query,
        )

        data = search_internet(
            query,
        )

        text, keyboard = format_results(
            query,
            data,
        )

        await loading.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    # -----------------------------------------------------
    # TIMEOUT
    # -----------------------------------------------------

    except requests.exceptions.Timeout:

        await loading.edit_text(
            "⏰ <b>Tìm kiếm bị timeout.</b>\n\n"
            "Máy chủ tìm kiếm phản hồi quá lâu.\n"
            "Hãy thử lại.",
            parse_mode=ParseMode.HTML,
        )

    # -----------------------------------------------------
    # CONNECTION
    # -----------------------------------------------------

    except requests.exceptions.ConnectionError:

        await loading.edit_text(
            "🌐 <b>Không kết nối được Tavily.</b>\n\n"
            "Kiểm tra kết nối Internet/API.",
            parse_mode=ParseMode.HTML,
        )

    # -----------------------------------------------------
    # HTTP ERROR
    # -----------------------------------------------------

    except requests.exceptions.HTTPError as error:

        response = error.response

        if response is not None:

            status = response.status_code

            try:
                detail = response.text
            except Exception:
                detail = str(error)

        else:

            status = "UNKNOWN"
            detail = str(error)

        logger.error(
            "Tavily HTTP %s: %s",
            status,
            detail,
        )

        # Các lỗi phổ biến
        if status == 401:

            message = (
                "🔑 <b>Tavily API Key không hợp lệ.</b>\n\n"
                "HTTP 401\n\n"
                "Hãy tạo API key Tavily mới."
            )

        elif status == 403:

            message = (
                "🚫 <b>Tavily từ chối yêu cầu.</b>\n\n"
                "HTTP 403\n\n"
                "Kiểm tra quyền truy cập/API key."
            )

        elif status == 429:

            message = (
                "⏳ <b>Tavily đang giới hạn request.</b>\n\n"
                "HTTP 429\n\n"
                "Có thể API đã hết quota hoặc "
                "gửi quá nhiều yêu cầu."
            )

        elif status == 400:

            message = (
                "⚠️ <b>Tavily nhận request không hợp lệ.</b>\n\n"
                "HTTP 400\n\n"
                f"<code>{html.escape(detail[:1000])}</code>"
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
            parse_mode=ParseMode.HTML,
        )

    # -----------------------------------------------------
    # OTHER ERROR
    # -----------------------------------------------------

    except Exception as error:

        logger.exception(
            "Search error",
        )

        await loading.edit_text(
            "❌ <b>Bot gặp lỗi.</b>\n\n"
            f"<code>"
            f"{html.escape(str(error))}"
            f"</code>",
            parse_mode=ParseMode.HTML,
        )


# =========================================================
# ❌ TELEGRAM ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logger.error(
        "Telegram error: %s",
        context.error,
    )


# =========================================================
# 🚀 MAIN
# =========================================================

def main():

    # Kiểm tra Telegram Token
    if (
        not BOT_TOKEN
        or BOT_TOKEN == "YOUR_NEW_TELEGRAM_BOT_TOKEN"
    ):

        raise RuntimeError(
            "❌ Chưa cấu hình Telegram Bot Token."
        )

    # Kiểm tra Tavily API
    if (
        not TAVILY_API_KEY
        or TAVILY_API_KEY == "YOUR_NEW_TAVILY_API_KEY"
    ):

        raise RuntimeError(
            "❌ Chưa cấu hình Tavily API Key."
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
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "search",
            search_command,
        )
    )

    # Tin nhắn thường
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            message_handler,
        )
    )

    # Error handler
    application.add_error_handler(
        error_handler,
    )

    print(
        "✅ BOT ĐÃ SẴN SÀNG!"
    )

    print(
        "📡 Đang chờ tin nhắn Telegram..."
    )

    # Long polling
    application.run_polling(
        drop_pending_updates=True,
    )


# =========================================================
# ▶️ RUN
# =========================================================

if __name__ == "__main__":
    main()
```
