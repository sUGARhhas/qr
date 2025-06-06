from aiogram import Router, F, types, Bot
from aiogram.filters import CommandStart, Command
from create_bot import bot
from keyboards import start_client_kb, settings_client_kb, category_client_kb
from data_base import sqlite_db
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from functools import partial

router = Router()

scheduler = AsyncIOScheduler()

async def cmd_learn_word(user_id: int, bot_instance: Bot):
    user_category = sqlite_db.get_user_category(user_id)
    word_data = sqlite_db.get_next_word(user_category)
    if word_data:
        word, transcription, description, example = word_data
        await bot_instance.send_message(user_id, f'🎲 | Английское слово: *{word}*\n'
                                        f'\n🛠 | Транскрипция: \\[{transcription}\\]\n'
                                        f'\n💎 | Перевод: \n{description}\n'
                                        f'\n📜 | Примеры использования: \n\n{example}\n'
                                        f'\n*🔥 Следующее слово Вы получите в это же время следующего дня!*',
                               parse_mode='Markdown')

        sqlite_db.increase_category_count(user_id, user_category)

    else:
        await bot_instance.send_message(user_id, 'Извините, нет новых слов для учебы в данной категории.')

async def scheduled_learn_word(user_id: int, bot_instance: Bot):
    await cmd_learn_word(user_id, bot_instance)

def start_scheduler(user_id: int, bot_instance: Bot):
    job_id = f'learn_word_job_{user_id}'

    if not scheduler.get_job(job_id):
        if not scheduler.running:
            scheduler.add_job(
                partial(scheduled_learn_word, user_id, bot_instance),
                IntervalTrigger(hours=1),
                id=job_id,
                name=f'Запуск cmd_learn_word каждые 1 час для пользователя {user_id}',
                replace_existing=True,
            )
            scheduler.start()
        else:
            scheduler.add_job(
                partial(scheduled_learn_word, user_id, bot_instance),
                IntervalTrigger(hours=1),
                id=job_id,
                name=f'Запуск cmd_learn_word каждые 1 час для пользователя {user_id}',
                replace_existing=True,
            )


@router.message(CommandStart())
async def cmd_start(message : types.Message):
    await bot.send_message(message.from_user.id, f'Добро пожаловать, *{message.from_user.first_name}*, '
                                                 'в EnglishBot для изучения английских слов.'
                                                 '\nЕжедневно Вы будете получать английские слова из выбраннай Вами '
                                                 'категории.\n'
                                                 '\nДля изменения категории зайдите в *⚙️ Настройки*\n',
                           parse_mode='Markdown', reply_markup=start_client_kb)

    username = message.from_user.username
    ud = message.from_user.id
    sqlite_db.add_user(username, ud)
    start_scheduler(message.from_user.id, bot)

@router.message(F.text == '🎲 Получить дополнительное слово')
async def cmd_word(message: types.Message):
    user_category = sqlite_db.get_user_category(message.from_user.id)
    word_data = sqlite_db.get_next_word(user_category)
    if word_data:
        word, transcription, description, example = word_data
        await bot.send_message(message.from_user.id, f'🎲 | Английское слово: *{word}*\n'
                                        f'\n🛠 | Транскрипция: \\[{transcription}\\]\n'
                                        f'\n💎 | Перевод: \n{description}\n'
                                        f'\n📜 | Примеры использования: \n\n{example}\n'
                                        f'\n*🔥 Следующее слово Вы получите в это же время следующего дня!*',
                               parse_mode='Markdown')

        sqlite_db.increase_category_count(message.from_user.id, user_category)

    else:
        await bot.send_message(message.from_user.id, 'Извините, нет новых слов для учебы в данной категории.')

@router.message(Command(commands=['hidekb']))
async def cmd_hide_kb(message : types.Message):
    await bot.send_message(message.from_user.id, 'Для отображения клавиатуры введите команду */start*',
                           parse_mode='Markdown',
                           reply_markup=types.ReplyKeyboardRemove())

@router.message(F.text == '⚙️ Настройки')
async def cmd_setting(message : types.Message):
    await bot.send_message(message.from_user.id, 'Вы перешли в раздел *⚙️ Настройки*', parse_mode='Markdown',
                           reply_markup=settings_client_kb)

@router.message(F.text == '◀️ Назад')
async def cmd_back(message : types.Message):
    await bot.send_message(message.from_user.id, 'Вы перешли в раздел *Главное меню*', parse_mode='Markdown',
                           reply_markup=start_client_kb)

@router.message(F.text == '⚙️ Категория слов')
async def cmd_category(message : types.Message):
    await bot.send_message(message.from_user.id, 'Пожалуйста, выберите новую категорию слов, которую хотите выучить.',
                           reply_markup=category_client_kb)

@router.message(F.text == '🌍 Путешествие')
async def cmd_category_1(message: types.Message):
    new_category = 'category_1'
    ud = message.from_user.id
    sqlite_db.update_user_category(ud, new_category)

    await bot.send_message(message.from_user.id, f'{message.from_user.first_name}, '
                                                 'категория успешно изменена на: *🌍 Путешествие*',
                           parse_mode='Markdown')

@router.message(F.text == '🗽 Государство и общество')
async def cmd_category_2(message: types.Message):
    new_category = 'category_2'
    ud = message.from_user.id
    sqlite_db.update_user_category(ud, new_category)

    await bot.send_message(message.from_user.id, f'{message.from_user.first_name}, '
                                                 'категория успешно изменена на: *🗽 Государство и общество*',
                           parse_mode='Markdown')

@router.message(F.text == '🏯 Дом')
async def cmd_category_3(message: types.Message):
    new_category = 'category_3'
    ud = message.from_user.id
    sqlite_db.update_user_category(ud, new_category)

    await bot.send_message(message.from_user.id, f'{message.from_user.first_name}, '
                                                 'категория успешно изменена на: *🏯 Дом*', parse_mode='Markdown')
