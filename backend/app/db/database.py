from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@localhost:5432/mock_interview_db"

# Engine for the database
engine = create_async_engine(DATABASE_URL, echo=True)

# Session maker for the database
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Dependency to get a database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session