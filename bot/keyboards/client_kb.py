from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

#Старт бота
NewWordButton = KeyboardButton(text='🎲 Получить дополнительное слово')
SettingsButton = KeyboardButton(text='⚙️ Настройки')

start_client_kb = ReplyKeyboardMarkup(
    keyboard=[
        [SettingsButton, NewWordButton]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

#Настройки бота
CategoryButton = KeyboardButton(text='⚙️ Категория слов')
Back = KeyboardButton(text='◀️ Назад')

settings_client_kb = ReplyKeyboardMarkup(
    keyboard=[
        [CategoryButton],
        [Back]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

#Категории бота
CategoryButton_1 = KeyboardButton(text='🌍 Путешествие')
CategoryButton_2 = KeyboardButton(text='🗽 Государство и общество')
CategoryButton_3 = KeyboardButton(text='🏯 Дом')

category_client_kb = ReplyKeyboardMarkup(
    keyboard=[
        [CategoryButton_1],
        [CategoryButton_2],
        [CategoryButton_3],
        [Back]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)
