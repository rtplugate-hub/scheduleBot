import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import Config
from app.handler import rout
from app.server import rs

config = Config("config.yaml")
logging.info(f"BOT_TOKEN found: {config.bot_token is not None}")

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(rout)


async def main():
    await rs()
    logging.info("start!!!")
    await dp.start_polling(bot, config=config)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
