"""Scraper utilities for fetching product listings from online retailers."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/118.0.0.0 Safari/537.36"
)
DEFAULT_HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Cache-Control": "no-cache",
    }
)


@dataclass
class RawListing:
    store: str
    name: str
    price: float
    link: str


def _clean_price(raw_price: Optional[str]) -> Optional[float]:
    if not raw_price:
        return None
    match = re.search(r"(\d+[.,]?\d*)", raw_price.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _safe_request(
    url: str,
    params: Optional[dict] = None,
    *,
    retries: int = 3,
    backoff_seconds: float = 1.0,
) -> Optional[str]:
    for attempt in range(1, retries + 1):
        try:
            response = SESSION.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            logging.warning(
                "Failed to fetch %s (attempt %s/%s): %s", url, attempt, retries, exc
            )
            if attempt < retries:
                sleep_for = backoff_seconds * attempt
                time.sleep(sleep_for)
    return None


def _amazon_parser(soup: BeautifulSoup, limit: int) -> List[RawListing]:
    results: List[RawListing] = []
    for node in soup.select("div.s-main-slot div[data-component-type='s-search-result']"):
        name_tag = node.select_one("h2 a span")
        price_tag = node.select_one("span.a-offscreen")
        link_tag = node.select_one("h2 a")

        if not (name_tag and price_tag and link_tag):
            continue

        price = _clean_price(price_tag.get_text())
        if price is None:
            continue

        listing = RawListing(
            store="Amazon",
            name=name_tag.get_text(strip=True),
            price=price,
            link=f"https://www.amazon.com{link_tag.get('href')}",
        )
        results.append(listing)
        if len(results) >= limit:
            break
    return results


def _walmart_parser(soup: BeautifulSoup, limit: int) -> List[RawListing]:
    results: List[RawListing] = []
    nodes: Iterable = soup.select("div[data-item-id]")
    for node in nodes:
        name_tag = node.select_one("a.product-title-link span") or node.select_one("span.lh-title")
        price_tag = node.select_one("span.price-main span[aria-hidden='true']") or node.select_one(
            "div[data-automation-id='product-price']"
        )
        link_tag = node.select_one("a.product-title-link") or node.select_one("a.absolute")

        if not (name_tag and price_tag and link_tag):
            continue

        price = _clean_price(price_tag.get_text())
        if price is None:
            continue

        href = link_tag.get("href", "")
        link = href if href.startswith("http") else f"https://www.walmart.com{href}"

        listing = RawListing(
            store="Walmart",
            name=name_tag.get_text(strip=True),
            price=price,
            link=link,
        )
        results.append(listing)
        if len(results) >= limit:
            break
    return results


def _bestbuy_parser(soup: BeautifulSoup, limit: int) -> List[RawListing]:
    results: List[RawListing] = []
    for node in soup.select("li.sku-item"):
        name_tag = node.select_one("h4.sku-header a")
        price_tag = node.select_one("div.priceView-hero-price span[aria-hidden='true']") or node.select_one(
            "div.priceView-customer-price span"
        )
        link_tag = name_tag

        if not (name_tag and price_tag and link_tag):
            continue

        price = _clean_price(price_tag.get_text())
        if price is None:
            continue

        link = link_tag.get("href", "")
        if link and not link.startswith("http"):
            link = f"https://www.bestbuy.com{link}"

        results.append(
            RawListing(
                store="Best Buy",
                name=name_tag.get_text(strip=True),
                price=price,
                link=link,
            )
        )
        if len(results) >= limit:
            break
    return results


def _newegg_parser(soup: BeautifulSoup, limit: int) -> List[RawListing]:
    results: List[RawListing] = []
    for node in soup.select("div.item-cell"):
        name_tag = node.select_one("a.item-title")
        price_tag = node.select_one("li.price-current strong")
        price_cent = node.select_one("li.price-current sup")
        link_tag = name_tag

        if not (name_tag and price_tag and link_tag):
            continue

        price_text = price_tag.get_text()
        if price_cent:
            price_text += price_cent.get_text()
        price = _clean_price(price_text)
        if price is None:
            continue

        results.append(
            RawListing(
                store="Newegg",
                name=name_tag.get_text(strip=True),
                price=price,
                link=name_tag.get("href", ""),
            )
        )
        if len(results) >= limit:
            break
    return results


def _generic_search(
    query: str,
    *,
    url: str,
    params: Optional[dict],
    parser: Callable[[BeautifulSoup, int], List[RawListing]],
    limit: int,
) -> List[RawListing]:
    html = _safe_request(url, params=params)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    return parser(soup, limit)


def search_amazon(query: str, limit: int = 5) -> List[RawListing]:
    params = {"k": query}
    return _generic_search(
        query,
        url="https://www.amazon.com/s",
        params=params,
        parser=_amazon_parser,
        limit=limit,
    )


def search_walmart(query: str, limit: int = 5) -> List[RawListing]:
    params = {"q": query}
    return _generic_search(
        query,
        url="https://www.walmart.com/search",
        params=params,
        parser=_walmart_parser,
        limit=limit,
    )


def search_bestbuy(query: str, limit: int = 5) -> List[RawListing]:
    params = {"st": query}
    return _generic_search(
        query,
        url="https://www.bestbuy.com/site/searchpage.jsp",
        params=params,
        parser=_bestbuy_parser,
        limit=limit,
    )


def search_newegg(query: str, limit: int = 5) -> List[RawListing]:
    params = {"d": query}
    return _generic_search(
        query,
        url="https://www.newegg.com/p/pl",
        params=params,
        parser=_newegg_parser,
        limit=limit,
    )


STORE_SEARCHERS: List[Callable[[str, int], List[RawListing]]] = [
    search_amazon,
    search_walmart,
    search_bestbuy,
    search_newegg,
]


def fetch_all(query: str, limit_per_store: int = 5) -> List[RawListing]:
    listings: List[RawListing] = []
    for searcher in STORE_SEARCHERS:
        try:
            listings.extend(searcher(query, limit_per_store))
        except Exception as exc:  # pragma: no cover - defensive
            logging.exception("Failed to scrape via %s: %s", searcher.__name__, exc)
    return listings

