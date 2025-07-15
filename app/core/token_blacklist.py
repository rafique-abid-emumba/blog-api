from app.core.redis import redis_client

def blacklist_token(token: str, expires_in: int):
    redis_client.setex(f"bl_refresh_{token}", expires_in, "blacklisted")

def is_token_blacklisted(token: str) -> bool:
    return redis_client.exists(f"bl_refresh_{token}") == 1