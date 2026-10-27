import pytest_asyncio
from services.api.app.core.database import Base, engine
from services.api.seed.seed_data import seed
from services.api.seed.seed_demo_agency import seed_demo_agency


@pytest_asyncio.fixture(autouse=True, scope="session")
async def init_test_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed()
    await seed_demo_agency()
