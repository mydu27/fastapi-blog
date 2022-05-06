from fastapi import HTTPException
from typing import AsyncGenerator
from app.core.config import settings
from redis import Redis, ConnectionPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

Base = declarative_base()

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    future=True,
    echo=False,
)
SessionLocal = sessionmaker(expire_on_commit=False,
                            autoflush=False,
                            class_=AsyncSession)
SessionLocal.configure(bind=engine)


async def get_db() -> AsyncGenerator:
    async with SessionLocal() as db:
        try:
            yield db
            await db.commit()
        except SQLAlchemyError as sql_ex:
            await db.rollback()
            raise sql_ex
        except HTTPException as http_ex:
            await db.rollback()
            raise http_ex
        finally:
            await db.close()


# redis连接
class Cache:

    _client = None

    @classmethod
    def client(cls):
        """
        单例模式获取连接
        """
        if cls._client:
            return cls._client
        else:
            pool = ConnectionPool(host=settings.REDIS_HOST,
                                  port=settings.REDIS_PORT,
                                  db=settings.REDIS_DB)
            cls._client = Redis(connection_pool=pool, decode_responses=True)
        return cls._client


cache = Cache().client()
