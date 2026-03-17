from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.database import AsyncSessionLocal
from app.services.parser import CoinMarketCapParser
from app.repositories.cryptocurrency import CryptocurrencyRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: parse and populate DB
    parser = CoinMarketCapParser()
    try:
        print("Fetching cryptocurrencies from CoinMarketCap...")
        cryptos = await parser.fetch_cryptocurrencies()
        print(f"Fetched {len(cryptos)} cryptocurrencies. Saving to DB...")

        async with AsyncSessionLocal() as session:
            repo = CryptocurrencyRepository(session)
            await repo.upsert_many(cryptos)

        print("Successfully saved populated cryptocurrencies.")
    except Exception as e:
        print(f"Error during parsing startup: {e}")

    yield
    # Shutdown
    pass


app = FastAPI(
    title="CoinMarketCap Parser",
    description="Parser and API for cryptocurrency data",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
