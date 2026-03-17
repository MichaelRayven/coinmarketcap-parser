from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.schemas.cryptocurrency import CryptocurrencyResponse
from app.services.repository import CryptocurrencyRepository

router = APIRouter(prefix="/api/cryptocurrencies", tags=["cryptocurrencies"])


@router.get("", response_model=List[CryptocurrencyResponse])
async def get_all_cryptocurrencies(session: AsyncSession = Depends(get_session)):
    repo = CryptocurrencyRepository(session)
    return await repo.get_all()


@router.get("/search", response_model=List[CryptocurrencyResponse])
async def search_cryptocurrencies(
    name: str, session: AsyncSession = Depends(get_session)
):
    repo = CryptocurrencyRepository(session)
    return await repo.search_by_name(name)
