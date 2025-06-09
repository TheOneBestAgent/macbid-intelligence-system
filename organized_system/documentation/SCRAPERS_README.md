# 🚀 mac.bid Advanced Scraper Suite

A comprehensive collection of 5 specialized scrapers for mac.bid auction analysis, built with authenticated API access.

## 📋 Overview

With authenticated access to mac.bid's APIs, you can now create powerful scrapers that go far beyond basic monitoring:

### 🔧 **The 5 Scrapers**

1. **📊 Price Tracker** - Monitor pricing trends and identify deals
2. **🔍 Search Scraper** - Advanced product search using Typesense API
3. **⏰ Timing Analyzer** - Find optimal bidding times and patterns
4. **🏆 Bid Analyzer** - Analyze winning patterns and undervalued categories
5. **📍 Location Scraper** - Track inventory by warehouse location

---

## 🚀 Quick Start

### **Run All Scrapers**
```bash
python3 master_scraper.py --all --pages 15
```

### **Quick Analysis**
```bash
python3 master_scraper.py --quick
```

### **Set Up Monitoring for Your SC Locations**
```bash
python3 master_scraper.py --setup-monitoring --locations 17,20,28,34,36
```

### **View Dashboard**
```bash
python3 master_scraper.py --dashboard
```

---

## 📊 1. Price Tracker (`price_tracker.py`)

**What it does:**
- Tracks auction prices across categories
- Identifies deals below market average
- Sets up price alerts for specific items
- Analyzes pricing trends over time

### **Usage Examples:**

```bash
# Run full price analysis
python3 price_tracker.py --pages 10

# Show price trends only
python3 price_tracker.py --trends

# Find current deals
python3 price_tracker.py --deals

# Add price alert for iPhones under $300 in SC locations
python3 price_tracker.py --add-alert "iPhone" 300 "17,20,28,34,36"

# Check triggered alerts
python3 price_tracker.py --alerts
```

### **Features:**
- **SQLite Database**: Stores historical pricing data
- **Category Analysis**: Automatic categorization of items
- **Deal Detection**: Finds items 20%+ below category average
- **Price Alerts**: Custom alerts for keywords and price thresholds
- **Trend Analysis**: Price patterns over time

---

## 🔍 2. Search Scraper (`search_scraper.py`)

**What it does:**
- Leverages mac.bid's Typesense search API
- Monitors specific brands and keywords
- Tracks inventory by UPC codes
- Analyzes search patterns and frequency

### **Usage Examples:**

```bash
# Search for Apple products in SC locations
python3 search_scraper.py --brand "Apple" --locations "17,20,28,34,36"

# Search by keywords
python3 search_scraper.py --keywords "iPhone" "13" "Pro" --locations "17,20,28"

# Search by UPC codes
python3 search_scraper.py --upc "123456789012" "987654321098"

# Add brand monitor for Samsung products $50-$400
python3 search_scraper.py --add-brand-monitor "Samsung" --price-range 50 400 --locations "17,20,28"

# Run all brand monitors
python3 search_scraper.py --run-monitors

# Show inventory analysis
python3 search_scraper.py --inventory-analysis
```

### **Features:**
- **Typesense Integration**: Direct access to mac.bid's search engine
- **Brand Monitoring**: Automated tracking of specific brands
- **UPC Tracking**: Search by exact product codes
- **Inventory Analysis**: Track how often items appear
- **Search History**: Complete log of all searches

---

## ⏰ 3. Timing Analyzer (`timing_analyzer.py`)

**What it does:**
- Analyzes optimal bidding times by hour/day
- Identifies low-competition time slots
- Studies auction duration patterns
- Provides timing recommendations

### **Usage Examples:**

```bash
# Run full timing analysis
python3 timing_analyzer.py --pages 15

# Show optimal bidding times only
python3 timing_analyzer.py --optimal-times

# Show day-of-week analysis
python3 timing_analyzer.py --day-analysis

# Generate timing report
python3 timing_analyzer.py --report
```

### **Features:**
- **Hourly Patterns**: Competition levels by hour of day
- **Day Analysis**: Best/worst days to bid
- **Duration Study**: How auction length affects prices
- **Competition Scoring**: Quantified competition levels
- **Optimal Times**: Data-driven bidding recommendations

---

## 🏆 4. Bid Analyzer (`bid_analyzer.py`)

**What it does:**
- Analyzes winning bid patterns
- Identifies undervalued categories
- Calculates optimal bidding ranges
- Tracks competition by category

### **Usage Examples:**

```bash
# Run full bid analysis
python3 bid_analyzer.py --pages 20

# Show undervalued categories
python3 bid_analyzer.py --undervalued

# Show optimal bidding ranges
python3 bid_analyzer.py --sweet-spots

# Show competition analysis
python3 bid_analyzer.py --competition

# Add value alert for Electronics under $150
python3 bid_analyzer.py --add-alert "Electronics" 150 "iPhone" "iPad"
```

### **Features:**
- **Value Rating**: Identifies undervalued vs overvalued items
- **Sweet Spots**: Optimal price ranges for each category
- **Competition Analysis**: Bidding competition by category
- **Success Patterns**: What makes winning bids successful
- **Value Alerts**: Notifications for undervalued opportunities

---

## 📍 5. Location Scraper (`location_scraper.py`)

**What it does:**
- Tracks inventory by warehouse location
- Analyzes regional pricing patterns
- Identifies best pickup routes
- Monitors location-specific trends

### **Usage Examples:**

```bash
# Run full location analysis
python3 location_scraper.py --pages 25

# Show top locations by inventory
python3 location_scraper.py --top-locations

# Show regional pricing patterns
python3 location_scraper.py --regional

# Show optimal pickup routes
python3 location_scraper.py --routes

# Show recent location trends
python3 location_scraper.py --trends
```

### **Features:**
- **Warehouse Mapping**: Links location IDs to actual addresses
- **Regional Analysis**: Pricing patterns by state
- **Route Optimization**: Best multi-location pickup routes
- **Inventory Tracking**: What's available where
- **Trend Monitoring**: Location activity over time

---

## 🎯 Master Scraper (`master_scraper.py`)

**Unified interface for all scrapers:**

### **Commands:**

```bash
# Run all 5 scrapers
python3 master_scraper.py --all --pages 15

# Quick analysis mode
python3 master_scraper.py --quick

# Show unified dashboard
python3 master_scraper.py --dashboard

# Set up monitoring for SC locations
python3 master_scraper.py --setup-monitoring --locations 17,20,28,34,36

# Run individual scrapers
python3 master_scraper.py --price --pages 10
python3 master_scraper.py --search
python3 master_scraper.py --timing --pages 12
python3 master_scraper.py --bid --pages 15
python3 master_scraper.py --location --pages 20
```

---

## 📊 Data Storage

Each scraper maintains its own SQLite database:

- `price_tracker.db` - Pricing data and alerts
- `search_tracker.db` - Search results and brand monitors
- `timing_analysis.db` - Timing patterns and statistics
- `bid_analysis.db` - Bid patterns and value analysis
- `location_inventory.db` - Location-based inventory data

---

## 🔔 Monitoring & Alerts

### **Price Alerts**
```bash
# iPhone under $300 in your locations
python3 price_tracker.py --add-alert "iPhone" 300 "17,20,28,34,36"

# Check all triggered alerts
python3 price_tracker.py --alerts
```

### **Brand Monitoring**
```bash
# Monitor Apple products $100-$500
python3 search_scraper.py --add-brand-monitor "Apple" --price-range 100 500 --locations "17,20,28"

# Run all brand monitors
python3 search_scraper.py --run-monitors
```

### **Value Alerts**
```bash
# Electronics under $200 with high value score
python3 bid_analyzer.py --add-alert "Electronics" 200 "iPhone" "iPad"
```

---

## 🏛️ Your South Carolina Locations

**Location IDs for SC warehouses:**
- **17**: Spartanburg (630 Edgefield Road, Cowpens, SC 29330)
- **20**: Greenville (141 Old Mill Rd, Greenville, SC 29607) ⭐ Most Active
- **28**: Rock Hill, SC
- **34**: Gastonia (1335 Isley Drive, Gastonia, NC 28052) ⭐ Most Active  
- **36**: Anderson (2 Greentree Road, Anderson, SC 29625)

---

## 🚀 Advanced Usage

### **Automated Monitoring Setup**
```bash
# Set up comprehensive monitoring for SC
python3 master_scraper.py --setup-monitoring --locations 17,20,28,34,36

# Run daily analysis
python3 master_scraper.py --all --pages 20

# Quick morning check
python3 master_scraper.py --quick
```

### **Custom Analysis Workflows**
```bash
# 1. Find undervalued categories
python3 bid_analyzer.py --undervalued

# 2. Check optimal timing for those categories
python3 timing_analyzer.py --optimal-times

# 3. Set up alerts for best opportunities
python3 price_tracker.py --add-alert "Electronics" 150 "17,20,28"

# 4. Monitor brand activity
python3 search_scraper.py --run-monitors
```

---

## 📈 What Each Scraper Reveals

### **Price Tracker**
- Which categories have the best deals
- Historical price trends
- When prices typically drop
- Alert you to great deals instantly

### **Search Scraper**  
- What brands appear most frequently
- Inventory turnover rates
- Product availability by location
- Search pattern analysis

### **Timing Analyzer**
- Best hours/days to bid (lowest competition)
- Worst times to avoid (highest competition)  
- How auction duration affects final prices
- Seasonal bidding patterns

### **Bid Analyzer**
- Which categories are consistently undervalued
- Optimal price ranges for successful bids
- Competition levels by category
- Success patterns of winning bidders

### **Location Scraper**
- Which warehouses have the most inventory
- Regional pricing differences
- Best multi-location pickup routes
- Location-specific trends and patterns

---

## 🎯 Pro Tips

1. **Start with Quick Analysis**: `python3 master_scraper.py --quick`
2. **Set Up Monitoring First**: Use `--setup-monitoring` with your locations
3. **Run Full Analysis Weekly**: `python3 master_scraper.py --all --pages 20`
4. **Check Dashboard Daily**: `python3 master_scraper.py --dashboard`
5. **Focus on Your Locations**: Always use `--locations 17,20,28,34,36`

---

## 🔧 Dependencies

All scrapers require:
- `aiohttp` - Async HTTP requests
- `sqlite3` - Database storage (built-in)
- `asyncio` - Async operations (built-in)
- `json` - Data parsing (built-in)
- `datetime` - Time handling (built-in)

Install with:
```bash
pip install aiohttp
```

---

## 📝 Output Files

- `master_scraper_summary.json` - Master scraper results
- `*.db` - SQLite databases for each scraper
- `locations_data.json` - Warehouse location data

---

**🎉 You now have the most comprehensive mac.bid analysis suite available!**

Each scraper provides unique insights that, when combined, give you a massive competitive advantage in finding the best deals and optimal bidding strategies. 