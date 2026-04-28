from app.repositories.cryptocurrency import CryptocurrencyRepository


class CryptocurrencyService:
    def __init__(self, repository: CryptocurrencyRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def search_by_name(self, name: str):
        return await self.repository.search_by_name(name)
