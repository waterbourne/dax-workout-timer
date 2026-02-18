#!/usr/bin/env python3
"""
Profit Calculator - Analyze deal profitability
Usage: python profit_calc.py --buy 100 --sell 200 --platform ebay
"""

import argparse

def calculate_deal(buy_price, sell_price, platform='ebay', 
                   shipping_cost=0, repair_cost=0, storage_cost=0):
    """Calculate full profit breakdown"""
    
    # Platform fees
    fees = {
        'ebay': 0.1325,
        'facebook': 0.0,
        'mercari': 0.10,
        'amazon': 0.15,
        'offerup': 0.129,
    }
    
    fee_rate = fees.get(platform, 0.13)
    platform_fee = sell_price * fee_rate
    
    # Payment processing (if not included)
    processing_fee = sell_price * 0.029 if platform == 'facebook' else 0
    
    # Calculate totals
    total_costs = (buy_price + platform_fee + processing_fee + 
                   shipping_cost + repair_cost + storage_cost)
    
    profit = sell_price - total_costs
    margin = (profit / buy_price) * 100 if buy_price > 0 else 0
    roi = (profit / total_costs) * 100 if total_costs > 0 else 0
    
    return {
        'revenue': sell_price,
        'costs': {
            'purchase': buy_price,
            'platform_fee': platform_fee,
            'processing': processing_fee,
            'shipping': shipping_cost,
            'repair': repair_cost,
            'storage': storage_cost,
            'total': total_costs
        },
        'profit': profit,
        'margin_percent': margin,
        'roi_percent': roi,
        'viable': margin >= 30
    }

def main():
    parser = argparse.ArgumentParser(description='Calculate deal profitability')
    parser.add_argument('--buy', '-b', type=float, required=True, help='Purchase price')
    parser.add_argument('--sell', '-s', type=float, required=True, help='Expected sell price')
    parser.add_argument('--platform', '-p', default='ebay',
                       choices=['ebay', 'facebook', 'mercari', 'amazon', 'offerup'],
                       help='Selling platform')
    parser.add_argument('--shipping', type=float, default=0, help='Shipping cost')
    parser.add_argument('--repair', type=float, default=0, help='Repair/cleaning cost')
    
    args = parser.parse_args()
    
    result = calculate_deal(
        args.buy, 
        args.sell, 
        args.platform,
        args.shipping,
        args.repair
    )
    
    print("📊 DEAL ANALYSIS")
    print("=" * 50)
    print(f"\n💰 Revenue: ${result['revenue']:.2f}")
    print(f"\n💸 Costs:")
    print(f"  Purchase:      ${result['costs']['purchase']:.2f}")
    print(f"  Platform Fee:  ${result['costs']['platform_fee']:.2f}")
    print(f"  Processing:    ${result['costs']['processing']:.2f}")
    print(f"  Shipping:      ${result['costs']['shipping']:.2f}")
    print(f"  Repair:        ${result['costs']['repair']:.2f}")
    print(f"  {'─' * 30}")
    print(f"  Total Costs:   ${result['costs']['total']:.2f}")
    
    print(f"\n📈 Results:")
    print(f"  Profit:        ${result['profit']:.2f}")
    print(f"  Margin:        {result['margin_percent']:.1f}%")
    print(f"  ROI:           {result['roi_percent']:.1f}%")
    
    if result['viable']:
        print(f"\n✅ VIABLE DEAL (30%+ margin)")
    else:
        print(f"\n⚠️  LOW MARGIN (under 30%)")
    
    # Quick assessment
    if result['margin_percent'] >= 100:
        print("🌟 EXCELLENT opportunity!")
    elif result['margin_percent'] >= 50:
        print("👍 GOOD opportunity")
    elif result['margin_percent'] >= 30:
        print("✓ ACCEPTABLE but monitor closely")
    else:
        print("❌ PASS - not enough margin")

if __name__ == '__main__':
    main()
