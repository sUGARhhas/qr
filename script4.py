from telethon import TelegramClient, events
import asyncio

# Ваши данные (замените на новый токен, который вы предоставите)
api_id = '23743591'
api_hash = 'aa03afc85a1d893ab2a062837f4e7d37'
bot_token = '7340013831:AAG7vFpfencCmKNRBxj1QTu_plvm02fqCII'  # Замените на новый токен, который вы предоставите

# Создаем клиента с уникальным именем сессии
client = TelegramClient('bot4', api_id, api_hash)

@client.on(events.NewMessage())
async def handler(event):
    """Обрабатываем новые сообщения"""
    # Проверяем, является ли сообщение пересланным
    if event.message.fwd_from:
        try:
            # Проверяем, переслан ли пост из канала
            if event.message.fwd_from.from_id and hasattr(event.message.fwd_from.from_id, 'channel_id'):
                channel_id = event.message.fwd_from.from_id.channel_id
                # Получаем информацию о канале
                channel = await client.get_entity(channel_id)
                channel_title = channel.title
                # Формируем красивое сообщение с использованием HTML
                response = (
                    "<b>📢 Информация о канале</b>\n"
                    f"<b>Название:</b> {channel_title}\n"
                    f"<b>ID канала:</b> <code>-100{channel_id}</code>\n"
                    "<i>Перешлите еще один пост, чтобы узнать информацию о другом канале!</i>"
                )
                # Отправляем ответ с HTML-разметкой
                await event.reply(response, parse_mode='html')
            else:
                await event.reply("Это сообщение не из канала. Перешлите пост из канала, чтобы узнать его ID и название.")
        except Exception as e:
            await event.reply(f"Произошла ошибка: {e}")
    else:
        await event.reply(
            "<b>👋 Привет!</b>\n"
            "Я бот, который может показать информацию о канале. "
            "Просто перешлите мне любой пост из канала, и я покажу его название и ID.",
            parse_mode='html'
        )

async def main():
    """Главная функция для запуска бота"""
    await client.start(bot_token=bot_token)
    print("Бот запущен и готов к работе!")
    await client.run_until_disconnected()

# Запускаем бота
if __name__ == '__main__':
    asyncio.run(main())