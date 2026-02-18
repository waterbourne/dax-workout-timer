#!/usr/bin/env python3
"""
eBay Deal Finder - Search for underpriced items on eBay
Usage: python ebay_deals.py --search "item name" --max-price 500
"""

import argparse
import json
import re
from urllib.parse import quote_plus
import sys

def search_ebay_deals(search_term, max_price=None, condition=None, category=None):
    """
    Generate eBay search URL with filters
    Returns search parameters for manual search
    """
    base_url = "https://www.ebay.com/sch/i.html"
    
    # Build search parameters
    params = {
        '_nkw': search_term,
        '_sacat': category or '0',
        'LH_BIN': '1',  # Buy It Now
        '_sop': '15',   # Price + Shipping: lowest first
    }
    
    if max_price:
        params['_udhi'] = str(max_price)
    
    if condition:
        condition_map = {
            'new': '1000',
            'open_box': '1500',
            'used': '3000'
        }
        if condition.lower() in condition_map:
            params['LH_ItemCondition'] = condition_map[condition.lower()]
    
    # Build URL
    query_string = '&'.join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
    search_url = f"{base_url}?{query_string}"
    
    return {
        'search_term': search_term,
        'max_price': max_price,
        'condition': condition,
        'search_url': search_url,
        'tips': [
            'Sort by "Price + Shipping: lowest first"',
            'Check "Sold listings" to see actual market value',
            'Look for auctions ending soon with no bids',
            'Filter by "Buy It Now" to find quick deals',
            'Check seller feedback before buying'
        ]
    }

def calculate_profit_margin(buy_price, sell_price, platform='ebay'):
    """Calculate profit margin after fees"""
    fees = {
        'ebay': 0.1325,  # 13.25% final value fee
        'facebook': 0.0,  # No fees for local
        'mercari': 0.10,  # 10% fee
    }
    
    fee_rate = fees.get(platform, 0.13)
    fee_amount = sell_price * fee_rate
    profit = sell_price - buy_price - fee_amount
    margin = (profit / buy_price) * 100 if buy_price > 0 else 0
    
    return {
        'buy_price': buy_price,
        'sell_price': sell_price,
        'platform_fee': fee_amount,
        'profit': profit,
        'margin_percent': margin
    }

def main():
    parser = argparse.ArgumentParser(description='Find deals on eBay')
    parser.add_argument('--search', '-s', required=True, help='Search term')
    parser.add_argument('--max-price', '-max', type=float, help='Maximum price')
    parser.add_argument('--condition', '-c', choices=['new', 'open_box', 'used'], 
                        help='Item condition')
    parser.add_argument('--min-profit', type=float, default=30, 
                        help='Minimum profit margin percent (default: 30)')
    
    args = parser.parse_args()
    
    print(f"🔍 Searching eBay for: {args.search}")
    print("=" * 60)
    
    result = search_ebay_deals(
        args.search, 
        args.max_price, 
        args.condition
    )
    
    print(f"\n📱 Search URL:\n{result['search_url']}\n")
    
    print("💡 Pro Tips:")
    for tip in result['tips']:
        print(f"  • {tip}")
    
    print("\n📊 Example Profit Analysis:")
    print("-" * 40)
    
    # Show example margins at different sell prices
    if args.max_price:
        sell_prices = [
            args.max_price * 1.5,
            args.max_price * 2.0,
            args.max_price * 2.5
        ]
        
        for sell in sell_prices:
            analysis = calculate_profit_margin(args.max_price, sell)
            if analysis['margin_percent'] >= args.min_profit:
                print(f"  Buy: ${args.max_price:.0f} → Sell: ${sell:.0f} = "
                      f"${analysis['profit']:.0f} profit ({analysis['margin_percent']:.0f}% margin)")

if __name__ == '__main__':
    main()
