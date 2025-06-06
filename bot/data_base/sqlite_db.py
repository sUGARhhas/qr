import sqlite3 as sq
import os

# Формируем абсолютный путь к файлу БД
# os.path.dirname(__file__) - получает путь к директории, где находится текущий скрипт (data_base)
# os.path.dirname(...) - поднимается на один уровень выше (в папку bot)
# os.path.join(..., 'DataBase.db') - добавляет имя файла к пути
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'DataBase.db')

def sql_start():
    global base, cur_base

    base = sq.connect(DB_PATH)
    cur_base = base.cursor()

    if base:
        print('Database connected OK!')

    # Создаем таблицу слов, если она не существует
    cur_base.execute('CREATE TABLE IF NOT EXISTS word('
                     'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                     'word TEXT UNIQUE, '
                     'transcription TEXT, '
                     'description TEXT, '
                     'example TEXT, '
                     'category TEXT )')
    base.commit()

    # Создаем таблицу пользователей, если она не существует
    cur_base.execute('CREATE TABLE IF NOT EXISTS users('
                     'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                     'ud TEXT UNIQUE, '
                     'username TEXT, '
                     'category TEXT, '
                     'category_1 INTEGER DEFAULT 0 , '
                     'category_2 INTEGER DEFAULT 0, '
                     'category_3 INTEGER DEFAULT 0 )')
    base.commit()

    return base, cur_base

def get_user_category(ud):
    cur_base.execute('SELECT category FROM users WHERE ud = ?', (ud,))
    result = cur_base.fetchone()
    return result[0] if result else None

def update_user_category(ud, new_category):
    cur_base.execute('UPDATE users SET category = ? WHERE ud = ?', (new_category, ud))
    base.commit()

def get_next_word(category):
    cur_base.execute('SELECT word, transcription, description, example FROM word WHERE category = ? '
                     'ORDER BY RANDOM() LIMIT 1', (category,))
    return cur_base.fetchone()

def increase_category_count(ud, category):
    cur_base.execute(f'UPDATE users SET {category} = {category} + 1 WHERE ud = ?', (ud,))
    base.commit()

def add_user(username, ud):
    # Добавляем нового пользователя с начальными значениями
    cur_base.execute('INSERT OR IGNORE INTO users(ud, username, category, category_1, category_2, category_3) '
                     'VALUES (?, ?, ?, ?, ?, ?)',
                     (ud, username, 'category_1', 0, 0, 0))
    base.commit()

def sql_add_command(word, transcription, description, example, category):
    # Добавляем слово в таблицу
    cur_base.execute('INSERT INTO word(word, transcription, description, example, category) VALUES (?, ?, ?, ?, ?)',
                     (word, transcription, description, example, category))
    base.commit()

def close_connections(base):
    base.close()
