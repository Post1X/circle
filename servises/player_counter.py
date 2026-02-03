import asyncio
import random
from typing import Optional
from redis import asyncio as aioredis
from servises.config import config
from celery import Celery
import time


celery_app = Celery('player_counter')


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from celery_config import CELERY_CONFIG

celery_app.conf.update(**CELERY_CONFIG)


class PlayerCounterService:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.real_count_key = "active_players:real"
        self.fake_count_key = "active_players:fake"
        self.target_fake_count = 9000
        self.fake_count_variance = 1000
        
    async def init_redis(self):
        if not self.redis:
            self.redis = aioredis.from_url(
                f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
                encoding="utf-8",
                decode_responses=True
            )
    
    async def increment_real_count(self, user_id: str) -> int:
        await self.init_redis()
        pipe = self.redis.pipeline()
        pipe.hincrby(self.real_count_key, user_id, 1)
        pipe.expire(self.real_count_key, 300)
        results = await pipe.execute()
        return results[0]
    
    async def decrement_real_count(self, user_id: str) -> int:
        await self.init_redis()
        pipe = self.redis.pipeline()
        pipe.hincrby(self.real_count_key, user_id, -1)
        pipe.expire(self.real_count_key, 300)
        results = await pipe.execute()
        return results[0]
    
    async def get_real_count(self) -> int:
        await self.init_redis()
        count = await self.redis.hlen(self.real_count_key)
        return count
    
    async def get_fake_count(self) -> int:
        await self.init_redis()
        count = await self.redis.get(self.fake_count_key)
        if count is None:
            await self.update_fake_count()
            count = await self.redis.get(self.fake_count_key)
        return int(count) if count else self.target_fake_count
    
    async def update_fake_count(self):
        """Обновить фейковый счетчик с плавными изменениями"""
        await self.init_redis()
        current_fake = await self.redis.get(self.fake_count_key)
        current_fake = int(current_fake) if current_fake else self.target_fake_count
        
        if current_fake < self.target_fake_count:
            change = random.randint(50, 200)
            new_count = min(current_fake + change, self.target_fake_count)
        elif current_fake > self.target_fake_count:
            change = random.randint(50, 200)
            new_count = max(current_fake - change, self.target_fake_count)
        else:
            variance = random.randint(-self.fake_count_variance, self.fake_count_variance)
            new_count = self.target_fake_count + variance
        
        await self.redis.set(self.fake_count_key, new_count, ex=3600)  # TTL 1 час
    
    async def cleanup_expired_users(self):
        """Очистка устаревших записей пользователей"""
        await self.init_redis()

        users = await self.redis.hgetall(self.real_count_key)
        for user_id, count in users.items():
            if int(count) <= 0:
                await self.redis.hdel(self.real_count_key, user_id)


player_counter_service = PlayerCounterService()


@celery_app.task
def update_fake_count_task():
    """Задача для обновления фейкового счетчика"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(player_counter_service.update_fake_count())
    finally:
        if not loop.is_closed():
        loop.close()

@celery_app.task
def cleanup_expired_users_task():
    """Задача для очистки устаревших пользователей"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(player_counter_service.cleanup_expired_users())
    finally:
        if not loop.is_closed():
        loop.close()


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(30.0, update_fake_count_task.s(), name='update-fake-count')
    sender.add_periodic_task(300.0, cleanup_expired_users_task.s(), name='cleanup-expired-users') 
    