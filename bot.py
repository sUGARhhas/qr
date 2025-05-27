from telethon import TelegramClient, events
import asyncio
from telethon.tl.types import PeerChannel

# Ваши данные
api_id = '23743591'
api_hash = 'aa03afc85a1d893ab2a062837f4e7d37'
bot_token = '7503623431:AAHDI_4vFTnEFlL_BKjWZUTGjTO_qf6BQTs'

# Создаем клиента
client = TelegramClient('forwarder_bot', api_id, api_hash)

# Список каналов-источников
SOURCE_CHANNELS = [-1002260116950, -1002590539144]

# Список ID чатов, куда пересылать сообщения (мегагруппы обрабатываем как каналы)
TARGET_CHATS = [PeerChannel(2692317476)]  # Указываем чат как PeerChannel

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    """Обрабатываем новые сообщения из указанных каналов"""
    for chat in TARGET_CHATS:
        try:
            # Пересылаем сообщение
            await client.forward_messages(chat, event.message)
            print(f"Сообщение успешно переслано в чат {chat.channel_id}")
        except Exception as e:
            print(f"Ошибка при пересылке в чат {chat.channel_id}: {e}")

async def main():
    """Главная функция для запуска бота"""
    await client.start(bot_token=bot_token)
    print("Бот запущен и готов к работе!")
    await client.run_until_disconnected()

# Запускаем бота
if __name__ == '__main__':
    asyncio.run(main())