import telebot
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageColor
import cv2
import numpy as np

API_TOKEN = '7322025078:AAHGKswq3viDIRrTAwDCPoTrxL1kESv6Xcc'

bot = telebot.TeleBot(API_TOKEN)

# Глобальная переменная для хранения последнего QR-кода
last_qr = None

# Клавиатуры
main_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add("🎨 Цветной QR", "🌈 Градиентный QR")
main_keyboard.add("🖼️ QR с логотипом", "🎨🖼️ Цвет + логотип")
main_keyboard.add("⚫ Простой QR", "🔍 Сканировать QR")
main_keyboard.add("🌈 QR с градиентным фоном", "🖼️ QR с рамкой")

cancel_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
cancel_keyboard.add("❌ Отмена")

color_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
color_keyboard.add("⚫ Черный", "🔴 Красный", "🔵 Синий", "🟢 Зеленый")
color_keyboard.add("🟣 Фиолетовый", "🟡 Жёлтый", "❌ Отмена")

background_color_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
background_color_keyboard.add("🔴 Красный", "🔵 Синий", "🟢 Зеленый")
background_color_keyboard.add("🟣 Фиолетовый", "🟡 Жёлтый", "❌ Отмена")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Привет! Я создам QR-код или отсканирую его для тебя! Выбери стиль: 🌟", reply_markup=main_keyboard)

@bot.message_handler(commands=['last'])
def send_last_qr(message):
    global last_qr
    if last_qr:
        last_qr.seek(0)
        bot.send_photo(message.chat.id, last_qr, caption="✨ Последний созданный QR-код! 🎉", reply_markup=main_keyboard)
    else:
        bot.send_message(message.chat.id, "❗ Пока нет сохраненных QR-кодов. Создай новый!", reply_markup=main_keyboard)

# Секретная команда "Россия"
@bot.message_handler(func=lambda message: message.text.lower() == "россия")
def secret_russia_qr(message):
    global last_qr
    data = "https://vt.tiktok.com/ZSrjXt2C5/"
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="green", back_color="white").convert('RGBA')
        
        gradient = Image.new("RGB", qr_img.size)
        height = qr_img.size[1]
        third = height // 3
        white_rgb = ImageColor.getrgb("white")
        blue_rgb = ImageColor.getrgb("blue")
        red_rgb = ImageColor.getrgb("red")
        
        for x in range(gradient.size[0]):
            for y in range(gradient.size[1]):
                if y < third:
                    gradient.putpixel((x, y), white_rgb)
                elif y < 2 * third:
                    gradient.putpixel((x, y), blue_rgb)
                else:
                    gradient.putpixel((x, y), red_rgb)
        
        gradient = gradient.convert('RGBA')
        final_img = gradient.copy()
        
        qr_pixels = qr_img.load()
        for x in range(qr_img.size[0]):
            for y in range(qr_img.size[1]):
                if qr_pixels[x, y] == (255, 255, 255, 255):
                    qr_pixels[x, y] = (255, 255, 255, 0)
        
        final_img.paste(qr_img, (0, 0), qr_img)
        
        bio = BytesIO()
        bio.name = 'russia_qr.png'
        final_img.convert('RGB').save(bio, 'PNG')
        bio.seek(0)
        
        last_qr = BytesIO(bio.getvalue())
        last_qr.name = 'russia_qr.png'
        
        bot.send_photo(message.chat.id, bio, caption="🇷🇺 Секретный QR-код готов! 🎉", reply_markup=main_keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}", reply_markup=cancel_keyboard)
        print(f"Ошибка в secret_russia_qr: {e}")

# Обработчик для "QR с логотипом"
@bot.message_handler(func=lambda message: message.text == "🖼️ QR с логотипом")
def add_logo_mode(message):
    bot.send_message(message.chat.id, "📝 Отправь текст или ссылку для QR-кода с логотипом:", reply_markup=cancel_keyboard)
    bot.register_next_step_handler(message, process_link_for_logo)

def process_link_for_logo(message):
    if message.text == "❌ Отмена":
        cancel_action(message)
        return
    
    data = message.text
    bot.send_message(message.chat.id, "🖼️ Теперь отправь картинку логотипа:", reply_markup=cancel_keyboard)
    bot.register_next_step_handler(message, lambda msg: add_logo_to_qr(msg, data))

def add_logo_to_qr(message, data):
    global last_qr
    if message.text == "❌ Отмена":
        cancel_action(message)
        return
    
    if message.content_type == 'photo' or message.content_type == 'document':
        try:
            if message.content_type == 'photo':
                file_info = bot.get_file(message.photo[-1].file_id)
            elif message.content_type == 'document':
                file_info = bot.get_file(message.document.file_id)

            downloaded_file = bot.download_file(file_info.file_path)
            logo = Image.open(BytesIO(downloaded_file))
            logo.thumbnail((50, 50))

            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
            qr.add_data(data)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
            qr_img.paste(logo, pos, logo if logo.mode == 'RGBA' else None)

            bio = BytesIO()
            bio.name = 'qr_with_logo.png'
            qr_img.save(bio, 'PNG')
            bio.seek(0)

            last_qr = BytesIO(bio.getvalue())
            last_qr.name = 'qr_with_logo.png'

            bot.send_photo(message.chat.id, bio, caption="✨ Твой QR-код с логотипом готов! 🎉", reply_markup=main_keyboard)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {e}. Попробуй снова!", reply_markup=cancel_keyboard)
            print(f"Ошибка при создании QR с логотипом: {e}")
    else:
        bot.send_message(message.chat.id, "📸 Отправь картинку (фото или файл):", reply_markup=cancel_keyboard)
        bot.register_next_step_handler(message, lambda msg: add_logo_to_qr(msg, data))

# Обработчик для "Цветной QR"
@bot.message_handler(func=lambda message: message.text == "🎨 Цветной QR")
def change_design_mode(message):
    bot.send_message(message.chat.id, "🌈 Выбери цвет для QR-кода:", reply_markup=color_keyboard)
    bot.register_next_step_handler(message, choose_color_for_design)

def choose_color_for_design(message):
    if message.text == "❌ Отмена":
        cancel_action(message)
        return

    color_map = {"⚫ Черный": "black", "🔴 Красный": "red", "🔵 Синий": "blue", "🟢 Зеленый": "green", 
                 "🟣 Фиолетовый": "purple", "🟡 Жёлтый": "yellow"}
    chosen_color = color_map.get(message.text)
    if not chosen_color:
        bot.send_message(message.chat.id, "❗ Выбери цвет из списка:", reply_markup=color_keyboard)
        bot.register_next_step_handler(message, choose_color_for_design)
        return

    bot.send_message(message.chat.id, f"🎨 Цвет '{message.text}' выбран! Отправь текст или ссылку:", reply_markup=cancel_keyboard)
    bot.register_next_step_handler(message, lambda msg: generate_colored_qr(msg, chosen_color))

def generate_colored_qr(message, fill_color):
    global last_qr
    if message.text == "❌ Отмена":
        cancel_action(message)
        return
    
    data = message.text
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fill_color, back_color="white")

        bio = BytesIO()
        bio.name = 'qr_colored.png'
        img.save(bio, 'PNG')
        bio.seek(0)

        last_qr = BytesIO(bio.getvalue())
        last_qr.name = 'qr_colored.png'

        bot.send_photo(message.chat.id, bio, caption=f"🌟 Твой цветной QR-код ({fill_color}) готов! 🎉", reply_markup=main_keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}", reply_markup=cancel_keyboard)
        print(f"Ошибка в generate_colored_qr: {e}")

# Обработчик для "Градиентный QR"
@bot.message_handler(func=lambda message: message.text == "🌈 Градиентный QR")
def two_colors_mode(message):
    bot.send_message(message.chat.id, "🌈 Выбери первый цвет для градиента:", reply_markup=color_keyboard)
    bot.register_next_step_handler(message, choose_primary_color)

def choose_primary_color(message):
    if message.text == "❌ Отмена":
        cancel_action(message)
        return

    color_map = {"⚫ Черный": "black", "🔴 Красный": "red", "🔵 Синий": "blue", "🟢 Зеленый": "green", 
                 "🟣 Фиолетовый": "purple", "🟡 Жёлтый": "yellow"}
    primary_color = color_map.get(message.text)
    if not primary_color:
        bot.send_message(message.chat.id, "❗ Выбери цвет из списка:", reply_markup=color_keyboard)
        bot.register_next_step_handler(message, choose_primary_color)
        return

    bot.send_message(message.chat.id, f"🌈 Первый цвет: {message.text}. Выбери второй:", reply_markup=color_keyboard)
    bot.register_next_step_handler(message, lambda msg: choose_secondary_color(msg, primary_color))

def choose_secondary_color(message, primary_color):
    if message.text == "❌ Отмена":
        cancel_action(message)
        return

    color_map = {"⚫ Черный": "black", "🔴 Красный": "red", "🔵 Синий": "blue", "🟢 Зеленый": "green", 
                 "🟣 Фиолетовый": "purple", "🟡 Жёлтый": "yellow"}
    secondary_color = color_map.get(message.text)
    if not secondary_color:
        bot.send_message(message.chat.id, "❗ Выбери цвет из списка:", reply_markup=color_keyboard)
        bot.register_next_step_handler(message, lambda msg: choose_secondary_color(msg, primary_color))
        return

    bot.send_message(message.chat.id, f"🌈 Цвета: {primary_color} → {secondary_color}. Отправь текст или ссылку:", reply_markup=cancel_keyboard)
    bot.register_next_step_handler(message, lambda msg: generate_qr_with_two_colors(msg, primary_color, secondary_color))

def generate_qr_with_two_colors(message, primary_color, secondary_color):
    global last_qr
    if message.text == "❌ Отмена":
        cancel_action(message)
        return
    
    data = message.text
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        gradient = Image.new("RGB", img.size)
        mid_point = img.size[0] // 2
        primary_rgb = ImageColor.getrgb(primary_color)
        secondary_rgb = ImageColor.getrgb(secondary_color)
        
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                pixel = img.getpixel((x, y))
                if pixel != (255, 255, 255):
                    if x < mid_point:
                        gradient.putpixel((x, y), primary_rgb)
                    else:
                        gradient.putpixel((x, y), secondary_rgb)
                else:
                    gradient.putpixel((x, y), (255, 255, 255))
        
        bio = BytesIO()
        bio.name = 'qr_gradient.png'
        gradient.save(bio, 'PNG')
        bio.seek(0)

        last_qr = BytesIO(bio.getvalue())
        last_qr.name = 'qr_gradient.png'

        bot.send_photo(message.chat.id, bio, caption=f"✨ Твой градиентный QR-код ({primary_color} → {secondary_color}) готов! 🎉", reply_markup=main_keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}", reply_markup=cancel_keyboard)
        print(f"Ошибка в generate_qr_with_two_colors: {e}")

# Обработчик для "Простой QR"
@bot.message_handler(func=lambda message: message.text == "⚫ Простой QR")
def generate_simple_qr(message):
    bot.send_message(message.chat.id, "📝 Отправь текст или ссылку для простого QR-кода:", reply_markup=cancel_keyboard)
    bot.register_next_step_handler(message, generate_qr)

def generate_qr(message):
    global last_qr
    if message.text == "❌ Отмена":
        cancel_action(message)
        return
    
    data = message.text
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        bio = BytesIO()
        bio.name = 'qr.png'
        img.save(bio, 'PNG')
        bio.seek(0)

        last_qr = BytesIO(bio.getvalue())
        last_qr.name = 'qr.png'

        bot.send_photo(message.chat.id, bio, caption="✨ Твой простой QR-код готов! 🎉", reply_markup=main_keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}", reply_markup=cancel_keyboard)
        print(f"Ошибка в generate_qr: {e}")

# Обработчик для "Цвет + логотип"
@bot.message_handler(func=lambda message: message.text == "🎨🖼️ Цвет + логотип")
def color_and_logo_mode(message):
    bot.send_message(message.chat.id, "🌈 Выбери цвет для QR-кода:", reply_markup=color_keyboard)
    bot.register_next_step_handler(message, choose_color_for_logo)

def choose_color_for_logo(message):
    if message.text == "❌ Отмена":
        cancel_action(message)
        return

    color_map = {"⚫ Черный": "black", "🔴 Красный": "red", "🔵 Синий": "blue", "🟢 Зеленый": "green", 
                 "🟣 Фиолетовый": "purple", "🟡 Жёлтый": "yellow"}
    chosen_color = color_map.get(message.text)
    if not chosen_color:
        bot.send_message(message.chat.id, "❗ Выбери цвет из списка:", reply_markup=color_keyboard)
        bot.register_next_step_handler(message, choose_color_for_logo)
        return

    bot.send_message(message.chat.id, f"🎨 Цвет '{message.text}' выбран! Отправь текст или ссылку:", reply_markup=cancel_keyboard)
    bot.register_next_step_handler(message, lambda msg: process_link_for_color_and_logo(msg, chosen_color))

def process_link_for_color_and_logo(message, fill_color):
    if message.text == "❌ Отмена":
        cancel_action(message)
        return
    
    data = message.text
    bot.send_message(message.chat.id, "🖼️ Теперь отправь картинку логотипа:", reply_markup=cancel_keyboard)
    bot.register_next_step_handler(message, lambda msg: add_logo_to_colored_qr(msg, data, fill_color))

def add_logo_to_colored_qr(message, data, fill_color):
    global last_qr
    if message.text == "❌ Отмена":
        cancel_action(message)
        return
    
    if message.content_type == 'photo' or message.content_type == 'document':
        try:
            if message.content_type == 'photo':
                file_info = bot.get_file(message.photo[-1].file_id)
            elif message.content_type == 'document':
                file_info = bot.get_file(message.document.file_id)

            downloaded_file = bot.download_file(file_info.file_path)
            logo = Image.open(BytesIO(downloaded_file))
            logo.thumbnail((50, 50))

            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
            qr.add_data(data)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color=fill_color, back_color="white").convert('RGB')
            pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
            qr_img.paste(logo, pos, logo if logo.mode == 'RGBA' else None)

            bio = BytesIO()
            bio.name = 'qr_color_logo.png'
            qr_img.save(bio, 'PNG')
            bio.seek(0)

            last_qr = BytesIO(bio.getvalue())
            last_qr.name = 'qr_color_logo.png'

            bot.send_photo(message.chat.id, bio, caption=f"✨ Твой QR-код с цветом ({fill_color}) и логотипом готов! 🎉", reply_markup=main_keyboard)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {e}. Попробуй снова!", reply_markup=cancel_keyboard)
            print(f"Ошибка при создании QR с цветом и логотипом: {e}")
    else:
        bot.send_message(message.chat.id, "📸 Отправь картинку (фото или файл):", reply_markup=cancel_keyboard)
        bot.register_next_step_handler(message, lambda msg: add_logo_to_colored_qr(msg, data, fill_color))

# Обработчик для "QR с градиентным фоном"
@bot.message_handler(func=lambda message: message.text == "🌈 QR с градиентным фоном")
def qr_with_gradient_background_mode(message):
    bot.send_message(message.chat.id, "🌈 Выбери первый цвет для фона:", reply_markup=background_color_keyboard)
    bot.register_next_step_handler(message, choose_first_background_color)

def choose_first_background_color(message):
    if message.text == "❌ Отмена":
        cancel_action(message)
        return

    color_map = {"🔴 Красный": "red", "🔵 Синий": "blue", "🟢 Зеленый": "green", 
                 "🟣 Фиолетовый": "purple", "🟡 Жёлтый": "yellow"}
    first_color = color_map.get(message.text)
    if not first_color:
        bot.send_message(message.chat.id, "❗ Выбери цвет из списка:", reply_markup=background_color_keyboard)
        bot.register_next_step_handler(message, choose_first_background_color)
        return

    bot.send_message(message.chat.id, f"🌈 Первый цвет фона: {message.text}. Выбери второй:", reply_markup=background_color_keyboard)
    bot.register_next_step_handler(message, lambda msg: choose_second_background_color(msg, first_color))

def choose_second_background_color(message, first_color):
    if message.text == "❌ Отмена":
        cancel_action(message)
        return

    color_map = {"🔴 Красный": "red", "🔵 Синий": "blue", "🟢 Зеленый": "green", 
                 "🟣 Фиолетовый": "purple", "🟡 Жёлтый": "yellow"}
    second_color = color_map.get(message.text)
    if not second_color:
        bot.send_message(message.chat.id, "❗ Выбери цвет из списка:", reply_markup=background_color_keyboard)
        bot.register_next_step_handler(message, lambda msg: choose_second_background_color(msg, first_color))
        return

    bot.send_message(message.chat.id, f"🌈 Цвета фона: {first_color} → {second_color}. Отправь текст или ссылку:", reply_markup=cancel_keyboard)
    bot.register_next_step_handler(message, lambda msg: generate_qr_with_gradient_background(msg, first_color, second_color))

def generate_qr_with_gradient_background(message, first_color, second_color):
    global last_qr
    if message.text == "❌ Отмена":
        cancel_action(message)
        return
    
    data = message.text
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
        
        gradient = Image.new("RGB", qr_img.size)
        mid_point = qr_img.size[0] // 2
        first_rgb = ImageColor.getrgb(first_color)
        second_rgb = ImageColor.getrgb(second_color)
        
        for x in range(gradient.size[0]):
            for y in range(gradient.size[1]):
                if x < mid_point:
                    gradient.putpixel((x, y), first_rgb)
                else:
                    gradient.putpixel((x, y), second_rgb)
        
        gradient = gradient.convert('RGBA')
        final_img = gradient.copy()
        
        qr_pixels = qr_img.load()
        for x in range(qr_img.size[0]):
            for y in range(qr_img.size[1]):
                if qr_pixels[x, y] == (255, 255, 255, 255):
                    qr_pixels[x, y] = (255, 255, 255, 0)
        
        final_img.paste(qr_img, (0, 0), qr_img)
        
        bio = BytesIO()
        bio.name = 'qr_with_gradient_background.png'
        final_img.convert('RGB').save(bio, 'PNG')
        bio.seek(0)
        
        last_qr = BytesIO(bio.getvalue())
        last_qr.name = 'qr_with_gradient_background.png'

        bot.send_photo(message.chat.id, bio, caption=f"✨ Твой QR-код с градиентным фоном ({first_color} → {second_color}) готов! 🎉", reply_markup=main_keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}", reply_markup=cancel_keyboard)
        print(f"Ошибка в generate_qr_with_gradient_background: {e}")

# Обработчик для "QR с рамкой"
@bot.message_handler(func=lambda message: message.text == "🖼️ QR с рамкой")
def qr_with_border_mode(message):
    bot.send_message(message.chat.id, "🌈 Выбери цвет для рамки:", reply_markup=color_keyboard)
    bot.register_next_step_handler(message, choose_border_color)

def choose_border_color(message):
    if message.text == "❌ Отмена":
        cancel_action(message)
        return

    color_map = {"⚫ Черный": "black", "🔴 Красный": "red", "🔵 Синий": "blue", "🟢 Зеленый": "green", 
                 "🟣 Фиолетовый": "purple", "🟡 Жёлтый": "yellow"}
    border_color = color_map.get(message.text)
    if not border_color:
        bot.send_message(message.chat.id, "❗ Выбери цвет из списка:", reply_markup=color_keyboard)
        bot.register_next_step_handler(message, choose_border_color)
        return

    bot.send_message(message.chat.id, f"🎨 Цвет рамки: {message.text}. Отправь текст или ссылку:", reply_markup=cancel_keyboard)
    bot.register_next_step_handler(message, lambda msg: generate_qr_with_border(msg, border_color))

def generate_qr_with_border(message, border_color):
    global last_qr
    if message.text == "❌ Отмена":
        cancel_action(message)
        return
    
    data = message.text
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        
        border_size = 20
        new_size = (qr_img.size[0] + 2 * border_size, qr_img.size[1] + 2 * border_size)
        final_img = Image.new('RGB', new_size, ImageColor.getrgb(border_color))
        final_img.paste(qr_img, (border_size, border_size))
        
        bio = BytesIO()
        bio.name = 'qr_with_border.png'
        final_img.save(bio, 'PNG')
        bio.seek(0)
        
        last_qr = BytesIO(bio.getvalue())
        last_qr.name = 'qr_with_border.png'

        bot.send_photo(message.chat.id, bio, caption=f"✨ Твой QR-код с рамкой ({border_color}) готов! 🎉", reply_markup=main_keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}", reply_markup=cancel_keyboard)
        print(f"Ошибка в generate_qr_with_border: {e}")

# Обработчик для "Сканировать QR"
@bot.message_handler(func=lambda message: message.text == "🔍 Сканировать QR")
def scan_qr_mode(message):
    bot.send_message(message.chat.id, "📸 Отправь фото QR-кода, чтобы я его отсканировал:", reply_markup=cancel_keyboard)
    bot.register_next_step_handler(message, process_qr_scan)

def process_qr_scan(message):
    if message.text == "❌ Отмена":
        cancel_action(message)
        return
    
    if message.content_type == 'photo':
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            img = Image.open(BytesIO(downloaded_file))
            
            open_cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            kernel = np.ones((3, 3), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            qr_detector = cv2.QRCodeDetector()
            data, bbox, _ = qr_detector.detectAndDecode(thresh)
            
            if not data:
                data, bbox, _ = qr_detector.detectAndDecode(open_cv_image)
            
            if data:
                bot.send_message(message.chat.id, f"✅ QR-код отсканирован! Содержимое:\n\n{data}", reply_markup=main_keyboard)
            else:
                bot.send_message(message.chat.id, "❗ Не удалось найти QR-код на фото. Попробуй четкое изображение:", reply_markup=cancel_keyboard)
                bot.register_next_step_handler(message, process_qr_scan)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка при сканировании: {e}. Попробуй снова!", reply_markup=cancel_keyboard)
            bot.register_next_step_handler(message, process_qr_scan)
            print(f"Ошибка при сканировании QR: {e}")
    else:
        bot.send_message(message.chat.id, "📸 Пожалуйста, отправь фото QR-кода:", reply_markup=cancel_keyboard)
        bot.register_next_step_handler(message, process_qr_scan)

@bot.message_handler(func=lambda message: message.text == "❌ Отмена")
def cancel_action(message):
    bot.send_message(message.chat.id, "👌 Действие отменено! Выбери новый стиль:", reply_markup=main_keyboard)

@bot.message_handler(func=lambda message: True)
def log_user_actions(message):
    print(f"Пользователь {message.from_user.username} ({message.from_user.id}) отправил: {message.text}")

bot.polling(none_stop=True)