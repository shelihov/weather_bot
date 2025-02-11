from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from keyboards.keyboards import *
from lexicon.lexicon import RUSSIAN_CITIES, LEXICON
import aiohttp
import os
from datetime import datetime

router = Router()
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

async def get_weather(city: str):
    coordinates = RUSSIAN_CITIES[city]
    async with aiohttp.ClientSession() as session:
        params = {
            'lat': coordinates['lat'],
            'lon': coordinates['lon'],
            'appid': WEATHER_API_KEY,
            'units': 'metric',
            'lang': 'ru'
        }
        async with session.get("http://api.openweathermap.org/data/2.5/weather", params=params) as response:
            data = await response.json()
            return {
                'temp': round(data['main']['temp']),
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'feels_like': round(data['main']['feels_like'])
            }

@router.message(CommandStart())
async def start_command(message: Message):
    await message.answer(LEXICON['start'], reply_markup=location_keyboard)

@router.message(Command(commands=['help']))
async def help_command(message: Message):
    await message.answer(LEXICON['help'], reply_markup=location_keyboard)

@router.message(F.location)
async def location_handler(message: Message):
    await message.answer(f"Получено местоположение: {message.location.latitude}, {message.location.longitude}")

@router.message(F.text)
async def handle_city_text(message: Message):
    city = message.text.strip().title()
    if city in RUSSIAN_CITIES:
        try:
            weather = await get_weather(city)
            await message.answer(
                f"🏙 Погода в городе {city}:\n\n"
                f"🌡 Температура: {weather['temp']}°C\n"
                f"🤔 Ощущается как: {weather['feels_like']}°C\n"
                f"☁️ {weather['description'].capitalize()}\n"
                f"💧 Влажность: {weather['humidity']}%",
                reply_markup=weather_keyboard
            )
        except Exception as e:
            await message.answer(
                "Извините, произошла ошибка при получении погоды. Попробуйте позже.",
                reply_markup=location_keyboard
            )
    else:
        await message.answer(
            "Извините, такой город не найден. Попробуйте другой или отправьте местоположение.",
            reply_markup=location_keyboard
        )
