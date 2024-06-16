import redis.asyncio as redis


class RedisDataBaseClient:
    def __init__(self, dsn: str, cached_user_data_prefix: str = 'userdata'):
        self.dsn = dsn
        self.redis_client = redis.Redis.from_url(dsn, decode_responses=True)
        self.cached_user_data_prefix = cached_user_data_prefix
        self.username_key = 'tg_username'
        self.throttle_key = 'throttle'
        self.app_cached_data_key = 'app_cached_data'

    def get_user_key(self, tg_id: int) -> str:
        return f'{self.cached_user_data_prefix}_{tg_id}'

    def get_user_throttle_key(self, tg_id: int) -> str:
        return f'{self.throttle_key}_{tg_id}'

    async def set_username(self, tg_id: int, username: str):
        username = username or ''
        await self.redis_client.hset(self.get_user_key(tg_id), self.username_key, username)

    async def get_username(self, tg_id: int) -> str:
        return await self.redis_client.hget(self.get_user_key(tg_id), self.username_key)

    async def username_is_changed(self, tg_id: int, current_username: str) -> bool:
        cached_user_name = await self.get_username(tg_id)
        return not (current_username == cached_user_name)

    async def is_user_in_db(self, tg_id: int):
        return await self.redis_client.exists(self.get_user_key(tg_id))

    async def get_user_cached_data(self, tg_id: int) -> dict:
        return await self.redis_client.hgetall(self.get_user_key(tg_id))

    async def is_username_setted(self, tg_id: int) -> bool:
        return (await self.redis_client.exists(self.get_user_key(tg_id), self.username_key)) == 1

    async def set_username_if_not_exists(self, tg_id: int, current_username: str):
        is_username_exists = await self.is_username_setted(tg_id)
        if is_username_exists is False:
            await self.set_username(tg_id, current_username)

    async def set_username_if_invalid(self, tg_id: int, current_username: str) -> bool:
        username = await self.get_username(tg_id)
        need_update = username is None or username != current_username
        if need_update:
            await self.set_username(tg_id, current_username)
        # был ли изменён username. True/False
        return need_update

    async def update_user_name_if_changed(self, tg_id: int, current_username: str) -> bool:
        current_username = current_username or ''
        saved_username = await self.get_username(tg_id)
        need_update = saved_username != current_username
        if need_update:
            await self.set_username(tg_id, current_username)
        # был ли изменён username. True/False
        return need_update

    async def get_user_throttle(self, tg_id: int):
        return await self.redis_client.get(self.get_user_throttle_key(tg_id))

    async def set_user_throttle(self, tg_id: int, sec: int):
        await self.redis_client.set(self.get_user_throttle_key(tg_id), 1, ex=sec)

    async def get_picture_id(self, picture_name: str) -> str:
        return await self.redis_client.hget(self.app_cached_data_key, picture_name)

    async def set_picture_id(self, picture_name: str, picture_id: str):
        await self.redis_client.hset(self.app_cached_data_key, picture_name, picture_id)

    async def aclose(self):
        await self.redis_client.aclose()
