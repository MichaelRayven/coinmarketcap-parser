from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Cryptocurrency(Base):
    __tablename__ = "cryptocurrencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    circulating_supply: Mapped[float | None] = mapped_column(Float, nullable=True)
    usd_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    usd_market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
