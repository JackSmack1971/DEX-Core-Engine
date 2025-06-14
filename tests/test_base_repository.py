import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from database.models import Base
from database.repositories.base import BaseRepository


class Item(Base):
    __tablename__ = "item"
    name: Mapped[str] = mapped_column(String(50))


class ItemRepository(BaseRepository):
    async def add(self, item: Item) -> None:
        self._session.add(item)
        await self._session.commit()

    async def get(self, item_id) -> Item | None:
        return await self._session.get(Item, item_id)

    async def update_name(self, item: Item, name: str) -> None:
        item.name = name
        await self._session.commit()

    async def delete(self, item: Item) -> None:
        await self._session.delete(item)
        await self._session.commit()


@pytest.mark.asyncio
async def test_item_repository_crud() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session_maker() as session:
        repo = ItemRepository(session)
        item = Item(name="foo")
        await repo.add(item)
        fetched = await repo.get(item.id)
        assert fetched is not None and fetched.name == "foo"
        await repo.update_name(fetched, "bar")
        assert (await repo.get(item.id)).name == "bar"
        await repo.delete(fetched)
        assert await repo.get(item.id) is None


