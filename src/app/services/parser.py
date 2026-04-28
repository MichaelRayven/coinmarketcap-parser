from app.core.lib.utils import parse_currency_amount, normalize_string
import logging
import asyncio
from typing import List

from httpx import AsyncClient
from bs4 import BeautifulSoup

from app.core.config.settings import settings
from app.schemas.cryptocurrency import CryptocurrencyResponse


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CoinMarketCapParser:
    def __init__(self):
        self.base_url = settings.cmc_api_url.rstrip("/")
        self.limit = settings.cmc_limit
        self.concurrency = settings.concurrency
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    def _parse_slugs_from_html(self, html: str, limit: int) -> List[str]:
        """Parses the top-N cryptocurrency slugs from the CMC homepage HTML."""
        soup = BeautifulSoup(html, "html.parser")
        slugs: list[str] = []
        for a_tag in soup.select('a[href^="/currencies/"]'):
            href = str(a_tag.get("href", ""))
            parts = [p for p in href.split("/") if p]
            if len(parts) >= 2 and parts[0] == "currencies":
                slug = parts[1]
                if slug not in slugs and not slug.startswith("coinmarketcap"):
                    slugs.append(slug)
        return slugs[:limit]

    def _parse_coin_from_html(self, html: str, slug: str) -> CryptocurrencyResponse:
        """Parses a single coin's data from its CMC detail page HTML."""
        soup = BeautifulSoup(html, "html.parser")

        # 1. Header Data (Price, Name, Symbol)
        price_el = soup.find(attrs={"data-test": "text-cdp-price-display"})
        usd_price = parse_currency_amount(price_el.text if price_el else None)

        name_el = soup.find(attrs={"data-role": "coin-name"}) or soup.find(
            attrs={"data-test": "coin-name"}
        )
        name_str = name_el.text.strip().replace(" price", "") if name_el else slug.capitalize()

        symbol_el = soup.find(attrs={"data-role": "coin-symbol"})
        symbol_str = symbol_el.text.strip() if symbol_el else slug.upper()

        # 2. Extract Metrics
        metrics_data = {"market cap": 0.0, "circulating_supply": 0.0}

        metric_groups = soup.select('[data-test="section-coin-metrics"] [data-role="group-item"]')
        for group in metric_groups:
            title_el = group.select_one("dt")
            value_el = group.select_one("dd")

            if title_el and value_el:
                title_text = normalize_string(title_el.text)
                # Strip nested elements (like tooltips or secondary values) for cleaner parsing
                value_text = normalize_string(value_el.get_text(separator="/"))

                if "market cap" in title_text and "diluted" not in title_text:
                    metrics_data["market cap"] = parse_currency_amount(value_text) or 0.0
                elif "circulating supply" in title_text:
                    # CMC often puts the BTC/ETH amount first in Circulating Supply
                    metrics_data["circulating_supply"] = parse_currency_amount(value_text) or 0.0

        return CryptocurrencyResponse(
            name=name_str,
            symbol=symbol_str,
            slug=slug,
            circulating_supply=metrics_data["circulating_supply"],
            usd_price=usd_price,
            usd_market_cap=metrics_data["market cap"],
        )

    async def _fetch_slugs(self, client: AsyncClient) -> List[str]:
        """Fetches the top cryptocurrency slugs."""
        response = await client.get(self.base_url)
        response.raise_for_status()
        return self._parse_slugs_from_html(response.text, self.limit)

    async def _fetch_cryptocurrency_data(
        self, client: AsyncClient, slug: str
    ) -> CryptocurrencyResponse:
        """Fetches the information for a single cryptocurrency."""
        coin_url = f"{self.base_url}/currencies/{slug}/"
        response = await client.get(coin_url)
        response.raise_for_status()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._parse_coin_from_html, response.text, slug)

    async def fetch_cryptocurrencies(self) -> List[CryptocurrencyResponse]:
        """Fetches the top cryptocurrencies by parsing coinmarketcap.com HTML."""
        async with AsyncClient(headers=self.headers, timeout=30.0) as client:
            slugs = await self._fetch_slugs(client)
            parsed_coins = []

            slug_chunks = [[] for _ in range(self.concurrency)]
            for idx, slug in enumerate(slugs):
                slug_chunks[idx % self.concurrency].append(slug)

            async def process_slugs(slugs: list[str]):
                try:
                    for slug in slugs:
                        result = await self._fetch_cryptocurrency_data(client, slug)
                        parsed_coins.append(result)
                except Exception as e:
                    logger.error(f"Error fetching {slug}: {e}")

            tasks = [process_slugs(chunk) for chunk in slug_chunks]
            await asyncio.gather(*tasks)

            return parsed_coins
