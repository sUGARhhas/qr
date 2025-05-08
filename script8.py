import asyncio
from typing import Dict
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from mimesis.enums import Gender
from mimesis import Person
from datetime import datetime
import random
import re
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token="7738403331:AAHICjtxw89JhA6Dra86Mg9XfGtLZvRSBrE")  # Замени на свой токен от @BotFather
dp = Dispatcher()

def generate_fake_user(locale: str = "ru", gender: Gender = Gender.MALE) -> Dict[str, str]:
    """
    Создаёт фейковые данные пользователя на основе локали и пола.

    Args:
        locale (str): Локаль для генерации данных (например, 'ru', 'en', 'es'). По умолчанию 'ru'.
        gender (Gender): Пол пользователя (Gender.MALE или Gender.FEMALE). По умолчанию Gender.MALE.

    Returns:
        Dict[str, str]: Словарь с данными: имя, рост, телефон, профессия, email, дата рождения.

    Raises:
        ValueError: Если указана неподдерживаемая локаль или другая ошибка.
    """
    try:
        # Инициализируем генератор данных с указанной локалью
        person = Person(locale)

        # Генерируем дату рождения вручную (18–80 лет)
        current_year = datetime.now().year
        min_year = current_year - 60
        max_year = current_year - 18
        birth_year = random.randint(min_year, max_year)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)  # Упрощаем для всех месяцев
        birth_date = datetime(birth_year, birth_month, birth_day)

        # Генерируем номер телефона и форматируем его
        raw_phone = person.telephone()
        # Заменяем дефисы на пробелы и обеспечиваем формат +7 (код) номер
        formatted_phone = re.sub(r'[-]', ' ', raw_phone)
        formatted_phone = re.sub(r'\s+', ' ', formatted_phone)  # Убираем двойные пробелы

        user_data = {
            "имя": person.full_name(gender=gender),
            "рост": f"{person.height()} метров",
            "телефон": formatted_phone,
            "профессия": person.occupation(),
            "email": person.email(),
            "дата_рождения": birth_date.strftime("%d.%m.%Y"),
        }

        return user_data

    except Exception as e:
        raise ValueError(f"Ошибка при генерации данных: {str(e)}")

def format_user_data(user: Dict[str, str]) -> str:
    """
    Форматирует данные пользователя для отправки в Telegram.

    Args:
        user (Dict[str, str]): Словарь с данными пользователя.

    Returns:
        str: Отформатированная строка с данными.
    """
    return (
        "=== Фейковый пользователь ===\n"
        f"Имя: {user['имя']}\n"
        f"Рост: {user['рост']}\n"
        f"Телефон: {user['телефон']}\n"
        f"Профессия: {user['профессия']}\n"
        f"Email: {user['email']}\n"
        f"Дата рождения: {user['дата_рождения']}\n"
        "=========================="
    )

# Создаём инлайн-клавиатуру с кнопками
def get_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Мужчина", callback_data="male"),
            InlineKeyboardButton(text="Женщина", callback_data="female")
        ]
    ])
    return keyboard

# Обработчик любого текстового сообщения
@dp.message()
async def handle_message(message: Message):
    await message.answer(
        "Выберите пол для генерации фейкового пользователя:",
        reply_markup=get_keyboard()
    )

# Обработчик нажатий на кнопки
@dp.callback_query(F.data.in_({"male", "female"}))
async def handle_callback(query: CallbackQuery):
    gender = Gender.MALE if query.data == "male" else Gender.FEMALE
    try:
        user_data = generate_fake_user(locale="ru", gender=gender)
        formatted_data = format_user_data(user_data)
        await query.message.answer(formatted_data, reply_markup=get_keyboard())
        await query.answer()  # Подтверждаем обработку callback
    except ValueError as e:
        await query.message.answer(f"Ошибка: {str(e)}", reply_markup=get_keyboard())
        await query.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())