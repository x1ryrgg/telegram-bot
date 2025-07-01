from dotenv import load_dotenv
from middleware import log_middleware
from handlers.login_handlers import dp_router
from handlers.authentication_handlers import auth_router
import os
from aiogram import Bot, Dispatcher


load_dotenv()
bot = Bot(token=os.getenv("TG_TOKEN"))
dp = Dispatcher()
dp.update.middleware(log_middleware)
dp.include_router(dp_router)
dp.include_router(auth_router)


if __name__ == "__main__":
    dp.run_polling(bot)