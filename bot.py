# bot_railway_no_port.py
# Bot Telegram chạy trên Railway.app KHÔNG CẦN PORT
# Chỉ dùng Polling mode - không cần webhook
# Railway tự quản lý process 24/7

import os
import asyncio
import logging
import sys
import urllib.parse
from datetime import datetime
from typing import List, Dict
import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ApplicationBuilder
from tavily import TavilyClient

# ===== LOGGING =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ===== CẤU HÌNH =====
# KHÔNG CẦN PORT - chỉ cần 2 biến này
BOT_TOKEN = os.environ.get("8747823218:AAE5clUs5rSf-bF_MTQkxlnFiWk3LUUS8AY")
TAVILY_API_KEY = os.environ.get("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")

# Cấu hình tìm kiếm
MAX_RESULTS = 50
TIMEOUT = 20

# Khởi tạo
ua = UserAgent()
tavily_client = None
if TAVILY_API_KEY and TAVILY_API_KEY != "THAY_BANG_TAVILY_API_KEY":
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    logger.info("✅ Tavily API initialized")

# Thống kê
bot_start_time = datetime.now()
total_searches = 0
total_results = 0

class NoPortBot:
    def __init__(self):
        self.application = None
        self.is_running = False
    
    async def initialize(self):
        try:
            builder = ApplicationBuilder()
            builder.token(BOT_TOKEN)
            builder.concurrent_updates(True)
            builder.connect_timeout(30)
            builder.read_timeout(30)
            builder.write_timeout(30)
            
            self.application = builder.build()
            self.register_handlers()
            logger.info("✅ Bot initialized - No Port Mode")
            return True
        except Exception as e:
            logger.error(f"❌ Init error: {e}")
            return False
    
    def register_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("search", self.search_command))
        self.application.add_handler(CommandHandler("tim", self.search_command))
        self.application.add_handler(CommandHandler("tavily", self.tavily_search_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("ping", self.ping_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"❌ Error: {context.error}")
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text("⚠️ Lỗi. Bot tự khôi phục.")
            except:
                pass
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 BOT TÌM KIẾM 24/7 - RAILWAY.APP\n"
            "✅ KHÔNG CẦN PORT - POLLING MODE\n\n"
            "🔍 Tìm kiếm: Tavily AI + Google + Bing + DuckDuckGo + Yahoo + Brave\n\n"
            "📖 Lệnh:\n"
            "/search <từ khóa> - Tìm kiếm tổng hợp\n"
            "/tavily <từ khóa> - Tìm kiếm Tavily AI\n"
            "/status - Trạng thái\n"
            "/help - Trợ giúp"
        )
    
    async def ping_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uptime = datetime.now() - bot_start_time
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        await update.message.reply_text(
            f"🏓 PONG!\n"
            f"⏰ Uptime: {uptime.days}d {hours}h {minutes}m {seconds}s\n"
            f"🔍 Tìm kiếm: {total_searches}\n"
            f"🔗 Kết quả: {total_results}\n"
            f"📡 Mode: Polling (No Port)"
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uptime = datetime.now() - bot_start_time
        tavily_status = "✅ Active" if tavily_client else "❌ Not configured"
        await update.message.reply_text(
            f"📊 STATUS\n"
            f"🔄 Uptime: {uptime}\n"
            f"🔍 Tavily: {tavily_status}\n"
            f"📡 Mode: Polling - No Port Required\n"
            f"🔗 Total results: {total_results}"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📖 HELP\n\n"
            "/search <từ khóa> - Search all sources\n"
            "/tavily <từ khóa> - Tavily AI search\n"
            "/tim <từ khóa> - Alias\n"
            "/status - Status\n"
            "/ping - Check alive\n\n"
            "🤖 Gửi text trực tiếp để tìm kiếm"
        )
    
    async def search_tavily(self, query: str, max_results: int = 20) -> List[Dict]:
        results = []
        if not tavily_client:
            return results
        
        try:
            response = tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=True,
                include_raw_content=False,
                include_images=False
            )
            
            if response.get("answer"):
                results.append({
                    "url": "Tavily AI Answer",
                    "title": f"🤖 AI Answer: {response['answer'][:500]}",
                    "engine": "Tavily AI",
                    "content": response["answer"]
                })
            
            for result in response.get("results", []):
                results.append({
                    "url": result.get("url", ""),
                    "title": result.get("title", "")[:200],
                    "engine": "Tavily",
                    "content": result.get("content", "")[:300],
                    "score": result.get("score", 0)
                })
            
            if response.get("follow_up_questions"):
                for question in response["follow_up_questions"][:3]:
                    results.append({
                        "url": "Follow-up",
                        "title": f"❓ {question}",
                        "engine": "Tavily AI",
                        "content": ""
                    })
                    
        except Exception as e:
            logger.error(f"Tavily error: {e}")
        
        return results
    
    async def search_google(self, query: str) -> List[Dict]:
        results = []
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={MAX_RESULTS}"
        try:
            async with aiohttp.ClientSession(headers={"User-Agent": ua.random}) as session:
                async with session.get(url, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        for item in soup.select('div.g')[:MAX_RESULTS]:
                            link = item.select_one('a')
                            title_elem = item.select_one('h3')
                            if link and link.get('href') and link['href'].startswith('http'):
                                results.append({
                                    "url": link['href'],
                                    "title": title_elem.get_text()[:200] if title_elem else link['href'][:200],
                                    "engine": "Google"
                                })
        except Exception as e:
            logger.error(f"Google error: {e}")
        return results
    
    async def search_bing(self, query: str) -> List[Dict]:
        results = []
        url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&count={MAX_RESULTS}"
        try:
            async with aiohttp.ClientSession(headers={"User-Agent": ua.random}) as session:
                async with session.get(url, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        for item in soup.select('li.b_algo')[:MAX_RESULTS]:
                            link = item.select_one('a')
                            if link and link.get('href'):
                                results.append({
                                    "url": link['href'],
                                    "title": link.get_text()[:200],
                                    "engine": "Bing"
                                })
        except Exception as e:
            logger.error(f"Bing error: {e}")
        return results
    
    async def search_duckduckgo(self, query: str) -> List[Dict]:
        results = []
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        try:
            async with aiohttp.ClientSession(headers={"User-Agent": ua.random}) as session:
                async with session.get(url, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        for item in soup.select('div.result')[:MAX_RESULTS]:
                            link = item.select_one('a.result__a')
                            if link and link.get('href'):
                                href = link['href']
                                if 'uddg=' in href:
                                    actual_url = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])
                                else:
                                    actual_url = href
                                results.append({
                                    "url": actual_url,
                                    "title": link.get_text()[:200],
                                    "engine": "DuckDuckGo"
                                })
        except Exception as e:
            logger.error(f"DuckDuckGo error: {e}")
        return results
    
    async def search_yahoo(self, query: str) -> List[Dict]:
        results = []
        url = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}&n={MAX_RESULTS}"
        try:
            async with aiohttp.ClientSession(headers={"User-Agent": ua.random}) as session:
                async with session.get(url, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        for item in soup.select('div.dd.algo')[:MAX_RESULTS]:
                            link = item.select_one('a')
                            if link and link.get('href'):
                                results.append({
                                    "url": link['href'],
                                    "title": link.get_text()[:200],
                                    "engine": "Yahoo"
                                })
        except Exception as e:
            logger.error(f"Yahoo error: {e}")
        return results
    
    async def search_brave(self, query: str) -> List[Dict]:
        results = []
        url = f"https://search.brave.com/search?q={urllib.parse.quote(query)}&source=web"
        try:
            async with aiohttp.ClientSession(headers={"User-Agent": ua.random}) as session:
                async with session.get(url, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        for item in soup.select('div.snippet')[:MAX_RESULTS]:
                            link = item.select_one('a')
                            if link and link.get('href'):
                                results.append({
                                    "url": link['href'],
                                    "title": link.get_text()[:200],
                                    "engine": "Brave"
                                })
        except Exception as e:
            logger.error(f"Brave error: {e}")
        return results
    
    async def search_all(self, query: str) -> List[Dict]:
        all_results = []
        tasks = [
            self.search_tavily(query),
            self.search_google(query),
            self.search_bing(query),
            self.search_duckduckgo(query),
            self.search_yahoo(query),
            self.search_brave(query),
        ]
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for results in results_list:
            if isinstance(results, list):
                all_results.extend(results)
        
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result.get('url', '').rstrip('/')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        global total_searches, total_results
        query = ' '.join(context.args)
        
        if not query:
            await update.message.reply_text("⚠️ Nhập từ khóa: /search <từ khóa>")
            return
        
        total_searches += 1
        status_msg = await update.message.reply_text(f"🔍 Đang tìm: \"{query}\"...")
        
        try:
            results = await self.search_all(query)
            total_results += len(results)
            
            if not results:
                await status_msg.edit_text("❌ Không tìm thấy kết quả")
                return
            
            message = f"📊 {len(results)} KẾT QUẢ CHO: \"{query}\"\n" + "=" * 30 + "\n\n"
            messages = []
            current = message
            
            for i, result in enumerate(results, 1):
                entry = f"{i}. 🔗 {result['title'][:150]}\n"
                entry += f"   📍 {result['url']}\n"
                entry += f"   🔎 {result['engine']}\n"
                if result.get('content'):
                    entry += f"   📄 {result['content'][:200]}\n"
                if result.get('score'):
                    entry += f"   ⭐ {result['score']:.2f}\n"
                entry += "\n"
                
                if len(current) + len(entry) > 4000:
                    messages.append(current)
                    current = entry
                else:
                    current += entry
            
            if current:
                messages.append(current)
            
            await status_msg.edit_text("✅ Hoàn tất!")
            
            for msg in messages:
                await update.message.reply_text(msg)
                await asyncio.sleep(0.1)
            
            await status_msg.delete()
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            await status_msg.edit_text("⚠️ Lỗi. Thử lại.")
    
    async def tavily_search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = ' '.join(context.args)
        if not query:
            await update.message.reply_text("⚠️ /tavily <từ khóa>")
            return
        
        status_msg = await update.message.reply_text(f"🤖 Tavily AI: \"{query}\"...")
        
        try:
            results = await self.search_tavily(query, max_results=30)
            
            if not results:
                await status_msg.edit_text("❌ Không có kết quả")
                return
            
            message = f"🤖 TAVILY: {len(results)} KẾT QUẢ\n" + "=" * 30 + "\n\n"
            messages = []
            current = message
            
            for i, result in enumerate(results, 1):
                entry = f"{i}. {result['title'][:200]}\n"
                if result['url'] not in ["Tavily AI Answer", "Follow-up"]:
                    entry += f"   📍 {result['url']}\n"
                if result.get('content'):
                    entry += f"   📄 {result['content'][:300]}\n"
                if result.get('score'):
                    entry += f"   ⭐ {result['score']:.2f}\n"
                entry += "\n"
                
                if len(current) + len(entry) > 4000:
                    messages.append(current)
                    current = entry
                else:
                    current += entry
            
            if current:
                messages.append(current)
            
            await status_msg.edit_text("✅ Tavily xong!")
            
            for msg in messages:
                await update.message.reply_text(msg)
                await asyncio.sleep(0.1)
            
            await status_msg.delete()
            
        except Exception as e:
            logger.error(f"Tavily command error: {e}")
            await status_msg.edit_text("⚠️ Lỗi Tavily")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if text and len(text) > 2:
            context.args = text.split()
            await self.search_command(update, context)
    
    async def run(self):
        self.is_running = True
        logger.info("🚀 Bot starting - No Port Mode...")
        
        if not await self.initialize():
            logger.error("❌ Cannot initialize")
            return
        
        # Chạy polling - KHÔNG CẦN PORT
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(
            drop_pending_updates=True,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30,
            allowed_updates=Update.ALL_TYPES
        )
        logger.info("✅ Bot running - Polling mode - No Port Required")
        
        # Giữ bot chạy
        while self.is_running:
            await asyncio.sleep(1)
        
        # Cleanup
        await self.application.stop()
        await self.application.shutdown()

if __name__ == "__main__":
    bot = NoPortBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped")
    except Exception as e:
        logger.error(f"❌ Fatal: {e}")
