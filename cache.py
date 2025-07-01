import redis.asyncio as redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    db=int(os.getenv("REDIS_DB")),
    decode_responses=True
)


async def save_tokens_redis(tg_id: int, tokens: dict) -> bool:
    """Сохраняет токены в Redis (асинхронно)."""
    try:
        await redis_client.set(f"user:{tg_id}", json.dumps(tokens), ex=60 * 60)
        return True
    except Exception as e:
        print(f"Redis Save Error: {e}")
        return False

async def get_tokens_redis(tg_id: int) -> dict | None:
    """Получает токены из Redis (асинхронно) с атомарным обновлением TTL."""
    async with redis_client.pipeline() as pipe:
        data, _ = await (pipe.get(f"user:{tg_id}")
                         .expire(f"user:{tg_id}", 60 * 60)
                         .execute())
        return json.loads(data) if data else None

async def delete_tokens_redis(tg_id: int) -> None | bool:
    """Удаляет токены из Redis (асинхронно)."""
    await redis_client.delete(f"user:{tg_id}")
    return True