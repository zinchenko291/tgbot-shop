import os
import asyncio
from datetime import date
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging

from db import BotDB

load_dotenv()
TOKEN = os.getenv('API_TOKEN')
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

class StateMachine(StatesGroup):
    phone_number = State()
    menu = State()
    products = State() # Список из категории
    product = State() # Описание товара
    orderAcception = State()
    order = State()

# Старт
@dp.message_handler(commands="start", state='*')
async def cmd_start(message: types.Message):
    user = message.from_user
    if db.user_exists(user.id):
        await message.answer(f"Здравствуйте, {user.first_name}!\nДавно не видились!")
        await StateMachine.menu.set()
        await cmd_menu(message)
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(types.KeyboardButton("Отправить контакт", request_contact=True))
        await message.answer(f"Здравствуйте, {user.first_name}!")
        await message.answer("Пожалуйста зарегистрируйтесь, чтобы пользоваться ботом. Для регистрации требуется номер телефона.", reply_markup=keyboard)
        await StateMachine.phone_number.set()

# Регистрация пользователя через номер телефона
@dp.message_handler(content_types=types.ContentType.CONTACT, state=StateMachine.phone_number)
async def get_contact(message: types.Message):
    user = message.from_user
    keyboard = types.ReplyKeyboardRemove()
    db.add_user(user.id, user.username, message.contact.phone_number)
    await message.answer("Спасибо за регистрацию, давайте приступим к покупкам.", reply_markup=keyboard)
    await StateMachine.menu.set()
    await cmd_menu(message)

@dp.message_handler(content_types=types.ContentType.TEXT, state=StateMachine.phone_number)
async def get_contact_from_text(message: types.Message):
    user = message.from_user
    keyboard = types.ReplyKeyboardRemove()
    db.add_user(user.id, user.username, int(message.text))
    await message.answer("Спасибо за регистрацию, давайте приступим к покупкам.", reply_markup=keyboard)
    await StateMachine.menu.set()
    await cmd_menu(message)

# Каталог товаров
@dp.message_handler(commands="menu")
async def cmd_menu(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    categories = db.get_categories()
    for name in categories:
        keyboard.add(name)
    await message.answer("Выберете категорию товаров:", reply_markup=keyboard)
    await StateMachine.products.set()

# Товары одной категории
@dp.message_handler(state=StateMachine.products, content_types=types.ContentType.TEXT)
async def send_products(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    category_id = db.get_category_id(message.text)
    products = db.get_products_in_category(category_id)
    for name in products:
        keyboard.add(name)
    await message.answer("Выберете товар:", reply_markup=keyboard)
    await StateMachine.product.set()

# Информация о товаре
@dp.message_handler(state=StateMachine.product, content_types=types.ContentType.TEXT)
async def send_product(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("Заказываем")
    keyboard.add("Отмена")
    name = message.text
    product_id = db.get_product_id(name)
    product = db.get_product(product_id)
    await message.answer_photo(types.InputFile(f"{os.getenv('IMGS')}/{product.get('image_path')}"))
    await message.answer(f"Название: <b>{name}</b>\nОписание: <i>{product.get('description')}</i>\nЦена: {product.get('price')} рубелй", parse_mode=types.ParseMode.HTML, reply_markup=keyboard)
    await StateMachine.orderAcception.set()
    async with state.proxy() as data:
        data["product"] = product

# Подтверждение заказа
@dp.message_handler(state=StateMachine.orderAcception, content_types=types.ContentType.TEXT)
async def send_orderAcception(message: types.Message):
    if message.text == "Отмена":
        await message.answer("Чтобы снова использовать магазин, напишите /start.")
    else:
        await message.answer("Укажите время доставки(ДД-ММ):")
        await StateMachine.order.set()

# Выбор даты
@dp.message_handler(state=StateMachine.order, content_types=types.ContentType.TEXT)
async def send_order(message: types.Message, state: FSMContext):
    product = 0
    async with state.proxy() as data:
        product = data["product"]
    order_date = f"{date.today().year}-{date.today().month}-{date.today().day}"
    delivery_date = message.text.split('-')
    delivery_date = f"{date.today().year}-{delivery_date[1]}-{delivery_date[0]}"
    db.add_order(message.from_user.id, product.get("id"), order_date, delivery_date)
    await message.answer(f"Спасибо, что воспользовались нашим сервисом.\nЧтобы снова использовать магазин, напишите /start.")

if __name__ == "__main__":
    print(f"[INFO] - Запуск бота")
    db = BotDB(os.getenv("DATABASE_FILE_PATH"))
    executor.start_polling(dp, skip_updates=True)
    db.close()
    print(f"[INFO] - База данных закрыта")
    print(f"[INFO] - Завершение работы бота")