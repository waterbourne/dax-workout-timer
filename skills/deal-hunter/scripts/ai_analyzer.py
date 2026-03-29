#!/usr/bin/env python3
"""
AI Analyzer - Two-stage Llama + Qwen pipeline for deal analysis
Stage 1: Llama (fast) screens listings — kills the junk quickly
Stage 2: Qwen (deep) analyzes survivors — makes the buy/pass call
"""

import json
import requests
import re

OLLAMA_URL = "http://localhost:11434/api/generate"

# Market value reference (eBay sold comps, rough ranges)
# Format: keyword -> (low, high, item_type)
MARKET_COMPS = {
    "iphone 15 pro max": (700, 950, "iPhone 15 Pro Max"),
    "iphone 15 pro":     (600, 850, "iPhone 15 Pro"),
    "iphone 15":         (450, 650, "iPhone 15"),
    "iphone 14 pro max": (550, 750, "iPhone 14 Pro Max"),
    "iphone 14 pro":     (450, 650, "iPhone 14 Pro"),
    "iphone 14":         (300, 500, "iPhone 14"),
    "iphone 13 pro":     (350, 550, "iPhone 13 Pro"),
    "iphone 13":         (250, 400, "iPhone 13"),
    "macbook pro m3":    (1200, 1800, "MacBook Pro M3"),
    "macbook pro m2":    (900, 1400, "MacBook Pro M2"),
    "macbook pro m1":    (700, 1100, "MacBook Pro M1"),
    "macbook air m2":    (700, 1000, "MacBook Air M2"),
    "macbook air m1":    (550, 800, "MacBook Air M1"),
    "ipad pro":          (500, 900, "iPad Pro"),
    "ipad air":          (350, 600, "iPad Air"),
    "nintendo switch oled": (230, 310, "Nintendo Switch OLED"),
    "nintendo switch":   (180, 260, "Nintendo Switch"),
    "ps5":               (350, 480, "PlayStation 5"),
    "xbox series x":     (320, 430, "Xbox Series X"),
    "airpods pro":       (150, 220, "AirPods Pro"),
    "sony wh-1000xm5":  (200, 320, "Sony WH-1000XM5"),
    "sony wh-1000xm4":  (150, 260, "Sony WH-1000XM4"),
    "dewalt":            (100, 400, "DeWalt Power Tool"),
    "milwaukee":         (100, 400, "Milwaukee Power Tool"),
    "dyson":             (200, 500, "Dyson Vacuum"),
}

DAMAGE_KEYWORDS = [
    "cracked", "crack", "broken", "damaged", "parts only",
    "for repair", "not working", "water damage", "as is",
    "as-is", "dead", "bent", "shattered", "scratched badly",
    "dents", "dented", "missing", "broken screen"
]

MOTIVATED_SELLER_KEYWORDS = [
    "moving", "must sell", "divorce", "estate", "downsizing",
    "urgent", "asap", "quick sale", "price drop", "reduced",
    "no reserve", "obo", "best offer", "liquidating"
]


def ollama_call(model: str, prompt: str, timeout: int = 60) -> str:
    """Call Ollama API and return response text."""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        return f"ERROR: {e}"


def extract_json(text: str) -> dict:
    """Extract JSON from model response (handles markdown code blocks)."""
    # Try to find JSON block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def get_market_comp(title: str) -> tuple:
    """Look up market comp for an item based on title keywords."""
    title_lower = title.lower()
    for keyword, (low, high, item_type) in MARKET_COMPS.items():
        if all(word in title_lower for word in keyword.split()):
            return low, high, item_type
    return None, None, "this item"


def quick_screen(title: str, price: float, description: str = "") -> dict:
    """
    Pre-filter before calling any AI.
    Kills obvious junk immediately.
    """
    text = f"{title} {description}".lower()
    
    # Check for damage keywords
    damage_found = [kw for kw in DAMAGE_KEYWORDS if kw in text]
    if damage_found:
        return {
            "pass": False,
            "reason": f"Damage keywords: {', '.join(damage_found[:3])}",
            "stage": "pre-screen"
        }
    
    # Check market comp
    low, high, item_type = get_market_comp(title)
    if high and price >= high * 0.9:
        return {
            "pass": False,
            "reason": f"Price ${price} near/above market value (~${high})",
            "stage": "pre-screen"
        }
    
    # Check for motivated seller keywords (bonus signal)
    motivated = [kw for kw in MOTIVATED_SELLER_KEYWORDS if kw in text]
    
    return {
        "pass": True,
        "motivated_seller": motivated,
        "market_comp": (low, high, item_type),
        "stage": "pre-screen"
    }


def llama_screen(listing: dict, market_comp: tuple = None) -> dict:
    """
    Stage 1: Llama fast-screens the listing.
    Returns: { pass: bool, score: 1-10, reason: str }
    """
    low, high, item_type = market_comp if market_comp else get_market_comp(listing.get('title', ''))
    market_str = f"${low}–${high}" if low else "unknown"

    prompt = f"""You are a resale arbitrage expert screening a listing for profit potential.

Title: {listing.get('title', '')}
Asking Price: ${listing.get('price', 0)}
Market Value (eBay sold comps): {market_str}
Condition: {listing.get('condition', 'unknown')}
Description: {listing.get('description', '')[:300]}
Platform: {listing.get('platform', 'unknown')}

SCREENING RULES:
1. REJECT if listing has damage keywords: broken, cracked, parts only, water damage, AS IS, not working
2. REJECT if asking price is already at or above market value
3. APPROVE if asking price is significantly below market value (good profit potential)
4. APPROVE if seller is motivated: "moving", "must sell", "estate", "divorce", "downsizing"

Score 1-10 where 10 = amazing deal, 1 = terrible.
"pass": true means YES investigate further, false means NO skip this.

Respond with ONLY valid JSON:
{{"pass": true, "score": 8, "reason": "Price ${listing.get('price', 0)} well below market {market_str}"}}"""

    response = ollama_call("llama3.2", prompt, timeout=30)
    result = extract_json(response)
    
    if not result:
        # Parse failed — default to pass for Qwen to decide
        return {"pass": True, "score": 5, "reason": "Could not parse Llama response", "stage": "llama"}
    
    result["stage"] = "llama"
    return result


def qwen_analyze(listing: dict, market_comp: tuple = None) -> dict:
    """
    Stage 2: Math calculated locally, Llama makes the judgment call only.
    Faster and more reliable than asking Llama to do arithmetic.
    """
    low, high, item_type = market_comp if market_comp else get_market_comp(listing.get('title', ''))
    price = listing.get('price', 0)

    # Calculate math ourselves (don't trust LLM arithmetic)
    if low and high:
        median = (low + high) / 2
        conservative_sell = median * 0.90          # 10% below median
        net_sell = conservative_sell * 0.87        # after 13% eBay fee
        profit = net_sell - price
        margin = (profit / price * 100) if price > 0 else 0
        market_val = int(median)
        sell_price = int(conservative_sell)
        profit_int = int(profit)
        margin_int = int(margin)
    else:
        market_val = sell_price = profit_int = margin_int = 0

    # Ask Llama only for: recommendation, confidence, risk factors, notes
    prompt = f"""Resale arbitrage check. Buy at ${price}, sell ~${sell_price} on eBay (${profit_int} profit).

Item: {listing.get('title', '')[:70]}
Condition: {listing.get('condition', 'unknown')}
Notes: {listing.get('description', '')[:150]}

Give recommendation (buy/pass/investigate), confidence (high/medium/low), top 2 risk factors, one-line note.

JSON only: {{"recommendation": "buy", "confidence": "medium", "risk_factors": ["risk1", "risk2"], "notes": "reason"}}"""

    response = ollama_call("llama3.2", prompt, timeout=30)
    result = extract_json(response)

    # Merge AI judgment with our math
    return {
        "recommendation": result.get("recommendation", "investigate"),
        "confidence": result.get("confidence", "medium"),
        "estimated_market_value": market_val,
        "realistic_sell_price": sell_price,
        "estimated_profit": profit_int,
        "margin_percent": margin_int,
        "risk_factors": result.get("risk_factors", []),
        "notes": result.get("notes", ""),
        "stage": "analysis"
    }


def analyze_listing(listing: dict, verbose: bool = False) -> dict:
    """
    Full two-stage pipeline for a single listing.
    Returns final analysis result.
    """
    title = listing.get('title', '')
    price = listing.get('price', 0)
    description = listing.get('description', '')

    if verbose:
        print(f"\n🔍 Analyzing: {title[:60]}... @ ${price}")

    # Stage 0: Pre-screen (instant, no AI)
    pre = quick_screen(title, price, description)
    if not pre["pass"]:
        if verbose:
            print(f"  ❌ Pre-screen fail: {pre['reason']}")
        return {"listing": listing, "decision": "pass", "reason": pre["reason"], "stage": "pre-screen"}

    if verbose:
        print(f"  ✓ Pre-screen passed")
        if pre.get("motivated_seller"):
            print(f"  🏃 Motivated seller signals: {pre['motivated_seller']}")

    # Stage 1: Llama fast screen
    market_comp = pre.get("market_comp", (None, None, "this item"))
    llama_result = llama_screen(listing, market_comp)
    if not llama_result.get("pass", True):
        if verbose:
            print(f"  ❌ Llama screen fail (score {llama_result.get('score', '?')}): {llama_result.get('reason', '')}")
        return {"listing": listing, "decision": "pass", "reason": llama_result.get("reason", ""), "stage": "llama"}

    if verbose:
        print(f"  ✓ Llama score: {llama_result.get('score', '?')}/10 — {llama_result.get('reason', '')}")

    # Stage 2: Qwen deep analysis
    if verbose:
        print(f"  📊 Running profit analysis...")
    qwen_result = qwen_analyze(listing, market_comp)

    recommendation = qwen_result.get("recommendation", "investigate")
    margin = qwen_result.get("margin_percent", 0)
    profit = qwen_result.get("estimated_profit", 0)
    confidence = qwen_result.get("confidence", "low")

    if verbose:
        emoji = "✅" if recommendation == "buy" else ("⚠️" if recommendation == "investigate" else "❌")
        print(f"  {emoji} Analysis: {recommendation.upper()} | {confidence} confidence | ${profit:.0f} profit | {margin:.0f}% margin")
        if qwen_result.get("risk_factors"):
            print(f"  ⚠️  Risks: {', '.join(qwen_result['risk_factors'][:3])}")

    return {
        "listing": listing,
        "decision": recommendation,
        "confidence": confidence,
        "profit": profit,
        "margin_percent": margin,
        "market_value": qwen_result.get("estimated_market_value", 0),
        "sell_price": qwen_result.get("realistic_sell_price", 0),
        "risk_factors": qwen_result.get("risk_factors", []),
        "notes": qwen_result.get("notes", ""),
        "stage": "qwen"
    }


def analyze_batch(listings: list, verbose: bool = True) -> list:
    """Analyze a batch of listings. Returns only actionable ones (buy/investigate)."""
    results = []
    passed = 0

    print(f"\n📦 Analyzing {len(listings)} listings...\n")

    for listing in listings:
        result = analyze_listing(listing, verbose=verbose)
        if result["decision"] in ("buy", "investigate"):
            passed += 1
            results.append(result)

    print(f"\n✅ Pipeline complete: {passed}/{len(listings)} worth action")
    return results


if __name__ == "__main__":
    # Test with sample listings
    test_listings = [
        {
            "title": "iPhone 14 Pro 256GB Space Black - Minor scratches",
            "price": 380,
            "condition": "Used",
            "description": "Works perfectly, minor scratches on back. Moving next week, must sell.",
            "platform": "craigslist",
            "location": "San Francisco, CA",
            "url": "https://sfbay.craigslist.org/test/123"
        },
        {
            "title": "iPhone 14 Pro - CRACKED SCREEN for parts only",
            "price": 150,
            "condition": "For parts",
            "description": "Screen is shattered, sold as is.",
            "platform": "craigslist",
            "location": "Oakland, CA",
            "url": "https://sfbay.craigslist.org/test/456"
        },
        {
            "title": "MacBook Air M1 2020 barely used",
            "price": 550,
            "condition": "Like New",
            "description": "Bought in 2021, barely used. No scratches, original box included. Downsizing.",
            "platform": "facebook",
            "location": "San Jose, CA",
            "url": "https://facebook.com/test/789"
        },
    ]

    results = analyze_batch(test_listings, verbose=True)

    print("\n\n🎯 ACTIONABLE DEALS:")
    print("=" * 60)
    for r in results:
        l = r["listing"]
        print(f"\n{'🟢 BUY' if r['decision'] == 'buy' else '🟡 INVESTIGATE'}: {l['title'][:50]}")
        print(f"  Price: ${l['price']} | Est. sell: ${r.get('sell_price', '?')} | Profit: ${r.get('profit', '?'):.0f} ({r.get('margin_percent', 0):.0f}%)")
        print(f"  Confidence: {r.get('confidence', '?')} | {r.get('notes', '')}")
        print(f"  URL: {l.get('url', 'N/A')}")
