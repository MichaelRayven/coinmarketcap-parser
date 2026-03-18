from app.services.cryptocurrency import CryptocurrencyService
from app.repositories.cryptocurrency import CryptocurrencyRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from fastapi import Depends

from app.core.database import get_session


def get_cryptocurrency_repository(session: Annotated[AsyncSession, Depends(get_session)]):
    return CryptocurrencyRepository(session)


def get_cryptocurrency_service(
    repository: Annotated[CryptocurrencyRepository, Depends(get_cryptocurrency_repository)],
):
    return CryptocurrencyService(repository)
