from aiogram import Bot, Dispatcher
from handlers.handlers import router
from dotenv import load_dotenv
from lexicon.lexicon import RUSSIAN_CITIES, LEXICON
import os
from keyboards.keyboards import *

load_dotenv()
# Замените на свои токены
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(router)

if __name__ == '__main__':
    dp.run_polling(bot)