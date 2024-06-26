import asyncio
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.flags import get_flag
from aiogram.types import TelegramObject, Message, User
from aiogram.utils.chat_action import ChatActionSender
from .redis_db import RedisDataBaseClient
from db.utils import AsyncDataBase
from .utils import get_admins


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
        is_username_updated = await self.redis_client.update_user_name_if_changed(user_id, actual_username)

        if is_username_updated:
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


class OnlyForAdminMiddleware(BaseMiddleware):

    @property
    def admins(self):
        return get_admins()

    async def __call__(self,
                       handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:

        # выполняем, если от админа
        if data['event_from_user'].id in self.admins:
            return await handler(event, data)


class OnePersonOperationMiddleware(BaseMiddleware):

    """
    Middleware для блокировки кокурентного выполнения хендлера.
    """
    def __init__(self, wait_for_result=False, check_period=1):
        self.wait_for_result = wait_for_result
        self.check_period = check_period

    async def __call__(self,
                       handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:

        is_one_person_operation = get_flag(data, 'one_person_operation')

        if is_one_person_operation:
            system_temp_data: dict = data['system_temp_data']
            is_pending = system_temp_data.get('pending')
            if is_pending:
                bot: Bot = data['bot']
                event_from_user: User = data['event_from_user']
                await bot.send_message(event_from_user.id, 'На данный момент бот уже занят выгрузкой данных.\n'
                                                           'Пожалуйста, повторите попытку позже.')
                if not self.wait_for_result:
                    return

            while system_temp_data.get('pending'):
                await asyncio.sleep(self.check_period)

            system_temp_data['pending'] = True
            try:
                result = await handler(event, data)
            finally:
                system_temp_data['pending'] = False
            return result

        return await handler(event, data)

