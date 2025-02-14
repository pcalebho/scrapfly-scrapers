"""
This is an example web scraper for Walmart.com.

To run this scraper set env variable $SCRAPFLY_KEY with your scrapfly API key:
$ export $SCRAPFLY_KEY="your key from https://scrapfly.io/dashboard"
"""

import os
import json
import math
from typing import Dict, List, TypedDict
from urllib.parse import urlencode
from loguru import logger as log
from scrapfly import ScrapeConfig, ScrapflyClient, ScrapeApiResponse

SCRAPFLY = ScrapflyClient(key=os.environ["SCRAPFLY_KEY"])

BASE_CONFIG = {
    # bypass walmart.com web scraping blocking
    "asp": True,
    # set the proxy country to US
    "country": "US",
    "proxy_pool": "public_residential_pool"
}


def parse_product(response: ScrapeApiResponse):
    """parse product data from walmart product pages"""
    sel = response.selector
    data = sel.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
    data = json.loads(data)
    _product_raw = data["props"]["pageProps"]["initialData"]["data"]["product"]
    # There's a lot of product data, including private meta keywords, so we need to do some filtering:
    wanted_product_keys = [
        "averageRating",
        "brand",
        "id",
        "imageInfo",
        "manufacturerName",
        "name",
        "priceInfo",
        "shortDescription",
        "type",
    ]
    product = {k: v for k, v in _product_raw.items() if k in wanted_product_keys}
    reviews_raw = data["props"]["pageProps"]["initialData"]["data"]["reviews"]
    return {"product": product, "reviews": reviews_raw}


def parse_search(response: ScrapeApiResponse) -> Dict:
    """parse refined product listing data from search pages"""
    sel = response.selector
    data = sel.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
    data = json.loads(data)

    # Check if there are any item stacks before accessing them
    item_stacks = data["props"]["pageProps"]["initialData"].get("searchResult", {}).get("itemStacks", [])
    if not item_stacks:
        return {"results": [], "total_results": 0}

    total_results = item_stacks[0].get("count", 0)
    results = item_stacks[0].get("items", [])

    # Define the keys we want to keep for each product
    wanted_search_keys = [
        "id",
        "usItemId",
        "name",
        "type",
        "imageInfo",
        "canonicalUrl",
        "salesUnitType",
        "sellerId",
        "sellerName",
        "averageRating",
        "numberOfReviews"
    ]

    # Filter each product to only include the desired keys
    refined_results = []
    for item in results:
        refined_item = {k: v for k, v in item.items() if k in wanted_search_keys}
        refined_results.append(refined_item)

    return {"results": refined_results, "total_results": total_results}


async def scrape_products(urls: List[str]) -> List[Dict]:
    """scrape product data from product pages"""
    # add the product pages to a scraping list
    result = []
    to_scrape = [ScrapeConfig(url, **BASE_CONFIG) for url in urls]
    async for response in SCRAPFLY.concurrent_scrape(to_scrape):
        result.append(parse_product(response))
    log.success(f"scraped {len(result)} product pages")
    return result


async def scrape_search(
    query: str = "",
    sort: TypedDict(
        "SortOptions",
        {"best_seller": str, "best_match": str, "price_low": str, "price_high": str},
    ) = "best_match",
    max_pages: int = None,
):
    """scrape single walmart search page"""

    def make_search_url(page):
        url = "https://www.walmart.com/search?" + urlencode(
            {
                "q": query,
                "page": page,
                sort: sort,
                "affinityOverride": "default",
            }
        )
        return url

    # scrape the first search page
    log.info(f"scraping the first search page with the query ({query})")
    first_page = await SCRAPFLY.async_scrape(
        ScrapeConfig(make_search_url(1), render_js=True, **BASE_CONFIG)
    )
    data = parse_search(first_page)
    search_data = data["results"]
    total_results = data["total_results"]

    # find total page count to scrape
    total_pages = math.ceil(total_results / 40) if total_results else 0
    total_pages = min(total_pages, 25)  # Walmart's limit
    if max_pages:
        total_pages = min(max_pages, total_pages)

    if total_pages <= 1:
        return search_data

    # then add the remaining pages to a scraping list and scrape them concurrently
    log.info(f"scraping search pagination, remaining ({total_pages - 1}) more pages")
    other_pages = [
        ScrapeConfig(make_search_url(page), **BASE_CONFIG)
        for page in range(2, total_pages + 1)
    ]
    async for response in SCRAPFLY.concurrent_scrape(other_pages):
        search_data.extend(parse_search(response)["results"])
    log.success(f"scraped {len(search_data)} product listings from search pages")
    return search_data
