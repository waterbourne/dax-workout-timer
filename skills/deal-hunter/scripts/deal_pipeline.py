#!/usr/bin/env python3
"""
Deal Pipeline - Main orchestrator
Pulls listings → AI screens → Telegram alerts
Usage: python deal_pipeline.py [--once] [--dry-run] [--test]
"""

import argparse
import json
import os
import time
import hashlib
import requests
import yaml
from datetime import datetime, timedelta
from pathlib import Path

# Import our modules
import sys
sys.path.insert(0, os.path.dirname(__file__))
from ai_analyzer import analyze_listing, analyze_batch
from ebay_scraper import scrape_ebay
from craigslist_scraper import scrape_craigslist, get_listing_detail

# Paths
SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR.parent / "config"
DATA_DIR = SCRIPT_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

WATCHLIST_FILE = CONFIG_DIR / "watchlist.yaml"
SEEN_FILE = DATA_DIR / "seen_listings.json"
LOG_FILE = DATA_DIR / "deal_log.json"

# Telegram (reads from OpenClaw config or env)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8584092724")


def load_watchlist() -> dict:
    with open(WATCHLIST_FILE, "r") as f:
        return yaml.safe_load(f)


def load_seen() -> dict:
    if SEEN_FILE.exists():
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    return {}


def save_seen(seen: dict):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f, indent=2)


def listing_id(listing: dict) -> str:
    """Generate a dedup ID for a listing."""
    key = f"{listing.get('platform', '')}-{listing.get('url', '')}-{listing.get('price', '')}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def is_seen(lid: str, seen: dict, window_hours: int = 24) -> bool:
    """Check if listing was already seen within the dedup window."""
    if lid not in seen:
        return False
    seen_time = datetime.fromisoformat(seen[lid])
    return datetime.now() - seen_time < timedelta(hours=window_hours)


def mark_seen(lid: str, seen: dict):
    seen[lid] = datetime.now().isoformat()


def send_telegram(message: str, token: str, chat_id: str) -> bool:
    """Send a Telegram message via Bot API."""
    if not token:
        print(f"  [No Telegram token — would send:\n{message}\n]")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"  Telegram send failed: {e}")
        return False


def format_alert(result: dict) -> str:
    """Format a deal result into a Telegram message."""
    l = result["listing"]
    decision = result["decision"].upper()
    emoji = "🟢" if decision == "BUY" else "🟡"
    
    lines = [
        f"{emoji} <b>{decision}</b> — {l['title'][:60]}",
        f"",
        f"💰 <b>Price:</b> ${l['price']}",
        f"📈 <b>Est. sell:</b> ${result.get('sell_price', '?')}",
        f"💵 <b>Profit:</b> ${result.get('profit', 0):.0f} ({result.get('margin_percent', 0):.0f}% margin)",
        f"🎯 <b>Confidence:</b> {result.get('confidence', '?')}",
        f"📍 <b>Location:</b> {l.get('location', '?')}",
        f"🏪 <b>Platform:</b> {l.get('platform', '?').capitalize()}",
    ]
    
    if result.get("risk_factors"):
        lines.append(f"⚠️ <b>Risks:</b> {', '.join(result['risk_factors'][:2])}")
    
    if result.get("notes"):
        lines.append(f"📝 {result['notes']}")
    
    lines.append(f"")
    lines.append(f"🔗 <a href=\"{l.get('url', '#')}\">View Listing</a>")
    lines.append(f"<i>Found at {datetime.now().strftime('%I:%M %p')}</i>")
    
    return "\n".join(lines)


def log_deal(result: dict):
    """Append deal to log file."""
    log = []
    if LOG_FILE.exists():
        with open(LOG_FILE, "r") as f:
            try:
                log = json.load(f)
            except Exception:
                log = []
    
    log.append({
        "timestamp": datetime.now().isoformat(),
        "decision": result["decision"],
        "title": result["listing"]["title"],
        "price": result["listing"]["price"],
        "profit": result.get("profit", 0),
        "margin": result.get("margin_percent", 0),
        "platform": result["listing"]["platform"],
        "url": result["listing"]["url"],
    })
    
    # Keep last 500 deals
    log = log[-500:]
    
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def run_scan(watchlist: dict, seen: dict, dry_run: bool = False, verbose: bool = True) -> int:
    """
    Run one full scan cycle across all watch items.
    Returns number of alerts sent.
    """
    config = watchlist.get("scan", {})
    tg_config = watchlist.get("telegram", {})
    
    dedup_hours = config.get("dedup_window_hours", 24)
    max_results = config.get("max_results_per_search", 25)
    fetch_full = config.get("fetch_full_descriptions", True)
    only_buy = tg_config.get("only_buy", False)
    min_confidence = tg_config.get("min_confidence", "medium")
    
    conf_rank = {"low": 0, "medium": 1, "high": 2}
    
    alerts_sent = 0
    timestamp = datetime.now().strftime("%H:%M")
    
    print(f"\n{'='*60}")
    print(f"🔍 Deal Pipeline Scan — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    for watch in watchlist.get("watches", []):
        name = watch["name"]
        search = watch["search"]
        max_price = watch.get("max_price")
        platforms = watch.get("platforms", ["craigslist", "ebay"])
        category = watch.get("category", "general")
        min_margin = watch.get("min_margin", 30)

        print(f"\n📦 {name} | max ${max_price} | {'+'.join(platforms)}")

        all_listings = []

        # Scrape each platform
        if "craigslist" in platforms:
            cl_listings = scrape_craigslist(search, max_price=max_price, 
                                             category=category, max_results=max_results)
            print(f"  Craigslist: {len(cl_listings)} listings")
            all_listings.extend(cl_listings)

        if "ebay" in platforms:
            time.sleep(1)  # Rate limit
            ebay_listings = scrape_ebay(search, max_price=max_price, 
                                         condition="used", max_results=max_results)
            print(f"  eBay: {len(ebay_listings)} listings")
            all_listings.extend(ebay_listings)

        if not all_listings:
            print(f"  No listings found")
            continue

        # Dedup
        new_listings = []
        for listing in all_listings:
            lid = listing_id(listing)
            if not is_seen(lid, seen, dedup_hours):
                new_listings.append(listing)
                mark_seen(lid, seen)
        
        print(f"  {len(new_listings)} new (deduped {len(all_listings) - len(new_listings)})")
        
        if not new_listings:
            continue

        # Fetch full descriptions for Craigslist (improves AI accuracy)
        if fetch_full:
            for listing in new_listings:
                if listing["platform"] == "craigslist" and listing.get("url"):
                    detail = get_listing_detail(listing["url"])
                    if detail.get("description"):
                        listing["description"] = detail["description"]
                    if detail.get("condition") and detail["condition"] != "Used":
                        listing["condition"] = detail["condition"]

        # AI analysis
        print(f"  🤖 Running AI analysis on {len(new_listings)} listings...")
        for listing in new_listings:
            result = analyze_listing(listing, verbose=verbose)
            
            if result["decision"] not in ("buy", "investigate"):
                continue
            
            # Filter by margin
            if result.get("margin_percent", 0) < min_margin:
                if verbose:
                    print(f"    Skipped (margin {result.get('margin_percent', 0):.0f}% < {min_margin}%)")
                continue
            
            # Filter by confidence
            result_conf_rank = conf_rank.get(result.get("confidence", "low"), 0)
            min_conf_rank = conf_rank.get(min_confidence, 1)
            if result_conf_rank < min_conf_rank:
                if verbose:
                    print(f"    Skipped (confidence {result.get('confidence')} < {min_confidence})")
                continue
            
            # Filter if only_buy
            if only_buy and result["decision"] != "buy":
                continue
            
            # Log it
            log_deal(result)
            
            # Send alert
            message = format_alert(result)
            
            if dry_run:
                print(f"\n  [DRY RUN] Would send:\n{message}\n")
            else:
                token = TELEGRAM_BOT_TOKEN
                chat_id = tg_config.get("target", TELEGRAM_CHAT_ID)
                sent = send_telegram(message, token, chat_id)
                if sent:
                    print(f"  📱 Alert sent: {result['decision'].upper()} — {listing['title'][:40]}")
                    alerts_sent += 1
                else:
                    print(f"  ⚠️  Alert send failed — check Telegram token")
                    print(f"  Deal: {result['decision'].upper()} — {listing['title'][:40]} @ ${listing['price']}")
    
    save_seen(seen)
    return alerts_sent


def main():
    parser = argparse.ArgumentParser(description="Deal Pipeline — AI-powered arbitrage scanner")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--dry-run", action="store_true", help="Don't send Telegram alerts")
    parser.add_argument("--test", action="store_true", help="Test with sample listings")
    parser.add_argument("--interval", type=int, default=30, help="Interval in minutes (default: 30)")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()

    if args.test:
        # Run the ai_analyzer test
        print("Running AI test with sample listings...")
        from ai_analyzer import analyze_batch
        test_listings = [
            {
                "title": "iPhone 14 Pro 256GB Space Black - Minor scratches",
                "price": 380,
                "condition": "Used - Good",
                "description": "Works perfectly, minor scratches on back glass. Moving next week, must sell. Comes with original charger.",
                "platform": "craigslist",
                "location": "San Francisco, CA",
                "url": "https://sfbay.craigslist.org/test/123"
            },
            {
                "title": "MacBook Air M1 2020 barely used",
                "price": 550,
                "condition": "Like New",
                "description": "Bought in 2021, barely used. No scratches. Original box. Downsizing after getting M3.",
                "platform": "craigslist",
                "location": "San Jose, CA",
                "url": "https://sfbay.craigslist.org/test/456"
            },
        ]
        results = analyze_batch(test_listings, verbose=True)
        print(f"\n✅ Test complete. {len(results)} actionable deals found.")
        return

    watchlist = load_watchlist()
    seen = load_seen()

    if args.once:
        alerts = run_scan(watchlist, seen, dry_run=args.dry_run, verbose=not args.quiet)
        print(f"\n✅ Scan complete. {alerts} alerts sent.")
        return

    # Continuous loop
    interval = args.interval
    print(f"🚀 Deal Pipeline started — scanning every {interval} minutes")
    print(f"   Watching {len(watchlist.get('watches', []))} items")
    print(f"   Press Ctrl+C to stop\n")

    while True:
        try:
            alerts = run_scan(watchlist, seen, dry_run=args.dry_run, verbose=not args.quiet)
            print(f"\n⏱️  Next scan in {interval} minutes... ({alerts} alerts sent this run)")
            time.sleep(interval * 60)
        except KeyboardInterrupt:
            print("\n\n👋 Pipeline stopped.")
            break
        except Exception as e:
            print(f"\n⚠️  Pipeline error: {e}")
            print("Retrying in 5 minutes...")
            time.sleep(300)


if __name__ == "__main__":
    main()
