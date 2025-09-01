import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def get_redis() -> redis.Redis:
    # decode_responses=True => always str (no bytes/str mismatches)
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)