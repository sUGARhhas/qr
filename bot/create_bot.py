from aiogram import Bot, Dispatcher
import os
from aiogram.fsm.storage.memory import MemoryStorage

storage = MemoryStorage()

bot = Bot(token="5917276984:AAFc697QqPrJlH_cM_Owulha33tIuO4Vrhw")
dp = Dispatcher(storage=storage)
