#!/usr/bin/env python3
"""
🔮 PREDICTIVE ANALYTICS - Demand Forecasting & Price Prediction
Advanced analytics for predicting market movements, optimal bidding times, and demand patterns
"""

import sqlite3
import json
import numpy as np
from datetime import datetime, timedelta
import statistics
from collections import defaultdict, Counter
import argparse
import math

class PredictiveAnalytics:
    def __init__(self, db_path="predictive_analytics.db"):
        self.db_path = db_path
        self.setup_database()
        
    def setup_database(self):
        """Setup predictive analytics database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS demand_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_date DATE DEFAULT CURRENT_DATE,
                category TEXT,
                brand TEXT,
                location TEXT,
                
                -- Demand Predictions
                predicted_demand_score REAL,
                demand_trend TEXT,  -- RISING, FALLING, STABLE
                demand_confidence REAL,
                
                -- Price Predictions
                predicted_avg_price REAL,
                predicted_discount_range TEXT,  -- JSON array [min, max]
                price_trend TEXT,  -- RISING, FALLING, STABLE
                price_confidence REAL,
                
                -- Volume Predictions
                predicted_auction_volume INTEGER,
                predicted_competition_level TEXT,  -- HIGH, MEDIUM, LOW
                
                -- Timing Predictions
                optimal_bidding_windows TEXT,  -- JSON array of time windows
                peak_activity_periods TEXT,    -- JSON array of peak periods
                
                -- Model Performance
                model_accuracy REAL,
                data_points_used INTEGER,
                forecast_horizon_days INTEGER DEFAULT 7,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_date DATE DEFAULT CURRENT_DATE,
                lot_id TEXT,
                product_name TEXT,
                category TEXT,
                brand TEXT,
                
                -- Current State
                current_retail_price REAL,
                current_instant_win_price REAL,
                current_bid REAL,
                
                -- Predictions
                predicted_final_price REAL,
                predicted_winning_bid REAL,
                predicted_discount_percent REAL,
                
                -- Confidence Metrics
                prediction_confidence REAL,
                price_volatility_score REAL,
                market_sentiment_score REAL,
                
                -- Factors
                demand_factor REAL,
                competition_factor REAL,
                timing_factor REAL,
                brand_factor REAL,
                
                -- Recommendations
                recommended_bid_min REAL,
                recommended_bid_max REAL,
                optimal_bid_timing TEXT,
                
                prediction_horizon_hours INTEGER DEFAULT 24,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seasonal_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_date DATE DEFAULT CURRENT_DATE,
                period_type TEXT,  -- WEEKLY, MONTHLY, QUARTERLY
                category TEXT,
                brand TEXT,
                
                -- Seasonal Patterns
                seasonal_strength REAL,
                peak_season_months TEXT,  -- JSON array
                low_season_months TEXT,   -- JSON array
                
                -- Predictions
                next_peak_period TEXT,
                next_low_period TEXT,
                seasonal_price_multiplier REAL,
                seasonal_demand_multiplier REAL,
                
                -- Recommendations
                buy_recommendations TEXT,   -- JSON array
                sell_recommendations TEXT,  -- JSON array
                inventory_recommendations TEXT,  -- JSON array
                
                confidence_score REAL,
                years_of_data_used INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def load_historical_data(self):
        """Load historical data from other system databases."""
        historical_data = {
            'market_data': [],
            'price_data': [],
            'bid_data': [],
            'timing_data': []
        }
        
        # Load from market intelligence database
        try:
            conn = sqlite3.connect("market_intelligence.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category, brand, auction_location, retail_price, 
                       instant_win_price, current_bid, total_bids, unique_bidders,
                       recorded_at
                FROM market_data 
                WHERE recorded_at > datetime('now', '-90 days')
                ORDER BY recorded_at
            ''')
            
            historical_data['market_data'] = cursor.fetchall()
            conn.close()
            
        except sqlite3.OperationalError:
            print("⚠️ Market intelligence database not found")
            
        # Load from price analytics database
        try:
            conn = sqlite3.connect("price_analytics.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category, brand, retail_price, instant_win_price,
                       discount_percent, value_score, recorded_at
                FROM price_analytics 
                WHERE recorded_at > datetime('now', '-90 days')
                ORDER BY recorded_at
            ''')
            
            historical_data['price_data'] = cursor.fetchall()
            conn.close()
            
        except sqlite3.OperationalError:
            print("⚠️ Price analytics database not found")
            
        return historical_data
        
    def calculate_demand_forecast(self, category, brand=None, location=None, days_ahead=7):
        """Calculate demand forecast for specific category/brand/location."""
        historical_data = self.load_historical_data()
        
        if not historical_data['market_data']:
            return self.generate_baseline_forecast(category, brand, location, days_ahead)
            
        # Filter data for specific category/brand/location
        filtered_data = []
        for row in historical_data['market_data']:
            cat, br, loc, retail, instant_win, current_bid, total_bids, unique_bidders, recorded_at = row
            
            if cat == category:
                if brand is None or br == brand:
                    if location is None or loc == location:
                        filtered_data.append(row)
                        
        if len(filtered_data) < 10:
            return self.generate_baseline_forecast(category, brand, location, days_ahead)
            
        # Calculate demand metrics
        recent_data = filtered_data[-30:]  # Last 30 data points
        older_data = filtered_data[-60:-30] if len(filtered_data) >= 60 else []
        
        # Demand indicators
        avg_bidders_recent = statistics.mean([row[7] for row in recent_data if row[7] > 0])
        avg_bids_recent = statistics.mean([row[6] for row in recent_data if row[6] > 0])
        
        if older_data:
            avg_bidders_older = statistics.mean([row[7] for row in older_data if row[7] > 0])
            avg_bids_older = statistics.mean([row[6] for row in older_data if row[6] > 0])
            
            # Calculate trends
            bidder_trend = (avg_bidders_recent - avg_bidders_older) / avg_bidders_older if avg_bidders_older > 0 else 0
            bid_trend = (avg_bids_recent - avg_bids_older) / avg_bids_older if avg_bids_older > 0 else 0
        else:
            bidder_trend = 0
            bid_trend = 0
            
        # Calculate demand score (0-100)
        base_demand = min((avg_bidders_recent * 10) + (avg_bids_recent * 5), 100)
        trend_adjustment = (bidder_trend + bid_trend) * 20
        demand_score = max(0, min(100, base_demand + trend_adjustment))
        
        # Determine trend direction
        if bidder_trend > 0.1 and bid_trend > 0.1:
            demand_trend = "RISING"
        elif bidder_trend < -0.1 and bid_trend < -0.1:
            demand_trend = "FALLING"
        else:
            demand_trend = "STABLE"
            
        # Calculate confidence based on data consistency
        bidder_variance = statistics.variance([row[7] for row in recent_data if row[7] > 0]) if len(recent_data) > 1 else 0
        confidence = max(0, min(100, 100 - (bidder_variance * 10)))
        
        return {
            'predicted_demand_score': demand_score,
            'demand_trend': demand_trend,
            'demand_confidence': confidence,
            'avg_bidders': avg_bidders_recent,
            'avg_bids': avg_bids_recent,
            'trend_strength': abs(bidder_trend + bid_trend) / 2,
            'data_points_used': len(filtered_data)
        }
        
    def generate_baseline_forecast(self, category, brand, location, days_ahead):
        """Generate baseline forecast when insufficient data."""
        # Category-based baseline scores
        category_baselines = {
            'Electronics': 75,
            'Audio': 65,
            'Gaming': 80,
            'Appliances': 55,
            'Tools': 60,
            'Photography': 70
        }
        
        base_score = category_baselines.get(category, 50)
        
        # Brand adjustments
        premium_brands = ['Apple', 'Sony', 'Samsung', 'Nintendo', 'Dyson', 'Bose']
        if brand in premium_brands:
            base_score += 15
            
        return {
            'predicted_demand_score': min(100, base_score),
            'demand_trend': "STABLE",
            'demand_confidence': 30,  # Low confidence for baseline
            'avg_bidders': 3,
            'avg_bids': 8,
            'trend_strength': 0,
            'data_points_used': 0
        }
        
    def predict_price_movement(self, lot_id, product_name, category, brand, 
                             retail_price, instant_win_price, current_bid=0):
        """Predict price movement and final auction price."""
        
        # Get demand forecast for this category/brand
        demand_forecast = self.calculate_demand_forecast(category, brand)
        
        # Calculate base prediction factors
        discount_percent = ((retail_price - instant_win_price) / retail_price * 100) if retail_price > 0 else 0
        
        # Demand factor (0-1)
        demand_factor = demand_forecast['predicted_demand_score'] / 100
        
        # Competition factor based on historical data
        competition_factor = min(1.0, demand_forecast['avg_bidders'] / 10)
        
        # Brand factor
        premium_brands = ['Apple', 'Sony', 'Samsung', 'Nintendo', 'Dyson', 'Bose']
        brand_factor = 1.2 if brand in premium_brands else 1.0
        
        # Timing factor (simplified - could be enhanced with actual timing data)
        timing_factor = 1.0  # Neutral for now
        
        # Calculate predicted final price
        base_prediction = instant_win_price
        
        # Apply demand pressure
        demand_pressure = demand_factor * 0.3  # Up to 30% increase from demand
        competition_pressure = competition_factor * 0.2  # Up to 20% from competition
        brand_premium = (brand_factor - 1) * 0.15  # Up to 15% brand premium
        
        total_pressure = demand_pressure + competition_pressure + brand_premium
        predicted_final_price = base_prediction * (1 + total_pressure)
        
        # Ensure it doesn't exceed retail price unreasonably
        predicted_final_price = min(predicted_final_price, retail_price * 0.85)
        
        # Calculate predicted winning bid (slightly lower than final price)
        predicted_winning_bid = predicted_final_price * 0.95
        
        # Calculate confidence based on data quality
        confidence = demand_forecast['demand_confidence'] * 0.7 + 30  # Base confidence
        
        # Price volatility score
        volatility = abs(discount_percent - 50) / 50  # Higher volatility for extreme discounts
        
        # Market sentiment (based on demand trend)
        sentiment_scores = {"RISING": 80, "STABLE": 50, "FALLING": 20}
        sentiment_score = sentiment_scores.get(demand_forecast['demand_trend'], 50)
        
        # Recommended bid range
        recommended_min = predicted_winning_bid * 0.8
        recommended_max = predicted_winning_bid * 1.1
        
        return {
            'predicted_final_price': predicted_final_price,
            'predicted_winning_bid': predicted_winning_bid,
            'predicted_discount_percent': ((retail_price - predicted_final_price) / retail_price * 100) if retail_price > 0 else 0,
            'prediction_confidence': confidence,
            'price_volatility_score': volatility * 100,
            'market_sentiment_score': sentiment_score,
            'demand_factor': demand_factor,
            'competition_factor': competition_factor,
            'timing_factor': timing_factor,
            'brand_factor': brand_factor,
            'recommended_bid_min': recommended_min,
            'recommended_bid_max': recommended_max,
            'optimal_bid_timing': "EARLY" if demand_forecast['demand_trend'] == "RISING" else "LATE"
        }
        
    def analyze_seasonal_patterns(self, category, brand=None):
        """Analyze seasonal patterns for category/brand."""
        historical_data = self.load_historical_data()
        
        if not historical_data['market_data']:
            return self.generate_baseline_seasonal_forecast(category, brand)
            
        # Group data by month
        monthly_data = defaultdict(list)
        
        for row in historical_data['market_data']:
            cat, br, loc, retail, instant_win, current_bid, total_bids, unique_bidders, recorded_at = row
            
            if cat == category and (brand is None or br == brand):
                try:
                    date_obj = datetime.fromisoformat(recorded_at.replace('Z', ''))
                    month = date_obj.month
                    monthly_data[month].append({
                        'retail_price': retail,
                        'instant_win_price': instant_win,
                        'bidders': unique_bidders,
                        'bids': total_bids
                    })
                except:
                    continue
                    
        if len(monthly_data) < 6:  # Need at least 6 months of data
            return self.generate_baseline_seasonal_forecast(category, brand)
            
        # Calculate monthly averages
        monthly_averages = {}
        for month, data in monthly_data.items():
            if len(data) >= 3:  # Need minimum data points per month
                avg_price = statistics.mean([d['retail_price'] for d in data if d['retail_price'] > 0])
                avg_bidders = statistics.mean([d['bidders'] for d in data if d['bidders'] > 0])
                monthly_averages[month] = {
                    'avg_price': avg_price,
                    'avg_bidders': avg_bidders,
                    'data_points': len(data)
                }
                
        if len(monthly_averages) < 4:
            return self.generate_baseline_seasonal_forecast(category, brand)
            
        # Identify patterns
        prices = [data['avg_price'] for data in monthly_averages.values()]
        bidders = [data['avg_bidders'] for data in monthly_averages.values()]
        
        price_variance = statistics.variance(prices) if len(prices) > 1 else 0
        bidder_variance = statistics.variance(bidders) if len(bidders) > 1 else 0
        
        # Calculate seasonal strength
        seasonal_strength = min(100, (price_variance + bidder_variance) * 10)
        
        # Identify peak and low periods
        sorted_months = sorted(monthly_averages.items(), key=lambda x: x[1]['avg_bidders'], reverse=True)
        peak_months = [month for month, _ in sorted_months[:3]]
        low_months = [month for month, _ in sorted_months[-3:]]
        
        # Generate recommendations
        current_month = datetime.now().month
        
        buy_recommendations = []
        sell_recommendations = []
        
        if current_month in low_months:
            buy_recommendations.append("Current month shows historically low demand - good buying opportunity")
        if current_month in peak_months:
            sell_recommendations.append("Current month shows historically high demand - good selling opportunity")
            
        return {
            'seasonal_strength': seasonal_strength,
            'peak_season_months': peak_months,
            'low_season_months': low_months,
            'next_peak_period': self.get_next_period(peak_months),
            'next_low_period': self.get_next_period(low_months),
            'seasonal_price_multiplier': max(prices) / min(prices) if prices else 1.0,
            'seasonal_demand_multiplier': max(bidders) / min(bidders) if bidders else 1.0,
            'buy_recommendations': buy_recommendations,
            'sell_recommendations': sell_recommendations,
            'confidence_score': min(100, len(monthly_averages) * 15),
            'months_of_data': len(monthly_averages)
        }
        
    def generate_baseline_seasonal_forecast(self, category, brand):
        """Generate baseline seasonal forecast."""
        # Category-specific seasonal patterns (simplified)
        seasonal_patterns = {
            'Electronics': {'peak': [11, 12, 1], 'low': [6, 7, 8]},  # Holiday season
            'Gaming': {'peak': [11, 12, 1], 'low': [6, 7, 8]},
            'Tools': {'peak': [3, 4, 5], 'low': [11, 12, 1]},  # Spring season
            'Appliances': {'peak': [9, 10, 11], 'low': [2, 3, 4]},  # Fall season
            'Audio': {'peak': [11, 12, 1], 'low': [6, 7, 8]}
        }
        
        pattern = seasonal_patterns.get(category, {'peak': [11, 12], 'low': [6, 7]})
        
        return {
            'seasonal_strength': 40,  # Moderate baseline
            'peak_season_months': pattern['peak'],
            'low_season_months': pattern['low'],
            'next_peak_period': self.get_next_period(pattern['peak']),
            'next_low_period': self.get_next_period(pattern['low']),
            'seasonal_price_multiplier': 1.3,
            'seasonal_demand_multiplier': 1.5,
            'buy_recommendations': ["Monitor for seasonal patterns"],
            'sell_recommendations': ["Track demand cycles"],
            'confidence_score': 25,  # Low confidence for baseline
            'months_of_data': 0
        }
        
    def get_next_period(self, months):
        """Get next occurrence of seasonal period."""
        current_month = datetime.now().month
        
        # Find next month in the list
        future_months = [m for m in months if m > current_month]
        if future_months:
            next_month = min(future_months)
        else:
            next_month = min(months)  # Next year
            
        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }
        
        return month_names.get(next_month, "Unknown")
        
    def generate_predictive_report(self, category=None, brand=None, location=None):
        """Generate comprehensive predictive analytics report."""
        print("🔮 PREDICTIVE ANALYTICS REPORT")
        print("="*60)
        
        # Demand Forecast
        print(f"\n📊 DEMAND FORECAST")
        print("-" * 40)
        
        demand_forecast = self.calculate_demand_forecast(category or "Electronics", brand, location)
        
        trend_icons = {"RISING": "📈", "FALLING": "📉", "STABLE": "➡️"}
        trend_icon = trend_icons.get(demand_forecast['demand_trend'], "➡️")
        
        print(f"Demand Score: {demand_forecast['predicted_demand_score']:.1f}/100")
        print(f"Trend: {trend_icon} {demand_forecast['demand_trend']}")
        print(f"Confidence: {demand_forecast['demand_confidence']:.1f}%")
        print(f"Avg Bidders: {demand_forecast['avg_bidders']:.1f}")
        print(f"Data Points: {demand_forecast['data_points_used']}")
        
        # Seasonal Analysis
        print(f"\n🗓️ SEASONAL ANALYSIS")
        print("-" * 40)
        
        seasonal_forecast = self.analyze_seasonal_patterns(category or "Electronics", brand)
        
        print(f"Seasonal Strength: {seasonal_forecast['seasonal_strength']:.1f}/100")
        print(f"Peak Months: {', '.join(map(str, seasonal_forecast['peak_season_months']))}")
        print(f"Low Months: {', '.join(map(str, seasonal_forecast['low_season_months']))}")
        print(f"Next Peak: {seasonal_forecast['next_peak_period']}")
        print(f"Price Multiplier: {seasonal_forecast['seasonal_price_multiplier']:.2f}x")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 40)
        
        if demand_forecast['demand_trend'] == "RISING":
            print("🔥 Demand is rising - consider aggressive bidding")
        elif demand_forecast['demand_trend'] == "FALLING":
            print("❄️ Demand is falling - wait for better opportunities")
        else:
            print("⚖️ Demand is stable - normal bidding strategy")
            
        if seasonal_forecast['buy_recommendations']:
            print("\n📥 Buy Recommendations:")
            for rec in seasonal_forecast['buy_recommendations']:
                print(f"   • {rec}")
                
        if seasonal_forecast['sell_recommendations']:
            print("\n📤 Sell Recommendations:")
            for rec in seasonal_forecast['sell_recommendations']:
                print(f"   • {rec}")
                
        # Sample Price Prediction
        print(f"\n💰 SAMPLE PRICE PREDICTION")
        print("-" * 40)
        
        sample_prediction = self.predict_price_movement(
            "SAMPLE123", "Sample Product", category or "Electronics", brand or "Apple",
            1000, 600, 0
        )
        
        print(f"Predicted Final Price: ${sample_prediction['predicted_final_price']:.2f}")
        print(f"Predicted Winning Bid: ${sample_prediction['predicted_winning_bid']:.2f}")
        print(f"Confidence: {sample_prediction['prediction_confidence']:.1f}%")
        print(f"Recommended Bid Range: ${sample_prediction['recommended_bid_min']:.2f} - ${sample_prediction['recommended_bid_max']:.2f}")
        print(f"Optimal Timing: {sample_prediction['optimal_bid_timing']}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="🔮 Predictive Analytics")
    parser.add_argument("--report", action="store_true", help="Generate predictive report")
    parser.add_argument("--demand", action="store_true", help="Show demand forecast")
    parser.add_argument("--seasonal", action="store_true", help="Show seasonal analysis")
    parser.add_argument("--price-predict", action="store_true", help="Predict price for sample item")
    parser.add_argument("--category", help="Category to analyze")
    parser.add_argument("--brand", help="Brand to analyze")
    parser.add_argument("--location", help="Location to analyze")
    
    args = parser.parse_args()
    
    analytics = PredictiveAnalytics()
    
    if args.demand:
        forecast = analytics.calculate_demand_forecast(
            args.category or "Electronics", args.brand, args.location
        )
        print("\n📊 DEMAND FORECAST")
        print("="*40)
        print(json.dumps(forecast, indent=2))
        
    elif args.seasonal:
        seasonal = analytics.analyze_seasonal_patterns(
            args.category or "Electronics", args.brand
        )
        print("\n🗓️ SEASONAL ANALYSIS")
        print("="*40)
        print(json.dumps(seasonal, indent=2, default=str))
        
    elif args.price_predict:
        prediction = analytics.predict_price_movement(
            "SAMPLE123", "Sample Product", args.category or "Electronics", 
            args.brand or "Apple", 1000, 600, 0
        )
        print("\n💰 PRICE PREDICTION")
        print("="*40)
        print(json.dumps(prediction, indent=2))
        
    else:
        analytics.generate_predictive_report(args.category, args.brand, args.location)

if __name__ == "__main__":
    main() 