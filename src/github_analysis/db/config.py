import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

# Default to docker-compose database URL if not overridden
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://github_analysis:github_analysis@localhost/github_analysis"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency for FastAPI endpoints
async def get_db():
    async with async_session() as session:
        yield session