from redis import Redis

from stock_market_analyzer.config.settings import Settings


def create_redis_client(settings: Settings) -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def check_cache_health(client: Redis) -> bool:
    try:
        return client.ping()
    except Exception:
        return False
