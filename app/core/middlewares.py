import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import TelegramObject, Message, User
from aiogram.utils.chat_action import ChatActionSender

from .redis_db import RedisDataBaseClient
from db.utils import AsyncDataBase


class ThrottlingMessagesMiddleware(BaseMiddleware):

    def __init__(self, redis_client: RedisDataBaseClient, flood_wait_secs: int = 3):
        self.redis_client = redis_client
        self.flood_wait_secs = flood_wait_secs

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:

        user_id = data['event_from_user'].id
        user_throttling_data = await self.redis_client.get_user_throttle(user_id)

        if user_throttling_data is None:
            await self.redis_client.set_user_throttle(user_id, self.flood_wait_secs)
            return await handler(event, data)


class AddUserToDataBasesMiddleware(BaseMiddleware):

    def __init__(self, redis_client: RedisDataBaseClient, async_db: AsyncDataBase):
        self.redis_client = redis_client
        self.async_db = async_db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        user: User = data['event_from_user']
        user_id = user.id
        username = user.username

        user_in_redis = await self.redis_client.is_user_in_db(user_id)

        if not user_in_redis:
            await self.redis_client.set_username(user_id, username)
            await self.async_db.create_user_if_not_exist(telegram_id=user_id,
                                                         user_name=username,
                                                         first_name=user.first_name,
                                                         last_name=user.last_name)

        return await handler(event, data)


class CheckAndUpdateUsernameMiddleware(BaseMiddleware):

    def __init__(self, redis_client: RedisDataBaseClient, async_db: AsyncDataBase):
        self.redis_client = redis_client
        self.async_db = async_db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        user: User = data['event_from_user']
        user_id = user.id
        actual_username = user.username
        saved_username = await self.redis_client.get_username(user_id)

        if actual_username != saved_username:
            await self.redis_client.set_username(user_id, actual_username)
            await self.async_db.update_tg_username(user_id, actual_username)

        return await handler(event, data)


class ChatActionMiddleware(BaseMiddleware):

    """
    Middleware для отправки статуса (например, "печатает") во время длительных операций.
    """

    async def __call__(self,
                       handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:

        long_operation_type = get_flag(data, 'long_operation')

        # Если такого флага на хэндлере нет
        if not long_operation_type:
            return await handler(event, data)

        # Если флаг есть
        async with ChatActionSender(action=long_operation_type,
                                    chat_id=data['event_chat'].id,
                                    bot=data['bot']):

            return await handler(event, data)
