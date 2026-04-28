from app.services.cryptocurrency import CryptocurrencyService
from app.core.dependencies import get_cryptocurrency_service
from fastapi import APIRouter, Depends

from typing import List, Annotated
from app.schemas.cryptocurrency import CryptocurrencyResponse

router = APIRouter(prefix="/api/cryptocurrencies", tags=["cryptocurrencies"])


@router.get("", response_model=List[CryptocurrencyResponse])
async def get_all_cryptocurrencies(
    service: Annotated[CryptocurrencyService, Depends(get_cryptocurrency_service)],
):
    return await service.get_all()


@router.get("/search", response_model=List[CryptocurrencyResponse])
async def search_cryptocurrencies(
    name: str, service: Annotated[CryptocurrencyService, Depends(get_cryptocurrency_service)]
):
    return await service.search_by_name(name)
