import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ContentType, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from io import BytesIO
from aiohttp import MultipartWriter
import ssl
from PIL import Image
import io
import time

# Токен бота
BOT_TOKEN = '7363048352:AAFyJ2IFnj_SMMR9Xd2sOOzIiEiRu9mkqtQ'

# Ключ API SauceNao
SAUCENAO_API_KEY = '643c9778727fabe66a1098b49808ab6efc5c8cbe'

# URL для запросов к SauceNao
SAUCENAO_API_URL = 'https://saucenao.com/search.php'

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Создаём SSL-контекст, который игнорирует проверку сертификатов
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def send_search_links(message: Message, file_url: str):
    """Функция для отправки сообщения с кнопками поиска в Google и Яндекс\n\nНаиболее точный результат находится в Яндекс браузере"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Искать в Google", 
                               url=f"https://www.google.com/searchbyimage?image_url={file_url}&client=app"),
            InlineKeyboardButton(text="🔍 Искать в Яндекс", 
                               url=f"https://yandex.com/images/search?url={file_url}&rpt=imageview")
        ]
    ])
    await message.answer(
        "🤔 Результат не очень точный. Вы можете попробовать найти изображение в Google или Яндекс:",
        reply_markup=keyboard
    )

# Обработчик команды /start
@dp.message(CommandStart())
async def send_welcome(message: Message):
    welcome_text = (
        "🌸 *Добро пожаловать в Anime Finder Bot!* 🌸\n\n"
        "Отправь мне фото или скриншот из аниме, и я найду название, серию, время и другую информацию! 🎬\n"
        "Используй /help, чтобы узнать доступные команды.\n"
        "Погрузись в мир аниме! ✨"
    )
    await message.answer(welcome_text, parse_mode=ParseMode.MARKDOWN)

# Обработчик команды /help
@dp.message(Command("help"))
async def send_help(message: Message):
    help_text = (
        "📖 *Помощь по Anime Finder Bot* 📖\n\n"
        "🔹 Отправь фото или скриншот из аниме, чтобы получить информацию (название, серия, время).\n"
        "🔹 Команды:\n"
        "  /start — начать работу с ботом\n"
        "  /help — показать это сообщение\n\n"
        "💡 Просто отправь изображение, и я сделаю всё остальное!"
    )
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)

async def search_saucenao(image_data: bytes):
    params = {
        'api_key': SAUCENAO_API_KEY,
        'output_type': 2,  # JSON-формат
        'numres': 1,  # Один лучший результат
    }
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        try:
            with MultipartWriter('form-data') as mp:
                part = mp.append(image_data, {'Content-Type': 'image/jpeg'})
                part.set_content_disposition('form-data', name='file', filename='image.jpg')
                async with session.post(SAUCENAO_API_URL, params=params, data=mp) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()
                    return data
        except Exception:
            return None

async def convert_to_supported_format(image_data: bytes) -> bytes:
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            if img.format.lower() not in ['jpeg', 'jpg', 'png', 'bmp', 'webp']:
                output = io.BytesIO()
                img.convert('RGB').save(output, format='JPEG')
                return output.getvalue()
            return image_data
    except Exception:
        raise

@dp.message(lambda message: message.content_type == ContentType.PHOTO)
async def handle_photo(message: Message):
    try:
        photo = message.photo[-1]  # Берём фото наилучшего качества
        file_info = await bot.get_file(photo.file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            async with session.get(file_url) as response:
                if response.status != 200:
                    await send_search_links(message, file_url)
                    return
                image_data = await response.read()

        # Конвертация изображения в поддерживаемый формат
        try:
            image_data = await convert_to_supported_format(image_data)
        except Exception:
            await send_search_links(message, file_url)
            return

        result = await search_saucenao(image_data)
        if not result or 'results' not in result or not result['results']:
            await send_search_links(message, file_url)
            return

        best_result = result['results'][0]
        header = best_result['header']
        data = best_result['data']
        similarity = float(header.get('similarity', 0))

        if similarity < 70:
            await send_search_links(message, file_url)
            return

        # Формирование ответа с информацией об аниме
        title = data.get('source', 'Название не указано')
        episode = data.get('part', 'Не указана')
        timestamp = data.get('est_time', 'Не указано')
        source_url = data.get('ext_urls', ['Отсутствует'])[0]

        response_text = (
            "🎉 *Результат найден!* 🎉\n\n"
            f"📺 *Название*: {title}\n"
            f"📼 *Серия*: {episode}\n"
            f"⏰ *Время*: {timestamp}\n"
            f"📊 *Сходство*: {similarity:.2f}%\n\n"
            "💡 Хочешь узнать больше? Отправь ещё одно изображение!"
        )

        await message.answer(response_text, parse_mode=ParseMode.MARKDOWN)

    except Exception:
        try:
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{message.photo[-1].file_id}"
            await send_search_links(message, file_url)
        except Exception:
            await message.answer("🤔 Не удалось обработать изображение. Попробуйте другое фото.")

# Обработчик неизвестных сообщений
@dp.message()
async def unknown_message(message: Message):
    await message.answer(
        "🤷‍♂️ Я понимаю только фотографии и команды /start, /help. Отправь изображение из аниме!",
        parse_mode=ParseMode.MARKDOWN
    )

# Запуск бота
async def main():
    start_time = time.time()
    await dp.start_polling(bot)
    end_time = time.time()

if __name__ == '__main__':
    asyncio.run(main())