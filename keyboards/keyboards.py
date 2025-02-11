from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

button_today = InlineKeyboardButton(text='Сегодня', callback_data='today')
button_tomorrow = InlineKeyboardButton(text='Завтра', callback_data='tomorrow')
button_week = InlineKeyboardButton(text='На неделю', callback_data='week')

weather_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [button_today, button_tomorrow, button_week]
])

# Изменяем на обычную клавиатуру для кнопки местоположения
location_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📍 Отправить местоположение", request_location=True)]],
    resize_keyboard=True
)