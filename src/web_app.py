from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils import executor

BOT_TOKEN = '8273727945:AAG8ZIr1nEJCh_G6rQsNKZSEzH0OGUg71VE'

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    web_app_btn = KeyboardButton(
        text="Открыть Graffiti Report",
        web_app=WebAppInfo(url="https://tau-lavender.github.io/graffity_report/")
    )
    keyboard.add(web_app_btn)
    await message.answer("Нажми на кнопку ниже, чтобы открыть мини-приложение:", reply_markup=keyboard)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
