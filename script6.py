from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler
import requests
from bs4 import BeautifulSoup
import re
import time

TOKEN = "8046831301:AAFZTumxzU3mmJ-AMr_hciH7p7rWzE671QQ"
API_TIMEOUT = 15  # Увеличено до 15 секунд
API_MAX_RETRIES = 3  # Увеличено до 3 попыток

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>📜 Добро пожаловать!</b>\n"
        "Я бот, который ищет источники цитат. Отправь мне цитату, и я найду автора и книгу! 📚\n"
        "Например: <i>\"Жизнь — это то, что случается\"</i>",
        parse_mode="HTML"
    )

def search_google_books(query, timeout=API_TIMEOUT):
    """Поиск цитат в Google Books API"""
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": f"\"{query}\""}  # Убрано maxResults для получения всех результатов
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        results = []
        if "items" in data:
            for item in data["items"]:
                volume_info = item.get("volumeInfo", {})
                results.append({
                    "text": query,
                    "author": volume_info.get("authors", ["Неизвестно"])[0],
                    "source": volume_info.get("title", "Неизвестно")
                })
        return results
    except Exception:
        return []

def search_wikiquote_ru(query, timeout=API_TIMEOUT):
    """Поиск цитат в Викицитатнике"""
    search_url = f"https://ru.wikiquote.org/w/index.php?search={query}&title=Служебная:Поиск&fulltext=1&ns0=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(search_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = soup.select('.mw-search-result-heading a')
        if not search_results:
            return []
        page_url = "https://ru.wikiquote.org" + search_results[0]['href']
        page_response = requests.get(page_url, headers=headers, timeout=timeout)
        page_response.raise_for_status()
        soup = BeautifulSoup(page_response.text, 'html.parser')
        quotes = soup.select('.mw-parser-output > ul > li, .mw-parser-output > dl > dd')
        results = []
        author = search_results[0].text
        for quote in quotes:
            results.append({
                "text": quote.text.strip(),
                "author": author,
                "source": "Викицитатник"
            })
        return results
    except Exception:
        return []

def search_quotes(query):
    """Поиск цитат через API и Викицитатник"""
    is_russian = bool(re.search('[а-яА-ЯёЁ]', query))
    apis = [search_google_books, search_wikiquote_ru] if is_russian else [search_google_books]
    all_results = []

    for api_func in apis:
        for attempt in range(API_MAX_RETRIES):
            try:
                timeout = API_TIMEOUT + (attempt * 5)  # 15с, 20с, 25с
                results = api_func(query, timeout=timeout)
                if results:
                    all_results.extend(results)
                break
            except Exception:
                if attempt < API_MAX_RETRIES - 1:
                    time.sleep(2)

    return all_results

def create_result_message(result, index, total):
    """Создаёт сообщение для одного результата с указанием номера и общего количества"""
    return (
        f"<b>Результат {index + 1} из {total}</b>\n"
        f"<b>Цитата:</b> <i>\"{result['text']}\"</i>\n"
        f"<b>Автор:</b> {result['author']}\n"
        f"<b>Источник:</b> {result['source']}"
    )

def create_keyboard(index, total):
    """Создаёт клавиатуру с кнопками 'Назад' и 'Вперёд'"""
    buttons = []
    if index > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_{index}"))
    if index < total - 1:
        buttons.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"next_{index}"))
    return InlineKeyboardMarkup([buttons]) if buttons else None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.message.text.strip()
        
        # Фильтр для некорректных запросов
        if "Начало поиска цитаты" in query:
            await update.message.reply_text(
                "<b>⚠️ Ошибка</b>\nПохоже, вы отправили текст из логов. Введите настоящую цитату.",
                parse_mode="HTML"
            )
            return
        
        if len(query) < 3:
            await update.message.reply_text(
                "<b>⚠️ Ошибка</b>\nЗапрос слишком короткий. Введите минимум 3 символа.",
                parse_mode="HTML"
            )
            return
        
        await update.message.reply_text(
            "<i>🔍 Поиск источника цитаты...</i>",
            parse_mode="HTML"
        )
        
        results = search_quotes(query)
        if not results:
            await update.message.reply_text(
                "<b>😔 Источник не найден</b>\n"
                "Возможно, цитата слишком специфична или возникли проблемы с сетью.\n"
                "Попробуйте другую фразу или сократите запрос.\n"
                "Например: <i>\"Смысл жизни\"</i>",
                parse_mode="HTML"
            )
            return
        
        # Сохраняем результаты и начинаем с первого
        context.user_data['results'] = results
        context.user_data['current_index'] = 0
        
        # Показываем первый результат с кнопками
        message = create_result_message(results[0], 0, len(results))
        keyboard = create_keyboard(0, len(results))
        await update.message.reply_text(message, parse_mode="HTML", reply_markup=keyboard)
    
    except Exception as e:
        await update.message.reply_text(
            "<b>❌ Ошибка</b>\nНе удалось обработать запрос из-за сетевых проблем или внутренней ошибки. Попробуйте позже.",
            parse_mode="HTML"
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки 'Назад' и 'Вперёд'"""
    query = update.callback_query
    await query.answer()
    
    results = context.user_data.get('results', [])
    if not results:
        await query.message.reply_text(
            "<b>❌ Ошибка</b>\nРезультаты не найдены. Попробуйте новый запрос.",
            parse_mode="HTML"
        )
        return
    
    current_index = context.user_data.get('current_index', 0)
    callback_data = query.data
    
    # Обновляем индекс в зависимости от нажатой кнопки
    if callback_data.startswith("prev_"):
        current_index -= 1
    elif callback_data.startswith("next_"):
        current_index += 1
    
    context.user_data['current_index'] = current_index
    
    # Обновляем сообщение
    message = create_result_message(results[current_index], current_index, len(results))
    keyboard = create_keyboard(current_index, len(results))
    await query.message.edit_text(message, parse_mode="HTML", reply_markup=keyboard)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))

app.run_polling()