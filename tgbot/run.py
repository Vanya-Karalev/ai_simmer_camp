import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from app.handlers import router
from config import settings


async def main():
    load_dotenv()
    bot = Bot(token=settings.tg_token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Interrupted')
