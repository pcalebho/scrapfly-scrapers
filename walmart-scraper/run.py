"""
This example run script shows how to run the Walmart.com scraper defined in ./walmart.py
It scrapes product data and saves it to ./results/

To run this script set the env variable $SCRAPFLY_KEY with your scrapfly API key:
$ export $SCRAPFLY_KEY="your key from https://scrapfly.io/dashboard"
"""

import asyncio
import json
from pathlib import Path
import walmart

output = Path(__file__).parent / "results"
output.mkdir(exist_ok=True)

query = [
  "fruits",
  "Vegetables",
  "Dairy",
  "Meat",
  "seafood",
  "Frozen foods",
  "Baked goods",
  "Snacks",
  "Beverages",
  "rice", 
  "pasta", 
  "flour", 
  "sugar", 
  "oils", 
  "canned goods",
  "Condiments",
  "Spices",
  "Cleaning supplies",
  "Paper products",
  "Trash bags",
  "Laundry essentials",
  "Oral care",
  "Hair care",
  "Skincare",
  "Deodorants",
  "Feminine hygiene products",
  "Shaving essentials",
  "Health and wellness",
  "Baby food",
  "Diapers& wipes",
  "Baby snacks and cereals",
  "Baby care items",
  "Pet food",
  "Coffee",
  "Tea",
  "Instant noodles and soups",
  "candy"
]


async def run():
    # enable scrapfly cache for basic use
    walmart.BASE_CONFIG["cache"] = False

    print("running Walmart scrape and saving results to ./results directory")

    products_data = await walmart.scrape_products(
        urls=[
        ]
    )
    with open(output.joinpath("products.json"), "w", encoding="utf-8") as file:
        json.dump(products_data, file, indent=2, ensure_ascii=False)

    for q in query:
        search_data = await walmart.scrape_search(
            query=q, sort="best_seller", max_pages=25
        )
        filename = f"{q}.json".replace(" ", "_")
        with open(output.joinpath(filename), "w", encoding="utf-8") as file:
            json.dump(search_data, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(run())
