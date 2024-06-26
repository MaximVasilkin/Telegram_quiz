import asyncio
import logging
from os import getenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from db.utils import AsyncDataBase
from core.handlers import router
from core.admin_handlers import admin_router
from core.redis_db import RedisDataBaseClient
from core.middlewares import AddUserToDataBasesMiddleware, \
                             CheckAndUpdateUsernameMiddleware, \
                             ThrottlingMessagesMiddleware, \
                             ChatActionMiddleware


async def start_bot() -> None:
    logging.basicConfig(level=logging.WARNING,
                        filename='./logs/tg_bot_log.txt',
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        encoding='utf-8')

    redis_fsm_dsn = getenv('REDIS_FSM_DSN')
    redis_fsm = RedisStorage.from_url(redis_fsm_dsn)

    redis_cache_dsn = getenv('REDIS_CACHE_DSN')
    redis_cache_client = RedisDataBaseClient(redis_cache_dsn)

    async_db_dsn = f'{getenv("DB_TYPE")}+{getenv("DB_DRIVER")}://' \
                   f'{getenv("DB_USER")}:{getenv("DB_PASSWORD")}@' \
                   f'{getenv("DB_HOST")}:{getenv("DB_PORT")}/' \
                   f'{getenv("DB_NAME")}'

    async_db = AsyncDataBase(async_db_dsn)
    await async_db.create_tables_if_not_exist()

    token = getenv('BOT_TOKEN')
    bot = Bot(token=token, parse_mode=ParseMode.HTML)
    await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher(events_isolation=SimpleEventIsolation(),
                    storage=redis_fsm,
                    redis_client=redis_cache_client,
                    async_db=async_db,
                    system_temp_data={})

    dp.update.outer_middleware(AddUserToDataBasesMiddleware(redis_cache_client, async_db))
    dp.update.outer_middleware(CheckAndUpdateUsernameMiddleware(redis_cache_client, async_db))
    dp.message.middleware(ThrottlingMessagesMiddleware(redis_cache_client))
    dp.callback_query.middleware(CallbackAnswerMiddleware())
    dp.callback_query.middleware(ChatActionMiddleware())
    dp.message.middleware(ChatActionMiddleware())

    dp.include_routers(router, admin_router)

    try:
        await dp.start_polling(bot)
    except Exception as err:
        logging.error(f'{err}', exc_info=True)
    finally:
        await bot.session.close()
        await dp.storage.close()
        await redis_cache_client.aclose()
        await async_db.disconnect()


if __name__ == '__main__':
    asyncio.run(start_bot())
