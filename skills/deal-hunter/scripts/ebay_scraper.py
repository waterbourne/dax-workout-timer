#!/usr/bin/env python3
"""
eBay Scraper - Pulls real listings from eBay search results
Focuses on Buy It Now + auction listings sorted by newest
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def parse_price(price_str: str) -> float:
    """Extract numeric price from string like '$399.99' or '$1,200.00'."""
    if not price_str:
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def scrape_ebay(search_term: str, max_price: float = None, condition: str = None, max_results: int = 30) -> list:
    """
    Scrape eBay listings for a search term.
    Returns list of listing dicts.
    """
    encoded = quote_plus(search_term)
    
    # Build URL - sorted by newly listed, Buy It Now
    url = f"https://www.ebay.com/sch/i.html?_nkw={encoded}&_sop=10&LH_BIN=1"
    
    if max_price:
        url += f"&_udhi={max_price}"
    
    if condition:
        condition_map = {"new": "1000", "open_box": "1500", "used": "3000"}
        code = condition_map.get(condition.lower())
        if code:
            url += f"&LH_ItemCondition={code}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  eBay request failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    listings = []

    # eBay listing items
    items = soup.select("li.s-item")
    
    for item in items[:max_results]:
        try:
            # Title
            title_el = item.select_one(".s-item__title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if title.lower() == "shop on ebay":
                continue

            # Price
            price_el = item.select_one(".s-item__price")
            price_str = price_el.get_text(strip=True) if price_el else ""
            # Handle price ranges (take lower)
            if "to" in price_str.lower():
                price_str = price_str.split("to")[0]
            price = parse_price(price_str)
            if price <= 0:
                continue

            # Condition
            cond_el = item.select_one(".SECONDARY_INFO")
            condition_text = cond_el.get_text(strip=True) if cond_el else "Unknown"

            # Location
            loc_el = item.select_one(".s-item__location")
            location = loc_el.get_text(strip=True).replace("from ", "") if loc_el else "Unknown"

            # URL
            link_el = item.select_one("a.s-item__link")
            item_url = link_el["href"].split("?")[0] if link_el else ""

            # Shipping
            ship_el = item.select_one(".s-item__shipping")
            shipping_text = ship_el.get_text(strip=True) if ship_el else ""
            shipping_cost = 0.0
            if "free" in shipping_text.lower():
                shipping_cost = 0.0
            else:
                ship_match = re.search(r'\$[\d.]+', shipping_text)
                if ship_match:
                    shipping_cost = parse_price(ship_match.group())

            listings.append({
                "title": title,
                "price": price,
                "condition": condition_text,
                "location": location,
                "shipping": shipping_cost,
                "platform": "ebay",
                "url": item_url,
                "description": title,  # eBay doesn't show description in search
            })

        except Exception:
            continue

    return listings


def scrape_ebay_sold(search_term: str, max_results: int = 20) -> list:
    """
    Scrape eBay SOLD listings to get real market comps.
    Returns list of {title, price, date_sold}.
    """
    encoded = quote_plus(search_term)
    url = f"https://www.ebay.com/sch/i.html?_nkw={encoded}&LH_Sold=1&LH_Complete=1&_sop=13"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  eBay sold request failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    sold = []

    for item in soup.select("li.s-item")[:max_results]:
        try:
            title_el = item.select_one(".s-item__title")
            if not title_el or "shop on ebay" in title_el.get_text(strip=True).lower():
                continue
            
            price_el = item.select_one(".s-item__price")
            if not price_el:
                continue
            
            price = parse_price(price_el.get_text(strip=True))
            if price <= 0:
                continue

            date_el = item.select_one(".s-item__title--tag")
            date_text = date_el.get_text(strip=True) if date_el else ""

            sold.append({
                "title": title_el.get_text(strip=True),
                "price": price,
                "date": date_text,
            })
        except Exception:
            continue

    return sold


def get_market_value_from_sold(search_term: str) -> dict:
    """
    Calculate market value from eBay sold comps.
    Returns { low, median, high, sample_size }.
    """
    sold = scrape_ebay_sold(search_term)
    
    if not sold:
        return {"low": None, "median": None, "high": None, "sample_size": 0}
    
    prices = sorted([s["price"] for s in sold])
    
    # Remove outliers (top/bottom 10%)
    trim = max(1, len(prices) // 10)
    trimmed = prices[trim:-trim] if len(prices) > 5 else prices
    
    mid = len(trimmed) // 2
    median = trimmed[mid] if trimmed else 0
    
    return {
        "low": min(trimmed) if trimmed else 0,
        "median": median,
        "high": max(trimmed) if trimmed else 0,
        "sample_size": len(sold),
    }


if __name__ == "__main__":
    print("Testing eBay scraper...")
    listings = scrape_ebay("iPhone 14 Pro", max_price=600, condition="used", max_results=10)
    print(f"\nFound {len(listings)} listings:")
    for l in listings:
        print(f"  ${l['price']:>6} | {l['condition']:<15} | {l['title'][:50]}")
    
    print("\n\nTesting sold comps for 'iPhone 14 Pro'...")
    mv = get_market_value_from_sold("iPhone 14 Pro 256GB used")
    print(f"Market value: ${mv['low']} - ${mv['median']} (median) - ${mv['high']} | {mv['sample_size']} comps")
