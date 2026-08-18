# bot_fixed.py
# Bot Telegram tìm kiếm Tavily - ĐÃ FIX LỖI
# Chạy 24/7 trên Railway.app không cần PORT

import os
import logging
import html
import asyncio
from datetime import datetime
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from tavily import TavilyClient

# =========================================================
# 🔑 API CONFIG - LẤY TỪ ENVIRONMENT VARIABLES
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8747823218:AAE5clUs5rSf-bF_MTQkxlnFiWk3LUUS8AY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "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")

# =========================================================
# ⚙️ SETTINGS
# =========================================================

MAX_RESULTS = 10
TIMEOUT = 60
bot_start_time = datetime.now()
total_searches = 0

# =========================================================
# LOG
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================================================
# 🌐 TAVILY CLIENT
# =========================================================

tavily_client = None
if TAVILY_API_KEY and TAVILY_API_KEY != "YOUR_TAVILY_API_KEY":
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        logger.info("✅ Tavily client initialized")
    except Exception as e:
        logger.error(f"❌ Tavily init error: {e}")

# =========================================================
# 🔎 SEARCH FUNCTION - DÙNG ASYNC
# =========================================================

async def search_internet_async(query: str):
    """Tìm kiếm Tavily bất đồng bộ"""
    if not tavily_client:
        raise ValueError("Tavily API Key không hợp lệ")
    
    # Chạy trong thread pool vì Tavily client là sync
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: tavily_client.search(
            query=query,
            search_depth="advanced",
            topic="general",
            max_results=MAX_RESULTS,
            include_answer=True,
            include_raw_content=False,
            include_images=False
        )
    )
    return result

# =========================================================
# 📄 FORMAT RESULTS
# =========================================================

def format_results(query, data):
    """Format kết quả tìm kiếm"""
    results = data.get("results", [])
    answer = data.get("answer", "")
    
    if not results and not answer:
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
    
    # Thêm AI answer nếu có
    if answer:
        text += f"🤖 <b>AI TRẢ LỜI:</b>\n{html.escape(answer)}\n\n"
        text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    buttons = []
    
    for i, item in enumerate(results, 1):
        title = item.get("title", "Không có tiêu đề")
        url = item.get("url", "")
        content = item.get("content", "")
        score = item.get("score", 0)
        
        # Làm sạch content
        content = content.replace("\n", " ").strip()
        if len(content) > 300:
            content = content[:300] + "..."
        
        text += f"<b>{i}. {html.escape(title)}</b>\n"
        
        if content:
            text += f"📄 {html.escape(content)}\n"
        
        if score:
            text += f"⭐ Độ liên quan: {score:.2f}\n"
        
        text += "\n"
        
        if url:
            buttons.append([
                InlineKeyboardButton(
                    f"🌐 MỞ KẾT QUẢ {i}",
                    url=url
                )
            ])
    
    # Giới hạn độ dài
    if len(text) > 3900:
        text = text[:3850] + "\n\n..."
    
    keyboard = InlineKeyboardMarkup(buttons) if buttons else None
    
    return text, keyboard

# =========================================================
# 🚀 START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = """
🤖 <b>INTERNET SEARCH BOT</b>

━━━━━━━━━━━━━━━━━━

🔎 Tìm kiếm thông tin trên Internet và gửi link liên quan.

<b>Cách sử dụng:</b>

<code>/search laptop gaming</code>
<code>/search việc làm online</code>
<code>/search giá vàng hôm nay</code>

Hoặc gửi câu hỏi trực tiếp.

━━━━━━━━━━━━━━━━━━

🌐 <b>Search Engine:</b> Tavily AI
⚡ <b>Chạy 24/7:</b> Railway.app
"""
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

# =========================================================
# ❓ HELP
# =========================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = """
📚 <b>HƯỚNG DẪN</b>

🔎 <b>Tìm kiếm:</b>

<code>/search từ khóa</code>

<b>Ví dụ:</b>

<code>/search điện thoại Samsung</code>
<code>/search laptop gaming giá rẻ</code>
<code>/search việc làm online</code>

Hoặc gửi câu hỏi trực tiếp cho bot.

━━━━━━━━━━━━━━━━━━

📊 <b>Lệnh khác:</b>

<code>/status</code> - Trạng thái bot
<code>/ping</code> - Kiểm tra bot sống
"""
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

# =========================================================
# 📊 STATUS
# =========================================================

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_searches, bot_start_time
    uptime = datetime.now() - bot_start_time
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    tavily_status = "✅ Hoạt động" if tavily_client else "❌ Lỗi API Key"
    
    message = f"""
📊 <b>TRẠNG THÁI BOT</b>

🔄 <b>Uptime:</b> {uptime.days}d {hours}h {minutes}m {seconds}s
🔍 <b>Tổng tìm kiếm:</b> {total_searches}
🌐 <b>Tavily:</b> {tavily_status}
📡 <b>Mode:</b> Polling (No Port)

━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

# =========================================================
# 🏓 PING
# =========================================================

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = datetime.now() - bot_start_time
    await update.message.reply_text(
        f"🏓 <b>PONG!</b>\n\n"
        f"⏰ Uptime: {uptime}\n"
        f"✅ Bot đang hoạt động bình thường",
        parse_mode=ParseMode.HTML
    )

# =========================================================
# 🔎 /SEARCH
# =========================================================

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Bạn chưa nhập từ khóa.\n\n"
            "Ví dụ:\n"
            "<code>/search laptop gaming</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    query = " ".join(context.args).strip()
    await do_search(update, query)

# =========================================================
# 💬 DIRECT MESSAGE
# =========================================================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    query = update.message.text.strip()
    if query:
        await do_search(update, query)

# =========================================================
# 🔎 SEARCH PROCESS
# =========================================================

async def do_search(update: Update, query: str):
    global total_searches
    total_searches += 1
    
    loading = await update.message.reply_text(
        "🔎 <b>Đang tìm kiếm Internet...</b>\n\n"
        "⏳ Đang thu thập kết quả từ Tavily AI...",
        parse_mode=ParseMode.HTML
    )
    
    try:
        logger.info("Searching: %s", query)
        
        data = await search_internet_async(query)
        
        text, keyboard = format_results(query, data)
        
        await loading.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        
    except asyncio.TimeoutError:
        await loading.edit_text(
            "⏰ <b>API tìm kiếm phản hồi quá lâu.</b>\n\n"
            "Hãy thử lại sau.",
            parse_mode=ParseMode.HTML
        )
        
    except ValueError as e:
        logger.error(f"Tavily value error: {e}")
        await loading.edit_text(
            "❌ <b>Lỗi cấu hình Tavily API.</b>\n\n"
            "Kiểm tra lại TAVILY_API_KEY trong biến môi trường.",
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.exception("Search error")
        await loading.edit_text(
            "❌ <b>Bot gặp lỗi.</b>\n\n"
            f"<code>{html.escape(str(e)[:200])}</code>",
            parse_mode=ParseMode.HTML
        )

# =========================================================
# ❌ ERROR HANDLER
# =========================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Telegram error: %s", context.error)
    
    # Gửi thông báo lỗi cho user
    if update and hasattr(update, 'effective_message') and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ <b>Đã xảy ra lỗi.</b>\n"
                "Bot sẽ tự khôi phục.",
                parse_mode=ParseMode.HTML
            )
        except:
            pass

# =========================================================
# 🚀 MAIN
# =========================================================

def main():
    # Kiểm tra API Keys
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.error("❌ Chưa nhập TELEGRAM BOT TOKEN")
        raise RuntimeError("❌ Chưa nhập TELEGRAM BOT TOKEN")
    
    if not TAVILY_API_KEY or TAVILY_API_KEY == "YOUR_TAVILY_API_KEY":
        logger.error("❌ Chưa nhập TAVILY API KEY")
        raise RuntimeError("❌ Chưa nhập TAVILY API KEY")
    
    print("=" * 40)
    print("🤖 INTERNET SEARCH TELEGRAM BOT")
    print("🌐 Tavily AI Search")
    print("📡 Mode: Polling - No Port")
    print("⚡ Bot đang khởi động...")
    print("=" * 40)
    
    # Tạo application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("ping", ping_command))
    
    # Tin nhắn thường
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )
    
    # Error handler
    application.add_error_handler(error_handler)
    
    print("✅ BOT ĐÃ SẴN SÀNG!")
    print("🔄 Chạy polling mode - không cần port")
    print("=" * 40)
    
    # Chạy bot - POLLING MODE
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()
