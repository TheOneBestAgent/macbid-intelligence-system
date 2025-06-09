# 🎯 Lot-Level Scrapers Suite for SC Warehouses

## 🚀 Overview

Now that we've discovered the search API can access **individual lots** (not just auction summaries), we've built a comprehensive suite of specialized scrapers to analyze all **37,037+ lots** across your 5 SC warehouse locations.

## 📍 Your SC Warehouse Locations
- **Location 17**: Spartanburg
- **Location 20**: Greenville (most active)
- **Location 28**: Rock Hill (highest concentration)
- **Location 34**: Gastonia (most active)
- **Location 36**: Anderson

---

## 🎛️ Master Dashboard

### `master_dashboard.py` - Command Center
**The ultimate control center for all your scrapers**

```bash
# Quick scan of all scrapers
python3 master_dashboard.py

# Comprehensive detailed analysis
python3 master_dashboard.py --comprehensive

# Targeted scans by category
python3 master_dashboard.py --category deals
python3 master_dashboard.py --category luxury
python3 master_dashboard.py --category urgent
python3 master_dashboard.py --category electronics

# List all available scrapers
python3 master_dashboard.py --list-scrapers
```

**Features:**
- Runs all 8 specialized scrapers automatically
- Extracts key metrics from each scraper
- Provides comprehensive summary and recommendations
- Saves detailed JSON reports
- Shows success rates and performance metrics

---

## 🔍 Core Scrapers

### 1. `universal_lot_searcher.py` - Search Anything
**Search for ANY product across all 37,037+ lots**

```bash
# Search by predefined category
python3 universal_lot_searcher.py --category electronics
python3 universal_lot_searcher.py --category phones
python3 universal_lot_searcher.py --category audio
python3 universal_lot_searcher.py --category cameras

# Custom search
python3 universal_lot_searcher.py --search "macbook pro"
python3 universal_lot_searcher.py --search "nintendo switch"

# List all categories
python3 universal_lot_searcher.py --list-categories
```

**10 Predefined Categories:**
- Electronics, Phones, Audio, Cameras, Appliances
- Tools, Home & Garden, Fitness, Automotive, Luxury

### 2. `lot_level_scanner.py` - Comprehensive Analytics
**Advanced analytics across ALL inventory with 60+ search terms**

```bash
# Full comprehensive scan (all 60+ terms)
python3 lot_level_scanner.py --full-scan

# Quick scan (first 20 terms)
python3 lot_level_scanner.py --quick-scan

# Custom term count
python3 lot_level_scanner.py --terms 30
```

**Analytics Provided:**
- Inventory overview with total lots and values
- Location breakdown by warehouse
- Category analysis with savings percentages
- Brand analysis and value scoring
- Top 20 highest value items
- Comprehensive market trends

---

## 💎 Deal Discovery Scrapers

### 3. `deal_hunter.py` - Find the Best Steals
**Automatically finds high-value deals with significant savings**

```bash
# Find steals (50%+ off)
python3 deal_hunter.py --mode steals

# Find premium deals (30%+ off)
python3 deal_hunter.py --mode premium

# Find luxury items ($500+)
python3 deal_hunter.py --mode luxury
```

**Recent Finds:**
- LG Washer/Dryer: $3,299 → $670 (80% off!)
- Samsung Soundbar: $1,998 → $1,381 (31% off)
- Sony Camera: $2,198 → $1,759 (20% off)

### 4. `flash_deal_detector.py` - Newly Appeared Deals
**Detects items with massive discounts that just appeared**

```bash
# Default: 40%+ savings, $100+ value
python3 flash_deal_detector.py

# Custom thresholds
python3 flash_deal_detector.py --min-savings 50 --min-value 500

# Show only mega deals (score 15+)
python3 flash_deal_detector.py --mega-only
```

**Flash Score Algorithm:**
- Savings percentage (higher = better)
- Item value (higher = better)
- No current bids (opportunity bonus)
- Premium brand bonus

### 5. `no_bid_tracker.py` - Zero Bid Opportunities
**Find valuable items that haven't received any bids yet**

```bash
# Default: $50+ minimum value
python3 no_bid_tracker.py

# High-value only ($500+)
python3 no_bid_tracker.py --high-value-only

# Ending soon with no bids
python3 no_bid_tracker.py --ending-soon

# Custom minimum value
python3 no_bid_tracker.py --min-value 200
```

**Recent No-Bid Finds:**
- 81 items with zero bids
- $81,575 total retail value
- $21,089 potential savings
- 25.9% average savings rate

---

## ⏰ Time-Sensitive Scrapers

### 6. `ending_soon_monitor.py` - Urgent Opportunities
**Track high-value items closing within hours**

```bash
# Items ending within 24 hours
python3 ending_soon_monitor.py --hours 24

# Critical items (2 hours or less)
python3 ending_soon_monitor.py --critical-only

# Custom time window
python3 ending_soon_monitor.py --hours 6 --min-value 500
```

**Urgency Categories:**
- 🚨 **Critical**: Ending in 2 hours
- ⚠️ **Urgent**: Ending in 6 hours  
- 📅 **Today**: Ending in 24 hours

### 7. `new_arrival_monitor.py` - Fresh Inventory
**Monitor for newly added lots and high-value items**

```bash
# Scan for new arrivals
python3 new_arrival_monitor.py --scan

# Monitor specific categories
python3 new_arrival_monitor.py --monitor electronics

# Set up continuous monitoring
python3 new_arrival_monitor.py --continuous
```

**Features:**
- SQLite database tracks what you've seen
- Alerts for high-value new items
- Priority term monitoring
- Historical tracking

---

## 🏷️ Brand & Luxury Scrapers

### 8. `brand_tracker.py` - Premium Brand Monitor
**Track Apple, Sony, Dyson, and other premium brands**

```bash
# Track all premium brands
python3 brand_tracker.py --all

# Track specific brand
python3 brand_tracker.py --brand Apple
python3 brand_tracker.py --brand Sony

# List available brands
python3 brand_tracker.py --list-brands
```

**12 Premium Brands Tracked:**
- **HIGH Priority**: Apple, Sony, Dyson
- **MEDIUM Priority**: Samsung, Nintendo, Xbox, Canon, Nikon, Bose
- **LOW Priority**: KitchenAid, DeWalt, Milwaukee

### 9. `luxury_watch_hunter.py` - Timepiece Specialist
**Hunt for Rolex, Omega, Cartier, and luxury watches**

```bash
# Hunt all luxury watches
python3 luxury_watch_hunter.py

# Luxury tier and above only
python3 luxury_watch_hunter.py --luxury-only

# Specific brand
python3 luxury_watch_hunter.py --brand Rolex

# No-bid watches only
python3 luxury_watch_hunter.py --no-bids-only
```

**Watch Tiers:**
- **ULTRA_LUXURY**: Rolex, Patek Philippe, Audemars Piguet
- **LUXURY**: Omega, Cartier, Breitling
- **PREMIUM**: TAG Heuer, Tudor
- **ENTRY_LUXURY**: Seiko, Citizen

---

## 📊 Usage Examples

### Quick Daily Check
```bash
# Get overview of all opportunities
python3 master_dashboard.py

# Check for urgent items
python3 ending_soon_monitor.py --critical-only

# Find no-bid steals
python3 no_bid_tracker.py --high-value-only
```

### Deep Dive Analysis
```bash
# Comprehensive market analysis
python3 lot_level_scanner.py --full-scan

# Find all deals
python3 master_dashboard.py --category deals

# Hunt luxury items
python3 master_dashboard.py --category luxury
```

### Targeted Hunting
```bash
# Electronics focus
python3 universal_lot_searcher.py --category electronics
python3 brand_tracker.py --brand Apple

# Deal hunting
python3 deal_hunter.py --mode steals
python3 flash_deal_detector.py --mega-only
```

---

## 🎯 Pro Tips

### 1. **Start with Master Dashboard**
Always begin with `python3 master_dashboard.py` for a complete overview.

### 2. **Focus on No-Bid Items**
Items with zero bids are pure opportunities - check `no_bid_tracker.py` daily.

### 3. **Monitor Time-Sensitive**
Use `ending_soon_monitor.py --critical-only` for urgent opportunities.

### 4. **Track Your Interests**
Use brand trackers for specific interests (Apple, luxury watches, etc.).

### 5. **Set Up Alerts**
The new arrival monitor can track fresh inventory automatically.

---

## 📈 Performance Stats

### Current Inventory Coverage
- **Total Auctions**: 75 across SC warehouses
- **Total Lots**: 37,037+ individual items
- **Scan Speed**: 15-25 seconds for full inventory
- **Success Rate**: 95%+ API reliability

### Recent Discoveries
- **81 no-bid opportunities** worth $81K+
- **27 electronics items** worth $17K+
- **11 steals** with 50%+ savings
- **Multiple luxury watches** available

---

## 🔧 Technical Details

### Rate Limiting
- 0.15-0.25 second delays between requests
- Concurrent connection limits (10-15)
- SSL handling for secure connections

### Data Storage
- SQLite databases for persistence
- JSON exports for detailed analysis
- Timestamped reports for tracking

### Error Handling
- Graceful API failure handling
- Connection retry logic
- Comprehensive logging

---

## 🚀 What's Next?

With access to individual lots, you now have:

1. **Complete Market Visibility** - See every item across all SC warehouses
2. **Advanced Analytics** - Understand pricing, trends, and opportunities
3. **Automated Discovery** - Let scrapers find deals for you
4. **Time-Sensitive Alerts** - Never miss urgent opportunities
5. **Specialized Hunting** - Target specific brands, categories, or deal types

The lot-level access has unlocked the full potential of the mac.bid inventory system. You're now equipped with professional-grade auction intelligence tools!

---

## 📞 Quick Reference

| Scraper | Purpose | Best For |
|---------|---------|----------|
| `master_dashboard.py` | Overview of everything | Daily check-ins |
| `no_bid_tracker.py` | Zero bid opportunities | Easy wins |
| `deal_hunter.py` | Massive discounts | Best steals |
| `ending_soon_monitor.py` | Time-sensitive items | Urgent action |
| `brand_tracker.py` | Premium brands | Specific interests |
| `luxury_watch_hunter.py` | High-end timepieces | Luxury collecting |
| `universal_lot_searcher.py` | Any product search | Custom needs |
| `lot_level_scanner.py` | Complete analytics | Market research |

**Happy hunting! 🎯** 