import asyncio
import logging
from os import getenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from handlers import router
from redis_db import redis_client
from middlewares import ThrottlingMessagesMiddleware


async def start_bot() -> None:
    logging.basicConfig(level=logging.WARNING,
                        filename='errors.txt',
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        encoding='utf-8')

    redis_fsm_dsn = getenv('REDIS_FSM_DSN')
    redis_fsm = RedisStorage.from_url(redis_fsm_dsn)

    token = getenv('BOT_TOKEN')
    bot = Bot(token=token, parse_mode=ParseMode.HTML)
    await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher(events_isolation=SimpleEventIsolation(),
                    storage=redis_fsm,
                    redis_client=redis_client)

    dp.callback_query.middleware(CallbackAnswerMiddleware())
    dp.message.middleware(ThrottlingMessagesMiddleware(redis_client))
    dp.include_routers(router)

    try:
        await dp.start_polling(bot)
    except Exception as err:
        logging.error(f'{err}', exc_info=True)
    finally:
        await bot.session.close()
        await dp.storage.close()
        await redis_client.aclose()


if __name__ == '__main__':
    asyncio.run(start_bot())
