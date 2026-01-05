from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import asyncio

from bd import Base
from servises import config

engine = create_async_engine(config.database_url, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

async def main():
    await drop_db()
    print("Database dropped.")



asyncio.run(main())
