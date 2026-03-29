#!/usr/bin/env python3
"""
Craigslist Scraper - Pulls listings from SF Bay Area Craigslist
Focuses on for-sale section, sorted by newest
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# Craigslist SF Bay Area base
BASE_URL = "https://sfbay.craigslist.org"

CATEGORY_MAP = {
    "electronics": "ela",
    "phones": "moa",
    "computers": "sya",
    "furniture": "fua",
    "tools": "tla",
    "bikes": "bia",
    "general": "sss",  # All for sale
}


def parse_price(price_str: str) -> float:
    """Extract numeric price."""
    if not price_str:
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def scrape_craigslist(search_term: str, max_price: float = None, 
                      category: str = "general", max_results: int = 30) -> list:
    """
    Scrape Craigslist SF Bay Area listings.
    Returns list of listing dicts.
    """
    cat_code = CATEGORY_MAP.get(category.lower(), "sss")
    encoded = quote_plus(search_term)
    
    url = f"{BASE_URL}/search/{cat_code}?query={encoded}&sort=date&srchType=A"
    
    if max_price:
        url += f"&max_price={int(max_price)}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  Craigslist request failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    listings = []

    # New CL layout uses cl-search-result
    items = soup.select("li.cl-search-result, div.result-row")

    for item in items[:max_results]:
        try:
            # Title
            title_el = item.select_one("a.cl-app-anchor, a.result-title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            item_url = title_el.get("href", "")
            if item_url and not item_url.startswith("http"):
                item_url = BASE_URL + item_url

            # Price
            price_el = item.select_one(".priceinfo, .result-price")
            price = parse_price(price_el.get_text(strip=True)) if price_el else 0.0

            if price <= 0:
                continue

            # Location
            loc_el = item.select_one(".meta, .result-hood")
            location_text = loc_el.get_text(strip=True) if loc_el else "SF Bay Area"
            # Clean up location
            location_text = location_text.strip("() ").split("·")[0].strip()

            # Date
            date_el = item.select_one("time")
            date_text = date_el.get("datetime", "") if date_el else ""

            listings.append({
                "title": title,
                "price": price,
                "condition": "Used",  # CL doesn't always specify
                "location": location_text or "SF Bay Area",
                "platform": "craigslist",
                "url": item_url,
                "description": title,  # Full desc requires another request
                "date": date_text,
            })

        except Exception:
            continue

    return listings


def get_listing_detail(url: str) -> dict:
    """
    Fetch the full description from a Craigslist listing page.
    Returns { description, condition, images_count }.
    """
    try:
        time.sleep(0.5)  # Be polite
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception:
        return {}

    soup = BeautifulSoup(resp.text, "lxml")

    # Description
    desc_el = soup.select_one("#postingbody, section.body")
    description = ""
    if desc_el:
        description = desc_el.get_text(separator=" ", strip=True)
        description = re.sub(r'\s+', ' ', description)[:800]

    # Condition from attributes
    condition = "Used"
    attrs = soup.select(".attrgroup span")
    for attr in attrs:
        text = attr.get_text(strip=True).lower()
        if "condition" in text or "like new" in text or "excellent" in text:
            condition = attr.get_text(strip=True)
            break

    # Image count
    images = soup.select(".slide img")

    return {
        "description": description,
        "condition": condition,
        "images_count": len(images),
    }


if __name__ == "__main__":
    print("Testing Craigslist scraper...")
    listings = scrape_craigslist("iPhone 14 Pro", max_price=600, category="phones", max_results=10)
    print(f"\nFound {len(listings)} listings:")
    for l in listings:
        print(f"  ${l['price']:>6} | {l['location']:<20} | {l['title'][:50]}")
        print(f"           URL: {l['url']}")
