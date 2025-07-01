import os
from typing import Any, Coroutine

import requests
from dotenv import load_dotenv
import logging

load_dotenv()
API_URL = os.getenv("API_URL")

logger = logging.getLogger(__name__)

async def authenticate_user(username: str, password: str) -> dict | None:
    """Аутентификация пользователя и получение токенов."""
    try:
        response = requests.post(
            f"{API_URL}/api/token/",
            json={"username": username, "password": password}
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"Auth Error: {e}")
        return None

async def refresh_access_token(refresh_token: str) -> dict | None:
    """Обновление access_token через refresh_token."""
    try:
        response = requests.post(
            f"{API_URL}/api/token/refresh/",
            json={"refresh": refresh_token}
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error("Refresh Error: {e}")
        return None

async def link_telegram_id(access_token: str, tg_id: int) -> bool:
    """Привязывает tg_id к пользователю в DRF."""
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.patch(
            f"{API_URL}/user/link_telegram/",
            json={"tg_id": tg_id},
            headers=headers
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"link_telegram_id Error: {e}")
        return False

async def check_user_role(access_token: str, tg_id: int) -> Any | None:
    """Проверка, есть ли пользователь с таким tg_id в БД."""
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(f"{API_URL}/users/{tg_id}/", headers=headers)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"check_user_role Error: {e}")
        return None

async def get_profile(access_token: str) -> dict | None:
    """ Полечение информации об аккаунте"""
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(f"{API_URL}/me/", headers=headers)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"get_profile Error: {e}")
        return None

async def get_groups_list(access_token: str) -> list | None:
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(f"{API_URL}/group/", headers=headers)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"get_groups_list Error: {e}")
        return None

async def post_event(access_token: str, json: dict) -> bool | None:
    """Получение всех мероприятий. """
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.post(f"{API_URL}/event/", headers=headers, json=json)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"post_event Error: {e}")
        return None

async def get_events(access_token: str) -> list | None:
    """Получение всех мероприятий. """
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(f"{API_URL}/event/", headers=headers)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"get_events Error: {e}")
        return None
