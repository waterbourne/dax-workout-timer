#!/usr/bin/env python3
"""
Price Comparison Tool - Compare prices across marketplaces
Usage: python price_compare.py --item "Nintendo Switch" --platforms ebay,facebook
"""

import argparse
from urllib.parse import quote_plus

def generate_comparison_links(item_name, platforms=None):
    """Generate search URLs for multiple platforms"""
    
    if platforms is None:
        platforms = ['ebay', 'facebook', 'craigslist', 'offerup', 'mercari']
    
    encoded_item = quote_plus(item_name)
    
    links = {}
    
    if 'ebay' in platforms:
        links['eBay (Buy It Now)'] = f"https://www.ebay.com/sch/i.html?_nkw={encoded_item}&LH_BIN=1&_sop=15"
        links['eBay (Auctions Ending)'] = f"https://www.ebay.com/sch/i.html?_nkw={encoded_item}&LH_Auction=1&_sop=1"
        links['eBay (Sold)'] = f"https://www.ebay.com/sch/i.html?_nkw={encoded_item}&LH_Sold=1&LH_Complete=1"
    
    if 'facebook' in platforms:
        links['Facebook Marketplace'] = f"https://www.facebook.com/marketplace/search/?query={encoded_item}"
    
    if 'craigslist' in platforms:
        links['Craigslist'] = f"https://sfbay.craigslist.org/search/sss?query={encoded_item}&sort=date"
    
    if 'offerup' in platforms:
        links['OfferUp'] = f"https://offerup.com/search/?q={encoded_item}"
    
    if 'mercari' in platforms:
        links['Mercari'] = f"https://www.mercari.com/search/?keyword={encoded_item}"
    
    return links

def estimate_market_value(item_name):
    """Provide guidance on finding market value"""
    print(f"\n💰 Finding Market Value for '{item_name}':")
    print("=" * 60)
    print("\n1. Check eBay SOLD listings (last 30 days):")
    print(f"   https://www.ebay.com/sch/i.html?_nkw={quote_plus(item_name)}&LH_Sold=1&LH_Complete=1")
    print("\n2. Filter by condition:")
    print("   • New: Look for sealed/brand new prices")
    print("   • Used: Check item specifics for comparable condition")
    print("\n3. Remove outliers:")
    print("   • Ignore extremely high/low sold prices")
    print("   • Focus on median price range")
    print("\n4. Factor in:")
    print("   • Shipping costs (free shipping vs paid)")
    print("   • Seller fees (eBay ~13%, Facebook 0%)")
    print("   • Time to sell (lower price = faster sale)")

def get_quick_flip_suggestions(category=None):
    """Suggest popular flip categories"""
    suggestions = {
        'electronics': [
            ('iPhone 13 Pro', 300, 500),
            ('iPad Air', 200, 400),
            ('Nintendo Switch OLED', 200, 300),
            ('MacBook Air M1', 400, 700),
            ('Sony WH-1000XM4', 100, 200),
        ],
        'furniture': [
            ('Mid century dresser', 50, 300),
            ('Eames chair replica', 100, 400),
            ('Standing desk', 100, 300),
            ('Leather sectional', 200, 800),
        ],
        'collectibles': [
            ('Pokemon cards lot', 50, 500),
            ('Vintage LEGO sets', 30, 300),
            ('Funko Pop chase', 10, 100),
        ],
        'tools': [
            ('Miter saw', 100, 300),
            ('Pressure washer', 50, 200),
            ('Table saw', 150, 500),
        ]
    }
    
    if category and category in suggestions:
        return suggestions[category]
    
    # Return all
    all_items = []
    for cat, items in suggestions.items():
        all_items.extend([(f"[{cat}] {name}", low, high) for name, low, high in items])
    return all_items

def main():
    parser = argparse.ArgumentParser(description='Compare prices across platforms')
    parser.add_argument('--item', '-i', help='Item to search for')
    parser.add_argument('--platforms', '-p', 
                       default='ebay,facebook,craigslist',
                       help='Comma-separated platforms')
    parser.add_argument('--suggestions', '-s', action='store_true',
                       help='Show popular flip items')
    parser.add_argument('--category', '-c',
                       choices=['electronics', 'furniture', 'collectibles', 'tools'],
                       help='Show suggestions for category')
    
    args = parser.parse_args()
    
    if args.suggestions or args.category:
        print("🔥 POPULAR FLIP OPPORTUNITIES")
        print("=" * 60)
        print("\nFormat: Item | Buy Range | Sell Range | Potential Margin")
        print("-" * 60)
        
        items = get_quick_flip_suggestions(args.category)
        for item, buy_low, sell_high in items:
            margin = ((sell_high - buy_low) / buy_low) * 100
            print(f"{item:30} | ${buy_low}-${sell_high} | {margin:.0f}% margin")
        
        print("\n💡 Pro Tip: Start with items under $500 to minimize risk")
        return
    
    if not args.item:
        print("Error: --item required (or use --suggestions)")
        return
    
    platforms = [p.strip() for p in args.platforms.split(',')]
    links = generate_comparison_links(args.item, platforms)
    
    print(f"🔍 Price Comparison for: '{args.item}'")
    print("=" * 60)
    
    for platform, url in links.items():
        print(f"\n{platform}:")
        print(f"  {url}")
    
    estimate_market_value(args.item)
    
    print("\n\n🎯 BUYING STRATEGY:")
    print("-" * 40)
    print("Target buy price: 40-60% of market value")
    print("Quick flip price: 70-80% of market value")
    print("Maximum hold time: 30 days")
    print("Minimum margin: 30% after all fees")

if __name__ == '__main__':
    main()
