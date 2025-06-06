from aiogram import Router, types, F
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from data_base import sqlite_db

router = Router()

id_admin = 6116796522

class AddWordStates(StatesGroup):
    waiting_for_word = State()
    waiting_for_transcription = State()
    waiting_for_description = State()
    waiting_for_example = State()
    waiting_for_category = State()

class AdminFilter(Filter):
    def __init__(self, admin_id: int):
        self.admin_id = admin_id

    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id == self.admin_id

# Восстанавливаем AdminFilter в декораторе
@router.message(Command(commands=['addword']), AdminFilter(admin_id=id_admin))
async def add_word_start(message: types.Message, state: FSMContext):
    # Убираем временную проверку ID администратора из функции
    await message.answer("Введите слово:")
    await state.set_state(AddWordStates.waiting_for_word)

@router.message(AddWordStates.waiting_for_word, F.text)
async def add_word_enter_word(message: types.Message, state: FSMContext):
    word = message.text
    await state.update_data(word=word)
    await message.answer("Введите транскрипцию:")
    await state.set_state(AddWordStates.waiting_for_transcription)

@router.message(AddWordStates.waiting_for_transcription, F.text)
async def add_word_enter_transcription(message: types.Message, state: FSMContext):
    transcription = message.text
    await state.update_data(transcription=transcription)
    await message.answer("Введите описание:")
    await state.set_state(AddWordStates.waiting_for_description)

@router.message(AddWordStates.waiting_for_description, F.text)
async def add_word_enter_description(message: types.Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    await message.answer("Введите пример использования:")
    await state.set_state(AddWordStates.waiting_for_example)

@router.message(AddWordStates.waiting_for_example, F.text)
async def add_word_enter_example(message: types.Message, state: FSMContext):
    example = message.text
    await state.update_data(example=example)
    await message.answer("Введите категорию слова (category_1, category_2, category_3):")
    await state.set_state(AddWordStates.waiting_for_category)

@router.message(AddWordStates.waiting_for_category, F.text.in_({'category_1', 'category_2', 'category_3'}))
async def add_word_enter_category(message: types.Message, state: FSMContext):
    category = message.text

    data = await state.get_data()
    word = data['word']
    transcription = data['transcription']
    description = data['description']
    example = data['example']

    sqlite_db.sql_add_command(word, transcription, description, example, category)

    await message.answer(f'Слово "{word}" успешно добавлено в базу данных.\nКатегория {category}')

    await state.clear()

@router.message(AddWordStates.waiting_for_category, F.text)
async def add_word_invalid_category(message: types.Message, state: FSMContext):
    await message.answer("Неверная категория. Пожалуйста, введите одну из: category_1, category_2, category_3.")
