import aiosqlite
import os

DB_FILE = 'users.db'

async def create_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                photo TEXT,
                education_place TEXT,
                role TEXT,
                course TEXT,
                completed_works INTEGER DEFAULT 0,
                is_confirmed INTEGER DEFAULT 0
            )
        ''')
        await db.commit() 