#!/usr/bin/env python3
"""
Deal Monitor - Set up alerts for specific items
Usage: python monitor_deals.py --search "macbook pro" --max-price 500 --interval 30
"""

import argparse
import time
from datetime import datetime
import sys

class DealMonitor:
    def __init__(self, search_term, max_price=None, min_profit=30):
        self.search_term = search_term
        self.max_price = max_price
        self.min_profit = min_profit
        self.seen_items = set()
    
    def generate_search_links(self):
        """Generate direct search links for all platforms"""
        from urllib.parse import quote_plus
        
        searches = {
            'eBay': f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(self.search_term)}&_sop=10",
            'Facebook': f"https://www.facebook.com/marketplace/search/?query={quote_plus(self.search_term)}",
            'Craigslist': f"https://sfbay.craigslist.org/search/sss?query={quote_plus(self.search_term)}&sort=date",
            'OfferUp': f"https://offerup.com/search/?q={quote_plus(self.search_term)}",
        }
        
        if self.max_price:
            searches['eBay'] += f"&_udhi={self.max_price}"
        
        return searches
    
    def check_deals(self):
        """Simulate deal checking - in real implementation, would scrape APIs"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] Checking for new deals: '{self.search_term}'")
        print("-" * 60)
        
        searches = self.generate_search_links()
        
        print("🔗 Quick Links (open in browser):")
        for platform, url in searches.items():
            print(f"\n{platform}:")
            print(f"  {url}")
        
        print("\n💡 Search Tips:")
        print(f"  • Sort by 'Date Listed' to see newest first")
        print(f"  • Set max price filter to ${self.max_price}" if self.max_price else "  • Set price filters manually")
        print(f"  • Look for keywords: 'moving', 'must sell', 'divorce', 'estate'")
        print(f"  • Check 'Sold' listings to confirm market value")
        
        return True
    
    def run(self, interval_minutes=30, once=False):
        """Run the monitor loop"""
        print(f"🎯 Deal Monitor Started")
        print(f"   Search: '{self.search_term}'")
        print(f"   Max Price: ${self.max_price}" if self.max_price else "   Max Price: None")
        print(f"   Check Interval: {interval_minutes} minutes")
        print(f"   Press Ctrl+C to stop\n")
        
        if once:
            self.check_deals()
            return
        
        try:
            while True:
                self.check_deals()
                print(f"\n⏱️  Next check in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n\n👋 Monitor stopped.")

def main():
    parser = argparse.ArgumentParser(description='Monitor for deals across platforms')
    parser.add_argument('--search', '-s', required=True, help='Item to search for')
    parser.add_argument('--max-price', '-max', type=float, help='Maximum price')
    parser.add_argument('--min-profit', type=float, default=30, help='Minimum profit %')
    parser.add_argument('--interval', '-i', type=int, default=30, 
                       help='Check interval in minutes (default: 30)')
    parser.add_argument('--once', action='store_true', 
                       help='Run once and exit (no loop)')
    
    args = parser.parse_args()
    
    monitor = DealMonitor(args.search, args.max_price, args.min_profit)
    monitor.run(args.interval, args.once)

if __name__ == '__main__':
    main()
