from contextlib import asynccontextmanager

import logging

import uvicorn
import asyncio
import socketio

from redis import asyncio as aioredis

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache import FastAPICache
from fastapi.staticfiles import StaticFiles

from servises import config
from handlers import admin_router, sio, pub_router, game_router, skills_router, user_router, beta_game_router, withdrawal_router

from bd import Base
from bd.database import engine

from servises.auth.token_service import token_service
from servises.player_counter import player_counter_service
from servises.tron_monitor import start_tron_monitor
from servises.withdrawal_service import start_withdrawal_processing, start_withdrawal_monitoring
from servises.hot_wallet_init import init_hot_wallet

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = aioredis.from_url(f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}")
    
    FastAPICache.init(RedisBackend(redis), prefix="cache")

    await player_counter_service.init_redis()
    
    await token_service.init_redis()
    
    await init_hot_wallet()

    yield
    
    await redis.close()
    await token_service.close()


app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(admin_router)
app.include_router(game_router)
app.include_router(pub_router)
app.include_router(skills_router)
app.include_router(user_router)
app.include_router(beta_game_router)
app.include_router(withdrawal_router)

app.mount("/static", StaticFiles(directory="static"), name="static")


async def run_api():
    cf = uvicorn.Config(socketio.ASGIApp(sio,app), host="0.0.0.0", port=8000, log_level="info", reload=True if config.mode == "test" else False)
    server = uvicorn.Server(cf)
    try:
        await server.serve()
    finally:
        if hasattr(server, 'should_exit'):
            server.should_exit = True


async def main():
    try:
        await asyncio.gather(
            run_api(),
            start_tron_monitor(),
            start_withdrawal_processing(),
            start_withdrawal_monitoring(),
        )
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
