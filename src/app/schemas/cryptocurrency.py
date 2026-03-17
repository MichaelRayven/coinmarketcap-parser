from pydantic import BaseModel, ConfigDict


class CryptocurrencyResponse(BaseModel):
    id: int
    name: str
    symbol: str
    slug: str
    circulating_supply: float | None
    usd_price: float | None
    usd_market_cap: float | None

    model_config = ConfigDict(from_attributes=True)
