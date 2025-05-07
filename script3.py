from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Функция для обработки команды /start или /id
async def start_or_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user  # Получаем информацию о пользователе
    user_info = (
        f"Ваш ID: {user.id}\n"
        f"Ваш тег: @{user.username}\n"
        f"Ваше имя: {user.first_name}"
    )
    await update.message.reply_text(user_info)

# Функция для обработки команды /teg
async def teg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем аргументы после команды /teg
    args = context.args
    if not args:
        await update.message.reply_text("Использование: /teg @username")
        return

    username = args[0].lstrip('@')  # Убираем символ '@' из тега
    try:
        # Ищем пользователя по тегу
        user = await context.bot.get_chat(username)
        user_info = (
            f"ID: {user.id}\n"
            f"Тег: @{user.username}\n"
            f"Имя: {user.first_name}"
        )
        await update.message.reply_text(user_info)
    except Exception as e:
        await update.message.reply_text(f"Пользователь с тегом @{username} не найден.")

# Основная функция для запуска бота
def main():
    # Вставьте сюда токен вашего бота
    TOKEN = "7698109317:AAG078X5h3r1VldVFLa1-DMeS6JMGRR8q0U"

    # Создаем приложение
    application = ApplicationBuilder().token(TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_or_id))
    application.add_handler(CommandHandler("id", start_or_id))
    application.add_handler(CommandHandler("teg", teg))

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()