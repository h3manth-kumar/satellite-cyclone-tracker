"""
Pytest configuration and async test fixtures.
"""
import pytest
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

os.environ["USE_MOCK_ML"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_cyclone.db"
os.environ["SATELLITE_DATA_DIR"] = "./test_data/satellite"

from app.models import Base
from app.db.session import get_db
from app.db.init_db import seed_initial_data
from app.main import app

test_engine = create_async_engine(
    "sqlite+aiosqlite:///./test_cyclone.db",
    connect_args={"check_same_thread": False},
    echo=False
)
TestAsyncSession = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def override_get_db():
    async with TestAsyncSession() as session:
        try:
            yield session
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
async def setup_test_database():
    os.makedirs("./test_data/satellite/raw", exist_ok=True)
    os.makedirs("./test_data/satellite/explainability", exist_ok=True)
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with TestAsyncSession() as db:
        await seed_initial_data(db)
        
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
