from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.pages.cryptocurrency import Cryptocurrency
from app.schemas.cryptocurrency import CryptocurrencyResponse


class CryptocurrencyRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def upsert_many(self, cryptos_data: list[CryptocurrencyResponse]) -> None:
        """Upsert a list of cryptocurrencies into the database."""
        if not cryptos_data:
            return

        values = [crypto.model_dump() for crypto in cryptos_data]

        stmt = insert(Cryptocurrency).values(values)

        # On conflict (duplicate slug), update the fields
        stmt = stmt.on_conflict_do_update(
            index_elements=["slug"],
            set_={
                "id": stmt.excluded.id,
                "name": stmt.excluded.name,
                "symbol": stmt.excluded.symbol,
                "circulating_supply": stmt.excluded.circulating_supply,
                "usd_price": stmt.excluded.usd_price,
                "usd_market_cap": stmt.excluded.usd_market_cap,
            },
        )

        await self._session.execute(stmt)
        await self._session.commit()

    async def get_all(self) -> Sequence[Cryptocurrency]:
        """Get all cryptocurrencies ordered by id."""
        stmt = select(Cryptocurrency).order_by(Cryptocurrency.id)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def search_by_name(self, name_query: str) -> Sequence[Cryptocurrency]:
        """Search cryptocurrencies by name (case-insensitive)."""
        stmt = (
            select(Cryptocurrency)
            .where(Cryptocurrency.name.ilike(f"%{name_query}%"))
            .order_by(Cryptocurrency.id)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
