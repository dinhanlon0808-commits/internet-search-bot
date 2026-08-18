import html
import logging
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, TAVILY_API_KEY


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


TAVILY_URL = "https://api.tavily.com/search"


def search_web(query: str, max_results: int = 10):
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "topic": "general",
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False
    }

    response = requests.post(
        TAVILY_URL,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def make_result_message(query, data):
    results = data.get("results", [])

    if not results:
        return (
            f"🔎 <b>Kết quả tìm kiếm</b>\n\n"
            f"Từ khóa: <code>{html.escape(query)}</code>\n\n"
            "❌ Không tìm thấy kết quả phù hợp."
        )

    text = (
        f"🔎 <b>KẾT QUẢ TÌM KIẾM</b>\n\n"
        f"🔍 Từ khóa: <code>{html.escape(query)}</code>\n"
        f"📊 Tìm thấy: <b>{len(results)}</b> kết quả\n\n"
    )

    buttons = []

    for index, result in enumerate(results, 1):
        title = result.get("title", "Không có tiêu đề")
        url = result.get("url", "")
        content = result.get("content", "")

        title = html.escape(title)
        url = html.escape(url)

        content = content.replace("\n", " ").strip()

        if len(content) > 350:
            content = content[:350] + "..."

        content = html.escape(content)

        text += (
            f"<b>{index}. {title}</b>\n"
            f"{content}\n"
            f"🔗 <code>{url}</code>\n\n"
        )

        if url:
            buttons.append([
                InlineKeyboardButton(
                    f"🌐 Mở kết quả {index}",
                    url=result.get("url")
                )
            ])

    keyboard = InlineKeyboardMarkup(buttons)

    return text, keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "🤖 <b>INTERNET SEARCH BOT</b>\n\n"
        "Tôi có thể tìm kiếm thông tin trên Internet và gửi "
        "các kết quả liên quan cho bạn.\n\n"
        "📌 <b>Cách sử dụng:</b>\n\n"
        "🔎 <code>/search iphone 17 pro max</code>\n"
        "🔎 <code>/search việc làm online tại nhà</code>\n"
        "🔎 <code>/search giá vàng hôm nay</code>\n\n"
        "Hoặc chỉ cần gửi câu hỏi trực tiếp cho tôi."
    )

    await update.message.reply_text(
        message,
        parse_mode=ParseMode.HTML
    )


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❗ Hãy nhập từ khóa.\n\n"
            "Ví dụ:\n"
            "<code>/search laptop gaming giá rẻ</code>",
            parse_mode=ParseMode.HTML
        )
        return

    query = " ".join(context.args).strip()

    await perform_search(update, query)


async def normal_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    if not query:
        return

    await perform_search(update, query)


async def perform_search(update: Update, query: str):
    waiting = await update.message.reply_text(
        "🔎 Đang tìm kiếm Internet...\n"
        "⏳ Vui lòng chờ một chút."
    )

    try:
        data = search_web(query, max_results=10)

        result = make_result_message(query, data)

        if isinstance(result, tuple):
            text, keyboard = result

            await waiting.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        else:
            await waiting.edit_text(
                result,
                parse_mode=ParseMode.HTML
            )

    except requests.exceptions.Timeout:
        await waiting.edit_text(
            "⏰ Máy chủ tìm kiếm phản hồi quá lâu.\n"
            "Vui lòng thử lại."
        )

    except requests.exceptions.HTTPError:
        await waiting.edit_text(
            "❌ API tìm kiếm trả về lỗi.\n\n"
            "Kiểm tra lại TAVILY_API_KEY."
        )

    except Exception as e:
        logging.exception(e)

        await waiting.edit_text(
            "❌ Đã xảy ra lỗi khi tìm kiếm.\n"
            "Vui lòng thử lại sau."
        )


def main():
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("search", search_command)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            normal_message
        )
    )

    print("===================================")
    print(" INTERNET SEARCH TELEGRAM BOT")
    print(" Bot đang chạy...")
    print("===================================")

    application.run_polling()


if __name__ == "__main__":
    main()