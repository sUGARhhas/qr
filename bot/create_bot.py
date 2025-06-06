from aiogram import Bot, Dispatcher
import os
from aiogram.fsm.storage.memory import MemoryStorage

storage = MemoryStorage()

bot = Bot(token="7873300445:AAGigBhxKPetZp8tCpqgOHQx2ndv2gWQSxc")
dp = Dispatcher(storage=storage)
