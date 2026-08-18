import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("Chưa cấu hình BOT_TOKEN trong file .env")

if not TAVILY_API_KEY:
    raise RuntimeError("Chưa cấu hình TAVILY_API_KEY trong file .env")