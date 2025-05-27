import os
import logging
from collections import defaultdict
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ID администратора
ADMIN_ID = 6356238822

# Получаем путь к текущей директории
current_dir = os.path.dirname(os.path.abspath(__file__))

# Создаем путь к файлу базы данных
db_path = os.path.join(current_dir, 'users.db')

# Подключение к базе данных SQLite
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# Логируем путь к базе данных
logger.info(f"База данных создана/открыта: {db_path}")

# Проверяем структуру таблицы и обновляем её при необходимости
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    is_banned INTEGER DEFAULT 0
)
''')
conn.commit()

# Логируем создание таблицы
logger.info("Таблица 'users' создана/проверена.")

# Проверяем, существует ли столбец username
cursor.execute("PRAGMA table_info(users)")
columns = [column[1] for column in cursor.fetchall()]
if 'username' not in columns:
    cursor.execute('ALTER TABLE users ADD COLUMN username TEXT')
    conn.commit()
    logger.info("Столбец 'username' добавлен в таблицу 'users'.")

# Функция для добавления пользователя в базу данных
def add_user(user_id, username):
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, is_banned) VALUES (?, ?, 0)', (user_id, username))
    conn.commit()
    logger.info(f"Пользователь добавлен: ID={user_id}, Username={username}")

# Функция для проверки, забанен ли пользователь
def is_user_banned(user_id):
    cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else False

# Функция для бана пользователя
def ban_user(user_id):
    cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    logger.info(f"Пользователь забанен: ID={user_id}")

# Функция для разбана пользователя
def unban_user(user_id):
    cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    logger.info(f"Пользователь разбанен: ID={user_id}")

# Хранилище для альбомов
media_groups = defaultdict(list)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    add_user(user_id, username)
    await update.message.reply_text("Привет! Отправь мне сообщение, фото, документ или голосовое сообщение, и я передам его администратору.")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Без имени"
    first_name = update.message.from_user.first_name or "Без имени"
    message_text = update.message.text

    # Проверяем, забанен ли пользователь
    if is_user_banned(user_id):
        await update.message.reply_text("Вы заблокированы и не можете отправлять сообщения.")
        return

    # Формируем сообщение для администратора
    admin_message = (
        f"📩 Новое сообщение:\n"
        f"👤 Отправитель: {first_name} (@{username})\n"
        f"🆔 ID: {user_id}\n"
        f"💬 Текст сообщения:\n{message_text}"
    )

    # Пересылаем сообщение администратору
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

    # Ответ пользователю
    await update.message.reply_text("Ваше сообщение отправлено администратору.")

# Обработчик медиа (фото, видео, альбомы)
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Без имени"
    first_name = update.message.from_user.first_name or "Без имени"

    # Проверяем, забанен ли пользователь
    if is_user_banned(user_id):
        await update.message.reply_text("Вы заблокированы и не можете отправлять сообщения.")
        return

    # Проверяем, является ли сообщение частью альбома
    media_group_id = update.message.media_group_id
    if media_group_id:
        # Добавляем медиа в хранилище альбомов
        media_groups[media_group_id].append(update.message)
        return

    # Если это одиночное фото
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        file_url = photo_file.file_path
        caption = update.message.caption or "Без подписи"

        admin_message = (
            f"📸 Новое фото:\n"
            f"👤 Отправитель: {first_name} (@{username})\n"
            f"🆔 ID: {user_id}\n"
            f"📝 Подпись к фото:\n{caption}\n"
            f"🔗 Ссылка на фото:\n{file_url}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_url)

    # Если это одиночное видео
    elif update.message.video:
        video_file = await update.message.video.get_file()
        file_url = video_file.file_path
        caption = update.message.caption or "Без подписи"

        admin_message = (
            f"🎬 Новое видео:\n"
            f"👤 Отправитель: {first_name} (@{username})\n"
            f"🆔 ID: {user_id}\n"
            f"📝 Подпись к видео:\n{caption}\n"
            f"🔗 Ссылка на видео:\n{file_url}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
        await context.bot.send_video(chat_id=ADMIN_ID, video=file_url)

    # Ответ пользователю
    await update.message.reply_text("Ваше медиа отправлено администратору.")

# Обработчик завершения альбома
async def process_media_group(context: ContextTypes.DEFAULT_TYPE):
    for media_group_id, messages in list(media_groups.items()):
        if not messages:
            continue

        first_message = messages[0]
        user_id = first_message.from_user.id
        username = first_message.from_user.username or "Без имени"
        first_name = first_message.from_user.first_name or "Без имени"

        # Формируем сообщение для администратора
        admin_message = (
            f"📚 Новый альбом:\n"
            f"👤 Отправитель: {first_name} (@{username})\n"
            f"🆔 ID: {user_id}\n"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

        # Отправляем все медиа из альбома
        for message in messages:
            if message.photo:
                photo_file = await message.photo[-1].get_file()
                file_url = photo_file.file_path
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_url)
            elif message.video:
                video_file = await message.video.get_file()
                file_url = video_file.file_path
                await context.bot.send_video(chat_id=ADMIN_ID, video=file_url)

        # Удаляем альбом из хранилища
        del media_groups[media_group_id]

# Обработчик документов
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Без имени"
    first_name = update.message.from_user.first_name or "Без имени"

    # Проверяем, забанен ли пользователь
    if is_user_banned(user_id):
        await update.message.reply_text("Вы заблокированы и не можете отправлять сообщения.")
        return

    # Получаем файл документа
    document_file = await update.message.document.get_file()
    file_url = document_file.file_path

    # Формируем сообщение для администратора
    admin_message = (
        f"📄 Новый документ:\n"
        f"👤 Отправитель: {first_name} (@{username})\n"
        f"🆔 ID: {user_id}\n"
        f"🔗 Ссылка на документ:\n{file_url}"
    )

    # Пересылаем сообщение администратору
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
    await context.bot.send_document(chat_id=ADMIN_ID, document=file_url)

    # Ответ пользователю
    await update.message.reply_text("Ваш документ отправлен администратору.")

# Обработчик голосовых сообщений
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Без имени"
    first_name = update.message.from_user.first_name or "Без имени"

    # Проверяем, забанен ли пользователь
    if is_user_banned(user_id):
        await update.message.reply_text("Вы заблокированы и не можете отправлять сообщения.")
        return

    # Получаем файл голосового сообщения
    voice_file = await update.message.voice.get_file()
    file_url = voice_file.file_path

    # Формируем сообщение для администратора
    admin_message = (
        f"🎤 Новое голосовое сообщение:\n"
        f"👤 Отправитель: {first_name} (@{username})\n"
        f"🆔 ID: {user_id}\n"
        f"🔗 Ссылка на файл:\n{file_url}"
    )

    # Пересылаем сообщение администратору
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
    await context.bot.send_voice(chat_id=ADMIN_ID, voice=file_url)

    # Ответ пользователю
    await update.message.reply_text("Ваше голосовое сообщение отправлено администратору.")

# Обработчик видеосообщений (кружков)
async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Без имени"
    first_name = update.message.from_user.first_name or "Без имени"

    # Проверяем, забанен ли пользователь
    if is_user_banned(user_id):
        await update.message.reply_text("Вы заблокированы и не можете отправлять сообщения.")
        return

    # Получаем файл видеосообщения
    video_note_file = await update.message.video_note.get_file()
    file_url = video_note_file.file_path

    # Формируем сообщение для администратора
    admin_message = (
        f"🎥 Новое видеосообщение (кружок):\n"
        f"👤 Отправитель: {first_name} (@{username})\n"
        f"🆔 ID: {user_id}\n"
        f"🔗 Ссылка на файл:\n{file_url}"
    )

    # Пересылаем сообщение администратору
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
    await context.bot.send_video_note(chat_id=ADMIN_ID, video_note=file_url)

    # Ответ пользователю
    await update.message.reply_text("Ваше видеосообщение (кружок) отправлено администратору.")

# Обработчик команды /ban
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        user_id_to_ban = int(context.args[0])
        ban_user(user_id_to_ban)
        await update.message.reply_text(f"Пользователь с ID {user_id_to_ban} заблокирован.")
    except (IndexError, ValueError):
        await update.message.reply_text("Использование: /ban <user_id>")

# Обработчик команды /unban
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        user_id_to_unban = int(context.args[0])
        unban_user(user_id_to_unban)
        await update.message.reply_text(f"Пользователь с ID {user_id_to_unban} разблокирован.")
    except (IndexError, ValueError):
        await update.message.reply_text("Использование: /unban <user_id>")

# Основная функция
def main():
    # Вставьте сюда токен вашего бота
    TOKEN = "7952695336:AAGbFGBsugbn7tmjIpzxUk_9NmOyeZvTlcw"

    application = ApplicationBuilder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("unban", unban))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_media))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_video_note))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()