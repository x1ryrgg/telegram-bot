from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils import markdown
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from api import authenticate_user, get_profile, get_events, link_telegram_id, check_user_role
from cache import get_tokens_redis, save_tokens_redis, delete_tokens_redis
from config import auth_required
from keyboards import main_keyboard


dp_router = Router()

class AuthState(StatesGroup):
    username = State()
    password = State()


@dp_router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    tokens = await get_tokens_redis(tg_id)

    if tokens:
        await message.answer("✅ Вы уже авторизованы! \n"
                             "Выберите нужный пункт в клавиатуре.", reply_markup=main_keyboard())
        await state.clear()
        return
    else:
        await message.answer(text=markdown.text("🔐 Введите ваш", markdown.bold("username"), "от аккаунта вгту:"),
                             parse_mode=ParseMode.MARKDOWN_V2)
        await state.set_state(AuthState.username)


@dp_router.message(AuthState.username)
async def handle_username(message: Message, state: FSMContext):
    # Игнорировие сообщения если состояние не соответствует
    current_state = await state.get_state()
    if current_state != AuthState.username:
        return

    await state.update_data(username=message.text)
    await message.answer(text=markdown.text("🔐 Теперь введите ваш ", markdown.bold("пароль"), ":"),
                         parse_mode=ParseMode.MARKDOWN_V2)
    await state.set_state(AuthState.password)


@dp_router.message(AuthState.password)
async def handle_password(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != AuthState.password:
        return

    data = await state.get_data()
    username = data["username"]
    password = message.text
    tg_id = message.from_user.id

    tokens = await authenticate_user(username, password)
    if not tokens:
        await message.answer("❌ Ошибка авторизации. Проверьте данные! /start")
        await state.clear()
        return

    if not await save_tokens_redis(tg_id, tokens):
        await message.answer("❌ Ошибка сохранения токенов. Попробуйте позже. /start")
        await state.clear()
        return

    success = await link_telegram_id(tokens["access"], tg_id)
    if not success:
        await message.answer("❌ Ошибка привязки аккаунта. Попробуйте позже. /start")
        await state.clear()
        return

    await message.answer("✅ Успешная авторизация!\n "
                         "Выберите нужный пункт в клавиатуре. ", reply_markup=main_keyboard())
    await state.clear()


@dp_router.message(F.text == 'Выйти из акканута')
async def delete_token_handler(message: Message):
    tg_id = message.from_user.id
    try:
        success = await delete_tokens_redis(tg_id)
        if success:
            await message.answer("✅ Вы успешно вышли из аккаунта.\n"
                                 "Для повторной авторизации используйте /start", reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer(
                "⚠️ Не удалось выйти из аккаунта. Попробуйте позже.",
                reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")