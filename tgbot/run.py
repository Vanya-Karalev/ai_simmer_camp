import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from app.handlers import router
from config import settings
from app.database.models import async_main
from alembic import command
from alembic.config import Config


async def main():
    await async_main()
    load_dotenv()
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    bot = Bot(token=settings.tg_token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Interrupted')
