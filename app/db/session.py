from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


if settings.DATABASE_URL.startswith("postgresql+psycopg2://"):
    async_database_url = settings.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
elif settings.DATABASE_URL.startswith("postgresql://"):
    async_database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    async_database_url = settings.DATABASE_URL

async_engine = create_async_engine(
    async_database_url,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    echo=False
)

AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()
