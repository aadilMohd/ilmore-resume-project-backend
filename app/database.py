from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings
from uuid import uuid4


# 1. Create the Async Engine
# We use echo=True during development so we can see the raw SQL queries in the terminal
engine = create_async_engine(
    settings.DATABASE_URL,
    # Add this exact connect_args dictionary:
    connect_args={
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
    }
)

# 2. Create the Session Factory
# This is what we will use in our FastAPI endpoints to talk to the database
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 3. Create the Base Model
# All of our database tables will inherit from this base class
Base = declarative_base()

# 4. Dependency Injection for FastAPI
# We will use this function to give each API request its own database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session