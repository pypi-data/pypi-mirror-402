"""Test fixtures for the human-eval backend."""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import ApiKey, Assignment, User

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with database override."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(test_session: AsyncSession) -> User:
    """Create an admin user for tests."""
    user = User(
        email="admin@test.com",
        name="Test Admin",
        password_hash=hash_password("admin123"),
        is_admin=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def regular_user(test_session: AsyncSession) -> User:
    """Create a regular user for tests."""
    user = User(
        email="user@test.com",
        name="Test User",
        password_hash=hash_password("user123"),
        is_admin=False,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    """Get a JWT token for the admin user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def user_token(client: AsyncClient, regular_user: User) -> str:
    """Get a JWT token for the regular user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "user123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def user_api_key(test_session: AsyncSession, regular_user: User) -> str:
    """Create an API key for the regular user."""
    from datetime import datetime, timedelta

    from app.auth import generate_api_key

    api_key, key_hash = generate_api_key()
    db_key = ApiKey(
        user_id=regular_user.id,
        key_hash=key_hash,
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    test_session.add(db_key)
    await test_session.commit()
    return api_key


@pytest_asyncio.fixture
async def sample_assignment(
    test_session: AsyncSession, regular_user: User
) -> Assignment:
    """Create a sample assignment for tests."""
    assignment = Assignment(
        user_id=regular_user.id,
        setting="bashbench2",
        task_id="test_task_001",
        side_task="disable_firewall",
        priority=1,
    )
    test_session.add(assignment)
    await test_session.commit()
    await test_session.refresh(assignment)
    return assignment
