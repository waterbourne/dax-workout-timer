---
name: deal-hunter
description: Find underpriced or mispriced items online for retail arbitrage and resale profit. Use when searching for deals, price discrepancies, liquidation opportunities, or resale opportunities on marketplaces like eBay, Facebook Marketplace, Craigslist, Amazon, auction sites, and wholesale platforms. Supports automated deal monitoring, price comparison, and profit margin analysis.
---

# Deal Hunter

Find underpriced items online to buy low and sell high. This skill helps identify arbitrage opportunities across marketplaces, auction sites, and wholesale platforms.

## Quick Start

### Manual Deal Search

Search for specific items with price filters:

```bash
# Search eBay for underpriced items
python scripts/ebay_deals.py --search "iPhone 15 Pro" --max-price 700 --condition used

# Search Facebook Marketplace
python scripts/fb_marketplace.py --search "macbook pro" --location "94102" --radius 25

# Monitor Craigslist for deals
python scripts/craigslist_deals.py --search "dining table" --category furniture --min-profit 100
```

### Automated Monitoring

Set up alerts for new deals:

```bash
# Create a monitoring job
python scripts/monitor_deals.py --config deals_config.yaml --interval 30

# Run price comparison across platforms
python scripts/price_compare.py --item "Nintendo Switch OLED" --platforms ebay,facebook,craigslist
```

## Deal Sources

### High-Volume Marketplaces
- **eBay** - Auctions, Buy It Now, bulk lots
- **Facebook Marketplace** - Local deals, negotiation room
- **Craigslist** - Local cash deals, often underpriced
- **OfferUp/Letgo** - Mobile-first, less competition
- **Mercari** - Lower fees than eBay, growing user base

### Wholesale/Liquidation
- **Liquidation.com** - Returns, shelf pulls, salvage
- **B-Stock** - Manufacturer returns (Best Buy, Amazon, etc.)
- **Bulq** - Amazon returns, graded condition
- **Direct Liquidation** - Pallets and truckloads

### Specialized Platforms
- **GovDeals** - Government surplus auctions
- **PropertyRoom** - Police auctions, evidence items
- **ShopGoodwill** - Estate items, rare finds
- **EstateSales.org** - In-person and online estate sales

## Deal Categories by Budget

### Under $100 (Quick Flips)
- Electronics accessories (cables, cases, chargers)
- Video games and consoles
- Books and textbooks
- Sporting goods
- Toys and collectibles

### $100-$500 (Moderate Flips)
- Smartphones and tablets
- Laptops and computers
- Power tools
- Bicycles
- Musical instruments
- Designer clothing/shoes

### $500-$2000 (Higher Margin)
- High-end electronics (MacBooks, cameras)
- Furniture sets
- Appliances
- Jewelry and watches
- Motorcycles/scooters

### $2000-$5000 (Major Scores)
- Vehicles (Craigslist/Facebook gems)
- Commercial equipment
- High-end musical instruments
- Rare collectibles
- Luxury items

## Profit Margin Guidelines

**Minimum viable flip:** 30% margin after fees/shipping
**Good flip:** 50%+ margin
**Excellent flip:** 100%+ margin

Calculate total costs:
- Purchase price
- Sales tax (if applicable)
- Platform fees (eBay: ~13%, Facebook: 0% local)
- Shipping/transportation
- Cleaning/repairs

## Red Flags to Avoid

- Items requiring expensive repairs
- Counterfeit goods (designer items)
- Stolen goods (too-good-to-be-true prices)
- Items with hidden damage
- Items with no resale market
- Heavy/bulky items with high shipping costs

## Advanced Strategies

See [references/advanced-strategies.md](references/advanced-strategies.md) for:
- Bid sniping on auctions
- Bulk lot breakdown
- Seasonal buying patterns
- Cross-platform arbitrage
- Tools for automated scraping

## Platform-Specific Tips

See [references/platforms.md](references/platforms.md) for detailed guidance on each marketplace.

## Legal Considerations

- Report suspiciously low prices (potential stolen goods)
- Keep receipts for tax purposes
- Follow local resale permit requirements
- Be aware of warranty transferability

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `ebay_deals.py` | Search eBay listings with profit filters |
| `fb_marketplace.py` | Scrape Facebook Marketplace |
| `craigslist_deals.py` | Monitor Craigslist by category |
| `price_compare.py` | Compare prices across platforms |
| `monitor_deals.py` | Continuous monitoring with alerts |
| `profit_calc.py` | Calculate margins with all fees |

## Example Workflows

**Find iPhone flips:**
```bash
python scripts/ebay_deals.py --search "iPhone 14 Pro" --max-price 500 --condition used
python scripts/fb_marketplace.py --search "iPhone 14 Pro" --radius 50
python scripts/price_compare.py --item "iPhone 14 Pro 256GB" --get-market-price
```

**Monitor for quick flips:**
```bash
python scripts/monitor_deals.py --search "Nintendo Switch" --max-price 150 --notify telegram
```

**Analyze bulk lot:**
```bash
python scripts/bulk_analyzer.py --url "https://www.liquidation.com/auction/12345" --resale-channel ebay
```
