import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from ..config import settings

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8",
        )
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


async def json_get(key: str) -> Optional[dict]:
    r = await get_redis()
    data = await r.get(key)
    if data:
        return json.loads(data)
    return None


async def json_set(key: str, value: dict, ex: Optional[int] = None):
    r = await get_redis()
    await r.set(key, json.dumps(value, ensure_ascii=False), ex=ex)


async def json_list(prefix: str) -> list[dict]:
    r = await get_redis()
    keys = []
    async for key in r.scan_iter(match=f"{prefix}*"):
        keys.append(key)
    result = []
    for key in sorted(keys):
        data = await json_get(key)
        if data:
            result.append(data)
    return result


async def delete_key(key: str):
    r = await get_redis()
    await r.delete(key)


async def publish(channel: str, message: dict):
    r = await get_redis()
    await r.publish(channel, json.dumps(message, ensure_ascii=False))


async def get_pubsub() -> aioredis.client.PubSub:
    r = await get_redis()
    return r.pubsub()
