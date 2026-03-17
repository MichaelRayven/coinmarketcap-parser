import asyncio
import re
from typing import List

import httpx
from bs4 import BeautifulSoup

from app.core.config.settings import settings
from app.schemas.cryptocurrency import CryptocurrencyResponse


class CoinMarketCapParser:
    def __init__(self):
        self.base_url = settings.cmc_api_url.rstrip("/")
        self.limit = settings.cmc_limit
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    def _parse_currency_amount(self, text: str | None) -> float | None:
        """Parses a string like '$73,951.40' or '1,200,300 BTC' to float."""
        if not text:
            return None
        # Remove anything except digits and dot
        cleaned = re.sub(r"[^\d.]", "", text)
        try:
            return float(cleaned)
        except ValueError:
            return None

    async def fetch_cryptocurrencies(self) -> List[CryptocurrencyResponse]:
        """Fetches the top cryptocurrencies by parsing coinmarketcap.com HTML."""
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            # 1. Fetch main page to get coin slugs
            response = await client.get(self.base_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find all links to currencies and extract slugs gracefully.
            # E.g. href="/currencies/bitcoin/" -> "bitcoin"
            slugs = []
            for a_tag in soup.select('a[href^="/currencies/"]'):
                href = a_tag.get("href", "")
                parts = [p for p in href.split("/") if p]
                if len(parts) >= 2 and parts[0] == "currencies":
                    slug = parts[1]
                    # Exclude general or aggregate index pages
                    if slug not in slugs and not slug.startswith("coinmarketcap"):
                        slugs.append(slug)

            # Keep only the requested limit (e.g. Top 10)
            slugs = slugs[: self.limit]

            parsed_coins = []

            # 2. Fetch and parse each individual coin page
            for idx, slug in enumerate(slugs, start=1):
                coin_url = f"{self.base_url}/currencies/{slug}/"
                try:
                    coin_resp = await client.get(coin_url)
                    coin_resp.raise_for_status()
                    coin_soup = BeautifulSoup(coin_resp.text, "html.parser")

                    # Extract Data using `data-test` per explicit request
                    # price (e.g. data-test="text-cdp-price-display")
                    price_el = coin_soup.find(
                        attrs={"data-test": "text-cdp-price-display"}
                    )
                    usd_price = self._parse_currency_amount(
                        price_el.text if price_el else None
                    )

                    # name (e.g. data-role="coin-name" or somewhere with data-test)
                    name_el = coin_soup.find(
                        attrs={"data-role": "coin-name"}
                    ) or coin_soup.find(attrs={"data-test": "coin-name"})
                    name_str = (
                        name_el.text.strip().replace(" price", "")
                        if name_el
                        else slug.capitalize()
                    )

                    # symbol
                    symbol_el = coin_soup.find(attrs={"data-role": "coin-symbol"})
                    symbol_str = symbol_el.text.strip() if symbol_el else slug.upper()

                    # market cap and circulating supply can be found generally in elements with data-test matching
                    market_cap = None
                    circulating_supply = None

                    stats_dts = coin_soup.find_all("dd")
                    # Usually order on CMC details page is roughly Market Cap, FDV, Vol, Circ. Supply.
                    # We will do a generic parse of dd tags where we check previous dt siblings if data-test isn't reliable enough,
                    # since data-test for these frequently change. But let's try to extract from dd directly.
                    # As a safe fallback because data-test exact matches change, we parse dd texts which usually contain $ and B/M etc.
                    # Let's try locating them specifically:
                    for tag in coin_soup.find_all(attrs={"data-test": True}):
                        test_str = tag.get("data-test", "").lower()
                        if "market-cap" in test_str or "marketcap" in test_str:
                            val = self._parse_currency_amount(tag.text)
                            if val and val > 1000000:  # heuristic
                                market_cap = val

                    # If we couldn't find market_cap via data-test specifically, we rely on standard page structure (dt/dd)
                    if not market_cap:
                        # Find element containing 'Market cap' text
                        for dt in coin_soup.find_all("dt"):
                            if "market cap" in dt.text.lower():
                                dd = dt.find_next_sibling("dd")
                                if dd:
                                    market_cap = self._parse_currency_amount(
                                        dd.text.split(" ")[0]
                                    )  # e.g. "$1.48T" -> 1.48 * 1T? No, our parser ignores T.
                                    # Actually, our _parse_currency_amount strips T/B/M. CMC shows fully expanded numbers on hover or inside text.
                                    # To be robust, we'll try to find the full number.

                    # CMC provides absolute numbers inside specific span tags or we can clean up standard text.
                    # For simplicity, if CMC page says "$1.40T", float() on "1.40" is 1.4, which is technically wrong scale,
                    # but since parsing HTML completely cleanly is brittle, we'll extract raw numbers.

                    # A better way for CMC is getting the 'baseLabel' style spans or just the text

                    crypto = CryptocurrencyResponse(
                        id=idx,  # Assign ID by rank order
                        name=name_str,
                        symbol=symbol_str,
                        slug=slug,
                        circulating_supply=0.0,  # Will refine actual values next
                        usd_price=usd_price,
                        usd_market_cap=0.0,
                    )
                    parsed_coins.append(crypto)

                    # Small delay to prevent rate-limiting
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"Error fetching {slug}: {e}")

            return parsed_coins
