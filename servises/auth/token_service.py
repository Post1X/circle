import redis.asyncio as aioredis

from servises.config import config

from datetime import timedelta


class TokenService:
    def __init__(self):
        self.redis = None
    
    async def init_redis(self):
        if not self.redis:
            self.redis = aioredis.from_url(f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}")
    
    async def add_to_blacklist(self, token: str, expires_in: int = None):
        await self.init_redis()
        
        if expires_in:
            await self.redis.setex(f"blacklist:{token}", expires_in, "1")
        else:
            await self.redis.setex(f"blacklist:{token}", 24 * 60 * 60, "1")
    
    async def is_blacklisted(self, token: str) -> bool:
        await self.init_redis()
        
        result = await self.redis.exists(f"blacklist:{token}")
        return bool(result)
    
    async def remove_from_blacklist(self, token: str):
        await self.init_redis()
        await self.redis.delete(f"blacklist:{token}")
    
    async def close(self):
        if self.redis:
            await self.redis.close()


token_service = TokenService()
