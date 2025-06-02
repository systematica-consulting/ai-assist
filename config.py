from telegram.ext import ApplicationBuilder
import os
import logging


# Telegram Bot Token
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "Ваш токен")
AI_TOKEN = os.environ.get("AI_TOKEN", "Ваш токен")
DEEP_SEEK_TOKEN = os.environ.get("DEEP_SEEK_TOKEN", "Ваш токен")
db_name= os.environ.get("DB_NAME", "Ваш токен")
db_user= os.environ.get("DB_USER", "Ваш токен")
db_password= os.environ.get("DB_PASSWORD", "Ваш токен")
db_host= os.environ.get("DB_HOST", "Ваш токен")