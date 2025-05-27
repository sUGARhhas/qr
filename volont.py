import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, any_state, default_state
import logging
import os
from dotenv import load_dotenv
from db import create_db
from data import load_volunteer_data, load_user_ids, save_user_ids
import aiosqlite
from aiogram.filters import Command, StateFilter

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN') or '7651729532:AAG4AdLaMYQZbdW1WWjr2nVULRKmdsTsalo'
ADMIN_ID = int(os.getenv('ADMIN_ID', '6356238822'))

volunteer_data = load_volunteer_data()
user_ids = load_user_ids()

main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📖Что такое волонтерство")],
        [KeyboardButton(text="🤝Вступление в волонтерство"), KeyboardButton(text="🆘Выбор помощи")],
        [KeyboardButton(text="Сайт dobro.ru"), KeyboardButton(text="Почему именно мы?")],
        [KeyboardButton(text="🛠Тех.поддержка")],
    ],
    resize_keyboard=True
)

# --- FSM для помощи ---
class HelpStates(StatesGroup):
    city = State()
    page = State()

# --- Обработчики главного меню ---
async def main_menu_handler(message: Message, state: FSMContext):
    text = message.text
    if text == "📖Что такое волонтерство":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Подробнее", url="https://vk.com/@proectva-volonterstvo-polnoe-rukovodstvo")]
            ]
        )
        await message.answer(
            "Руководство о волонтёрстве:",
            reply_markup=kb
        )
    elif text == "🛠Тех.поддержка":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Написать в поддержку", url="https://t.me/help_Emy_off_bot")]
            ]
        )
        await message.answer(
            "Связаться с техподдержкой:",
            reply_markup=kb
        )
    elif text == "🤝Вступление в волонтерство":
        cities = [
            [KeyboardButton(text=city)] for city in volunteer_data['volunteer_entry'].keys()
        ] + [[KeyboardButton(text="🔙Назад")]]
        await message.answer("🌍Выберите город для вступления", reply_markup=ReplyKeyboardMarkup(keyboard=cities, resize_keyboard=True))
        await state.set_state("entry_city")
    elif text == "🆘Выбор помощи":
        cities = [
            [KeyboardButton(text=city)] for city in volunteer_data['help_data'].keys()
        ] + [[KeyboardButton(text="🔙Назад")]]
        await message.answer("🌍Выберите город для получения помощи", reply_markup=ReplyKeyboardMarkup(keyboard=cities, resize_keyboard=True))
        await state.set_state(HelpStates.city)
    elif text == "Сайт dobro.ru":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Вход", url="https://dobro.ru/login?__target_path=/dashboard"),
                    InlineKeyboardButton(text="Регистрация", url="https://dobro.ru/register?__target_path=%2Fdashboard")
                ]
            ]
        )
        await message.answer("Выберите действие:", reply_markup=kb)
    elif text == "Почему именно мы?":
        info = volunteer_data['why_us']
        await message.answer(f"{info['title']}\n\n{info['content']}", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙Назад")]], resize_keyboard=True))
    elif text == "🔙Назад":
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
    else:
        await message.answer("Пожалуйста, выберите кнопку из меню.", reply_markup=main_menu_kb)

# --- Команды администратора ---
async def cmd_check(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет прав для этой команды.")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /check <ID или @username>")
        return
    identifier = args[1].replace('@', '')
    async with aiosqlite.connect('users.db') as db:
        if identifier.isdigit():
            async with db.execute('SELECT * FROM users WHERE telegram_id = ?', (int(identifier),)) as cursor:
                user = await cursor.fetchone()
        else:
            async with db.execute('SELECT * FROM users WHERE username = ?', (identifier,)) as cursor:
                user = await cursor.fetchone()
        if not user:
            await message.answer("Пользователь не найден")
            return
        await db.execute('UPDATE users SET is_confirmed = 1 WHERE telegram_id = ?', (user[0],))
        await db.commit()
    await message.answer(f"Профиль пользователя {user[2]} {user[1]} подтвержден")

async def cmd_add_work(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет прав для этой команды.")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /add_work <ID или @username>")
        return
    identifier = args[1].replace('@', '')
    async with aiosqlite.connect('users.db') as db:
        if identifier.isdigit():
            async with db.execute('SELECT * FROM users WHERE telegram_id = ?', (int(identifier),)) as cursor:
                user = await cursor.fetchone()
        else:
            async with db.execute('SELECT * FROM users WHERE username = ?', (identifier,)) as cursor:
                user = await cursor.fetchone()
        if not user:
            await message.answer("Пользователь не найден")
            return
        await db.execute('UPDATE users SET completed_works = completed_works + 1 WHERE telegram_id = ?', (user[0],))
        await db.commit()
    await message.answer(f"Работа зачтена пользователю {user[2]} {user[1]}")

async def cmd_remove_work(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет прав для этой команды.")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /remove_work <ID или @username>")
        return
    identifier = args[1].replace('@', '')
    async with aiosqlite.connect('users.db') as db:
        if identifier.isdigit():
            async with db.execute('SELECT * FROM users WHERE telegram_id = ?', (int(identifier),)) as cursor:
                user = await cursor.fetchone()
        else:
            async with db.execute('SELECT * FROM users WHERE username = ?', (identifier,)) as cursor:
                user = await cursor.fetchone()
        if not user:
            await message.answer("Пользователь не найден")
            return
        await db.execute('UPDATE users SET completed_works = MAX(completed_works - 1, 0) WHERE telegram_id = ?', (user[0],))
        await db.commit()
    await message.answer(f"Работа убрана у пользователя {user[2]} {user[1]}")

async def cmd_send_announcement(message: Message, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет прав для этой команды.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Пожалуйста, введите текст объявления после команды.")
        return
    announcement_text = args[1]
    from data import load_user_ids, load_volunteer_data
    user_ids = load_user_ids()
    volunteer_data = load_volunteer_data()
    msg = volunteer_data['announcements']['broadcast_template'].format(message=announcement_text)
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=int(user_id), text=msg)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
    await message.answer("Объявление отправлено всем пользователям.")

# --- Выбор города для помощи ---
async def help_city(message: Message, state: FSMContext):
    if message.text in volunteer_data['help_data']:
        await state.update_data(help_city=message.text, help_page=0)
        await show_help_event(message, state)
        await state.set_state(HelpStates.page)
    elif message.text == "🔙Назад":
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
        await state.clear()
    else:
        await message.answer("Пожалуйста, выберите город из списка.")

# --- Просмотр события по городу и странице ---
async def show_help_event(message: Message, state: FSMContext):
    data = await state.get_data()
    city = data.get('help_city')
    page = data.get('help_page', 0)
    events = volunteer_data['help_data'].get(city, [])
    if not events:
        await message.answer("Нет событий для этого города.", reply_markup=main_menu_kb)
        await state.clear()
        return
    total_pages = len(events)
    event_text = events[page]
    nav_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️"), KeyboardButton(text="▶️")],
            [KeyboardButton(text="🔙Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer(f"{event_text}\n\nСтраница {page + 1} из {total_pages}", reply_markup=nav_kb)

# --- Перелистывание страниц ---
async def help_page_nav(message: Message, state: FSMContext):
    data = await state.get_data()
    city = data.get('help_city')
    page = data.get('help_page', 0)
    events = volunteer_data['help_data'].get(city, [])
    if not events:
        await message.answer("Нет событий для этого города.", reply_markup=main_menu_kb)
        await state.clear()
        return
    if message.text == "◀️":
        page = (page - 1) % len(events)
    elif message.text == "▶️":
        page = (page + 1) % len(events)
    elif message.text == "🔙Назад":
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
        await state.clear()
        return
    await state.update_data(help_page=page)
    await show_help_event(message, state)

# --- Глобальный обработчик '🔙Назад' для любого состояния FSM ---
async def fsm_back_handler(message: Message, state: FSMContext):
    await message.answer("Главное меню:", reply_markup=main_menu_kb)
    await state.clear()

async def cmd_start(message: Message):
    await message.answer("Добро пожаловать! Выберите кнопку ниже:", reply_markup=main_menu_kb)

# Новый обработчик выбора города для вступления
async def entry_city_handler(message: Message, state: FSMContext):
    if message.text in volunteer_data['volunteer_entry']:
        info = volunteer_data['volunteer_entry'][message.text]
        await message.answer(f"Адрес для вступления в городе {message.text}:\n{info}", reply_markup=main_menu_kb)
        await state.clear()
    elif message.text == "🔙Назад":
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
        await state.clear()
    else:
        await message.answer("Пожалуйста, выберите город из списка.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await create_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(cmd_start, F.text == "/start")
    dp.message.register(main_menu_handler, F.text, default_state)

    dp.message.register(cmd_check, Command(commands=["check"]))
    dp.message.register(cmd_add_work, Command(commands=["add_work"]))
    dp.message.register(cmd_remove_work, Command(commands=["remove_work"]))
    dp.message.register(cmd_send_announcement, Command(commands=["send_announcement"]))

    dp.message.register(help_city, HelpStates.city)
    dp.message.register(help_page_nav, HelpStates.page)
    dp.message.register(fsm_back_handler, any_state, F.text == "🔙Назад")

    dp.message.register(entry_city_handler, StateFilter("entry_city"))

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 