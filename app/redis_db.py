import redis.asyncio as redis
from os import getenv


# redis_cache = Redis(host=getenv('REDIS_CACHE_HOST'),
#                     port=int(getenv('REDIS_CACHE_PORT')),
#                     db=int(getenv('REDIS_CACHE_DB')),
#                     decode_responses=True)

redis_client = redis.Redis.from_url(getenv('REDIS_CACHE_DSN'), decode_responses=True)
