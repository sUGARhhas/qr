import os
import asyncio
from difflib import SequenceMatcher
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import lyricsgenius
import re

# Конфигурация
BOT_TOKEN = "7941650366:AAEo6GsSZ_Hf9rrVllPywyMVY1Bq59OQDc0"  # Вставьте ваш токен бота
GENIUS_API_KEY = 'CaRmec5MDGN8v87xC0fGf-TfE7QxvihGK8-UuC1phjkbuCqHQCdd--0lemesGbFp'
MAX_RETRIES = 3  # Максимальное количество попыток поиска

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Инициализация Genius API
try:
    genius = lyricsgenius.Genius(
        GENIUS_API_KEY,
        verbose=False,
        remove_section_headers=True,
        skip_non_songs=True,
        timeout=30,
        retries=3
    )
except Exception as e:
    print(f"Критическая ошибка инициализации Genius: {e}")
    genius = None

def normalize_text(text: str) -> str:
    """Нормализация текста: удаление специальных символов и приведение к нижнему регистру"""
    text = re.sub(r'[^\w\s]', '', text)
    return text.lower().strip()

def similar(a: str, b: str) -> float:
    """Вычисление схожести строк от 0 до 1"""
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()

async def find_exact_match(artist: str, title: str, attempts=3) -> dict:
    """Поиск точного совпадения с проверкой качества"""
    for attempt in range(attempts):
        try:
            # Нормализуем запрос
            search_query = f"{normalize_text(artist)} {normalize_text(title)}"
            search_results = genius.search_songs(search_query)
            
            if not search_results or not search_results.get('hits'):
                print(f"Попытка {attempt + 1}: Нет результатов для {search_query}")
                return None

            # Логируем результаты для отладки
            print(f"Попытка {attempt + 1}: Найдено {len(search_results['hits'])} результатов для {search_query}")

            # Ищем лучшее совпадение
            best_match = None
            best_score = 0.5  # Сниженный порог совпадения

            for hit in search_results['hits']:
                result = hit['result']
                current_artist = result['primary_artist']['name']
                current_title = result['title']
                
                # Комбинированная оценка совпадения
                score = (similar(artist, current_artist) * 0.6 + 
                         similar(title, current_title) * 0.4)
                
                print(f"Проверяем: {current_artist} - {current_title} (score: {score:.2f})")
                
                if score > best_score:
                    best_score = score
                    best_match = result

            if best_match:
                # Дополнительная проверка - получаем полную песню
                full_song = genius.search_song(
                    title=best_match['title'],
                    artist=best_match['primary_artist']['name']
                )
                if full_song and full_song.lyrics:
                    return {
                        'id': best_match['id'],
                        'title': best_match['title'],
                        'artist': best_match['primary_artist']['name'],
                        'url': best_match['url'],
                        'lyrics': full_song.lyrics
                    }
                else:
                    print(f"Не удалось получить текст для {best_match['title']} - {best_match['primary_artist']['name']}")

        except Exception as e:
            print(f"Попытка {attempt + 1} не удалась: {e}")
            if attempt == attempts - 1:
                return None
            await asyncio.sleep(1)
    
    return None

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("""
<b>🎵 Точный поиск текстов песен 🎵</b>

Отправьте запрос в формате:
<code>Исполнитель - Название песни</code>

Примеры:
<code>Грибы - Тает лёд</code>
<code>Кино - Группа крови</code>

Бот использует улучшенный алгоритм поиска для максимально точных результатов!
""")

@dp.message(F.text)
async def handle_search(message: types.Message):
    if not genius:
        await message.answer("⚠️ Сервис временно недоступен. Приносим извинения!")
        return

    try:
        if '-' not in message.text:
            await message.answer("❌ Используйте формат: <code>Исполнитель - Название</code>")
            return

        artist, title = map(str.strip, message.text.split('-', 1))
        if not artist or not title:
            await message.answer("❌ Укажите и исполнителя, и название!")
            return

        search_msg = await message.answer(f"🔍 Ищем <b>{title}</b> — <b>{artist}</b>...")

        # Поиск с несколькими попытками
        song_data = None
        for attempt in range(MAX_RETRIES):
            song_data = await find_exact_match(artist, title)
            if song_data:
                break
            await asyncio.sleep(1)

        if not song_data:
            await search_msg.edit_text(f"""
❌ Точное совпадение не найдено: <b>{artist} - {title}</b>

Советы:
1. Проверьте правильность написания
2. Попробуйте оригинальное название
3. Упростите сложные названия
""")
            return

        # Форматирование текста
        lyrics = song_data['lyrics']
        if len(lyrics) > 4000:
            lyrics = lyrics[:4000] + "\n\n[...текст сокращен...]"

        response = f"""
🎤 <b>{song_data['artist']}</b>
🎵 <b>{song_data['title']}</b>

{lyrics}

<i>Источник: Genius.com • ID: {song_data['id']}</i>
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="ℹ️ Подробнее", callback_data=f"info_{song_data['id']}"),
                InlineKeyboardButton(text="🌐 Открыть на Genius", url=song_data['url'])
            ]
        ])

        await search_msg.edit_text(response, reply_markup=keyboard)

    except Exception as e:
        print(f"Ошибка: {e}")
        await message.answer("⚠️ Произошла критическая ошибка. Попробуйте позже.")

@dp.callback_query(F.data.startswith("info_"))
async def show_song_info(callback: types.CallbackQuery):
    try:
        song_id = callback.data.split("_")[1]
        song_info = genius.song(song_id)['song']

        info_text = f"""
📌 <b>Детальная информация</b>

🎤 <b>Исполнитель:</b> {song_info['primary_artist']['name']}
🎵 <b>Название:</b> {song_info['title']}
📀 <b>Альбом:</b> {song_info.get('album', {}).get('name', 'не указан')}
📅 <b>Дата выхода:</b> {song_info.get('release_date', 'неизвестна')}
👀 <b>Просмотры:</b> {song_info.get('stats', {}).get('pageviews', 'нет данных')}

🔗 <a href="{song_info['url']}">Ссылка на Genius</a>
"""
        await callback.message.answer(info_text)
        await callback.answer()

    except Exception as e:
        print(f"Ошибка информации: {e}")
        await callback.answer("❌ Не удалось загрузить информацию")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())