from typing import Union
import jwt
from time import time
from functools import wraps
from dateutil.parser import parse

from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from datetime import datetime
from api import refresh_access_token
from cache import save_tokens_redis, get_tokens_redis, delete_tokens_redis
import logging

logger = logging.getLogger(__name__)


def auth_required(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        # Получаем токены из Redis
        tg_id = message.from_user.id
        tokens = await get_tokens_redis(tg_id)

        if not tokens:
            await message.answer("❌ Требуется авторизация! /start",
                                 reply_markup=ReplyKeyboardRemove())
            return

        # Проверяем срок действия access_token
        try:
            decoded = jwt.decode(tokens["access"], options={"verify_signature": False})
            if decoded.get("exp", 0) < time():
                # Обновляем токен, если истек
                new_tokens = await refresh_access_token(tokens["refresh"])
                if new_tokens:
                    await save_tokens_redis(tg_id, {
                        'access': new_tokens["access"],
                        'refresh': tokens["refresh"]
                    })
                    return await func(message, new_tokens["access"], *args, **kwargs)
                else:
                    await message.answer("❌ Сессия истекла. Авторизуйтесь снова /start")
                    return
        except jwt.DecodeError:
            await message.answer("❌ Ошибка токена. Авторизуйтесь снова /start")
            return

        # Выполняем запрос с текущим токеном
        return await func(message, tokens["access"], *args, **kwargs)

    return wrapper


def format_profile(profile):
    return [
        f"👤 <b>Ваш профиль</b>\n",
        f"🔹 <b>Логин:</b> <code>{profile['username']}</code>",
        f"📧 <b>Email:</b> {profile['email']}",
        f"✖️ <b>Имя:</b> {profile['first_name'] or 'не указано'}",
        f"✖️ <b>Фамилия:</b> {profile['last_name'] or 'не указано'}",
        f"🎓 <b>Роль:</b> {'преподаватель' if profile['role'] == 'teacher' else 'студент'}"
    ]


def format_event(event):
    try:
        # Универсальный парсинг даты с timezone
        event_date = parse(event['event_date'])
        # Форматируем в читаемый вид с учетом часового пояса
        formatted_date = event_date.strftime("%d.%m.%Y в %H:%M")
    except (ValueError, KeyError) as e:
        formatted_date = "дата не указана"

    caption = (
        f"🎯 <b>{event.get('title', 'Без названия')}</b>\n\n"
        f"⏳ <i>Дата проведения:</i> <b>{formatted_date}</b>\n"
        f"🏛 <i>Группа:</i> {event.get('group', {}).get('name', 'не указана')}\n"
        f"👤 <i>Организатор:</i> {event['author']['username']}\n"
        f"📝 <i>Описание:</i> {event.get('description', 'нет описания')}\n"
        f"👥 <i>Участников:</i> {event.get('attendees', 'пока нет')}\n"
        f"🔖 <i>Тип:</i> {event.get('type', 'не указан').capitalize()}"
    )

    photo_url = event.get('first_photo', {}).get('photo') if event.get('first_photo') else None

    return {
        'caption': caption,
        'photo_url': photo_url
    }

