from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import aiohttp
import pytz
import asyncio
import dotenv
import os
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.client.default import DefaultBotProperties

dotenv.load_dotenv()

# Замените на свои токены
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler()

# Состояния FSM
class UserState(StatesGroup):
    waiting_for_location = State()

# Хранилище локаций пользователей
user_locations = {}

def get_main_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🌤 Узнать погоду сейчас")],
        [KeyboardButton(text="📍 Изменить местоположение", request_location=True)]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_location_keyboard() -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text="Отправить местоположение", request_location=True)]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    await message.answer(
        "Привет! Я бот прогноза погоды.\n"
        "Вы можете:\n"
        "1. Отправить местоположение с мобильного устройства\n"
        "2. Использовать команду /setlocation ШИРОТА ДОЛГОТА\n"
        "Например: /setlocation 55.7558 37.6173 (координаты Москвы)",
        reply_markup=get_location_keyboard()
    )
    await state.set_state(UserState.waiting_for_location)

@dp.message(lambda message: message.text and message.text.startswith('/setlocation'))
async def handle_location_command(message: types.Message):
    try:
        _, lat, lon = message.text.split()
        lat, lon = float(lat), float(lon)
        user_locations[message.from_user.id] = {
            'lat': lat,
            'lon': lon
        }
        await message.answer(
            "Местоположение успешно установлено!\n"
            "Теперь вы будете получать уведомления о погоде каждый день в 19:00.",
            reply_markup=get_main_keyboard()
        )
    except ValueError:
        await message.answer(
            "Неверный формат. Используйте: /setlocation <широта> <долгота>\n"
            "Например: /setlocation 55.7558 37.6173"
        )

@dp.message(UserState.waiting_for_location, F.location)
async def handle_location(message: types.Message, state: FSMContext):
    try:
        user_locations[message.from_user.id] = {
            'lat': message.location.latitude,
            'lon': message.location.longitude
        }
        
        # Проверяем работу API сразу
        weather = await get_current_weather(
            message.location.latitude,
            message.location.longitude
        )
        
        await message.answer(
            "Спасибо! Теперь вы будете получать уведомления о погоде каждый день в 19:00.\n"
            "Также вы можете узнать погоду в любой момент, нажав на кнопку ниже.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        
        # Отправляем текущую погоду сразу
        await message.answer(
            f"🌤 <b>Текущая погода:</b>\n\n"
            f"🌡 Температура: {weather['temp']}°C\n"
            f"🤔 Ощущается как: {weather['feels_like']}°C\n"
            f"☁️ Погода: {weather['description']}\n"
            f"💧 Влажность: {weather['humidity']}%"
        )
    except Exception as e:
        print(f"Ошибка при обработке местоположения: {e}")
        await message.answer(
            "Извините, произошла ошибка при получении данных о погоде.\n"
            "Пожалуйста, попробуйте отправить местоположение еще раз.",
            reply_markup=get_location_keyboard()
        )

@dp.message(F.location)
async def handle_new_location(message: types.Message):
    user_locations[message.from_user.id] = {
        'lat': message.location.latitude,
        'lon': message.location.longitude
    }
    await message.answer("Местоположение успешно обновлено!", reply_markup=get_main_keyboard())

async def get_current_weather(lat: float, lon: float) -> dict:
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': WEATHER_API_KEY,
                'units': 'metric',
                'lang': 'ru'
            }
            print(f"Отправка запроса к OpenWeather API с параметрами: {params}")
            
            async with session.get("http://api.openweathermap.org/data/2.5/weather", params=params) as response:
                if response.status != 200:
                    error_data = await response.text()
                    print(f"OpenWeather API error: Status {response.status}")
                    print(f"Error details: {error_data}")
                    print(f"API Key used: {WEATHER_API_KEY}")
                    raise Exception(f"API вернул статус {response.status}: {error_data}")
                
                data = await response.json()
                print(f"Успешный ответ от API: {data}")
                
                return {
                    'temp': round(data['main']['temp']),
                    'description': data['weather'][0]['description'],
                    'humidity': data['main']['humidity'],
                    'feels_like': round(data['main']['feels_like'])
                }
    except Exception as e:
        print(f"Ошибка при получении погоды: {str(e)}")
        print(f"Тип ошибки: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise

async def get_weather_forecast(lat: float, lon: float) -> dict:
    async with aiohttp.ClientSession() as session:
        params = {
            'lat': lat,
            'lon': lon,
            'appid': WEATHER_API_KEY,
            'units': 'metric',
            'lang': 'ru'
        }
        async with session.get("http://api.openweathermap.org/data/2.5/forecast", params=params) as response:
            data = await response.json()
            tomorrow = datetime.now().date()
            for item in data['list']:
                forecast_date = datetime.fromtimestamp(item['dt']).date()
                if forecast_date > tomorrow:
                    return {
                        'temp': round(item['main']['temp']),
                        'description': item['weather'][0]['description'],
                        'humidity': item['main']['humidity']
                    }

@dp.message(F.text == "🌤 Узнать погоду сейчас")
async def get_current_weather_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_locations:
        await message.answer(
            "Пожалуйста, сначала отправьте своё местоположение.",
            reply_markup=get_main_keyboard()
        )
        return

    try:
        weather = await get_current_weather(
            user_locations[user_id]['lat'],
            user_locations[user_id]['lon']
        )
        await message.answer(
            f"🌤 <b>Текущая погода:</b>\n\n"
            f"🌡 Температура: {weather['temp']}°C\n"
            f"🤔 Ощущается как: {weather['feels_like']}°C\n"
            f"☁️ Погода: {weather['description']}\n"
            f"💧 Влажность: {weather['humidity']}%"
        )
    except Exception as e:
        await message.answer("Извините, не удалось получить данные о погоде. Попробуйте позже.")

async def send_weather_notifications():
    for user_id, location in user_locations.items():
        try:
            weather = await get_weather_forecast(location['lat'], location['lon'])
            message = (
                f"🌤 <b>Прогноз погоды на завтра:</b>\n\n"
                f"🌡 Температура: {weather['temp']}°C\n"
                f"☁️ Погода: {weather['description']}\n"
                f"💧 Влажность: {weather['humidity']}%"
            )
            await bot.send_message(user_id, message)
        except Exception as e:
            print(f"Ошибка отправки уведомления пользователю {user_id}: {e}")

async def main():
    scheduler.add_job(
        send_weather_notifications,
        trigger='cron',
        hour=19,
        minute=0,
        timezone=pytz.timezone('Europe/Moscow')
    )
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 