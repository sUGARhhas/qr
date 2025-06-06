import asyncio
from aiogram import Bot
from handlers import client_router, admin_router
from create_bot import dp, bot as main_bot_instance
from data_base import sqlite_db

async def on_startup(bot: Bot):
    print('Бот вышел в онлайн')
    sqlite_db.sql_start()

async def on_shutdown(bot: Bot):
    print('Бот уходит в офлайн')

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.include_router(client_router)
    dp.include_router(admin_router)

    await dp.start_polling(main_bot_instance)

if __name__ == '__main__':
    asyncio.run(main())
