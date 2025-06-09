# System Patterns

## Architecture Overview
The advanced analytics scraper suite follows a modular, specialized analytics architecture:

```
[Mac.bid API] → [Analytics Scrapers] → [Data Processing] → [Intelligence Generation] → [Alerts & Reports]
```

## Core Analytics Modules

### 1. Price Analytics Tracker (`price_analytics_tracker.py`)
- **Purpose**: Monitor pricing trends and detect market anomalies
- **Technology**: aiohttp for async API calls, SQLite for historical data
- **Patterns**: 
  - Strategy pattern for different category analysis methods
  - Observer pattern for price anomaly detection

### 2. Advanced Product Search (`advanced_product_search.py`)
- **Purpose**: Intelligent product discovery and brand monitoring
- **Responsibilities**:
  - Premium brand tracking (Apple, Sony, Samsung, Nintendo, Dyson, Bose, DeWalt, Milwaukee)
  - Rarity scoring based on keywords and value patterns
  - Inventory level tracking by location
- **Patterns**: Factory pattern for brand-specific analysis

### 3. Auction Timing Analyzer (`auction_timing_analyzer.py`)
- **Purpose**: Identify optimal bidding times and competition patterns
- **Detection Methods**:
  - Time slot analysis (6 periods: Early Morning to Late Night)
  - Day-of-week competition scoring
  - Opportunity scoring based on competition vs discount ratios
- **Patterns**: Template method pattern for timing analysis algorithms

### 4. Winning Bid Pattern Analyzer (`winning_bid_analyzer.py`)
- **Purpose**: Analyze bidding patterns and identify sweet spots
- **Capabilities**:
  - Sweet spot scoring (optimal 30-60% of retail price range)
  - Competition level analysis (LOW/MEDIUM/HIGH)
  - Category opportunity rating (EXCELLENT/GOOD/FAIR/POOR)
- **Patterns**: Chain of responsibility for bid analysis methods

### 5. Enhanced New Arrivals Monitor (`enhanced_new_arrivals.py`)
- **Purpose**: Comprehensive monitoring combining all analytics modules
- **Integration**: Applies all 4 analytics to every new item
- **Patterns**: Facade pattern providing unified interface to all analytics

## Key Design Decisions

### Asynchronous API Processing
- Use aiohttp for concurrent API requests to mac.bid search endpoints
- Implement rate limiting (0.15-0.25 seconds between requests)
- Connection pooling with SSL context handling for certificate issues

### Modular Analytics Architecture
- Each analytics module operates independently
- Shared base patterns for API communication and data processing
- Enhanced monitor combines all modules for comprehensive analysis

### Data Persistence Strategy
- SQLite databases for each analytics module
- Separate schemas optimized for each analysis type
- Historical data retention for trend analysis

### Intelligent Alert System
- Multi-factor scoring combining price, timing, bid, and rarity analytics
- Severity levels (HIGH, MEDIUM, LOW) based on opportunity scores
- Alert categorization (PRICING, BRAND, BIDDING, TIMING, RARITY)

## Data Flow Architecture
1. **API Data Acquisition**: Fetch auction data from mac.bid search endpoints
2. **Parallel Analytics Processing**: Run specialized analysis on each item
3. **Data Enhancement**: Add calculated metrics (discounts, scores, ratings)
4. **Intelligence Synthesis**: Combine analytics for opportunity ranking
5. **Alert Generation**: Create intelligent alerts based on multi-factor analysis
6. **Report Output**: Generate formatted reports with actionable insights

## Analytics Patterns

### Price Analytics Pattern
```python
# Trend analysis with anomaly detection
def analyze_price_trends(items):
    by_category_location = group_items(items)
    for group in by_category_location:
        calculate_statistics(group)
        detect_anomalies(group)
        assign_trend_direction(group)
```

### Product Intelligence Pattern
```python
# Brand detection and rarity scoring
def analyze_product_intelligence(item):
    brand = extract_brand(item.product_name)
    rarity_score = calculate_rarity(item)
    priority = determine_priority(brand, rarity_score)
    return ProductIntelligence(brand, rarity_score, priority)
```

### Timing Optimization Pattern
```python
# Competition analysis by time periods
def analyze_timing_patterns(items):
    by_time_slot = group_by_time(items)
    for slot, slot_items in by_time_slot:
        competition_score = calculate_competition(slot_items)
        opportunity_score = calculate_opportunity(competition_score, discounts)
```

### Bid Strategy Pattern
```python
# Sweet spot identification
def analyze_bid_patterns(item):
    bid_ratio = current_bid / retail_price
    sweet_spot_score = calculate_sweet_spot(bid_ratio, retail_price)
    suggested_range = (retail_price * 0.3, retail_price * 0.6)
    return BidAnalysis(sweet_spot_score, suggested_range)
```

## Error Handling & Resilience
- Graceful handling of SSL certificate issues with custom SSL context
- Retry mechanisms for failed API requests
- Connection error recovery with exponential backoff
- Data validation and sanitization for all API responses

## Performance Optimization Patterns
- Concurrent request processing with connection limits (10-15 per session)
- Request deduplication by lot_id to avoid processing duplicates
- Memory-efficient data processing with streaming patterns
- Database connection pooling and prepared statements

## Configuration & Extensibility
- Configurable rate limiting and connection parameters
- Extensible category and brand definitions
- Customizable scoring algorithms and thresholds
- Pluggable alert generation rules

## Security & Compliance
- Respectful API usage with built-in rate limiting
- SSL certificate handling for secure connections
- Input validation and sanitization
- No sensitive data storage (read-only API access) 