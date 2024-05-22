from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
import redis.asyncio as async_redis


class ThrottlingMessagesMiddleware(BaseMiddleware):

    def __init__(self, redis_client: async_redis.Redis, flood_wait_secs: int = 3):
        self.redis_client = redis_client
        self.flood_wait_secs = flood_wait_secs

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:

        user_id_str = str(event.from_user.id)
        user_throttling_data = await self.redis_client.get(user_id_str)

        if user_throttling_data is None:
            await self.redis_client.set(user_id_str, 1, ex=self.flood_wait_secs)
            return await handler(event, data)
