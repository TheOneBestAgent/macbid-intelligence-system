#!/usr/bin/env python3
"""
Predictive Pricing Model for Mac.bid Auctions
Uses machine learning to predict final sale prices and optimal bidding strategies
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Tuple, Optional
import pickle
import warnings
warnings.filterwarnings('ignore')

# Machine Learning imports
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    ML_AVAILABLE = True
except ImportError:
    print("⚠️  Scikit-learn not available. Install with: pip install scikit-learn")
    ML_AVAILABLE = False

class PredictivePricingModel:
    def __init__(self):
        self.db_path = "databases/predictive_pricing.db"
        self.model_path = "databases/pricing_models"
        self.setup_database()
        
        # Model components
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_columns = []
        
        # Model configuration
        if ML_AVAILABLE:
            self.model_types = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'linear': LinearRegression()
            }
        else:
            self.model_types = {}
        
        # Ensure model directory exists
        os.makedirs(self.model_path, exist_ok=True)
    
    def setup_database(self):
        """Setup database for historical data and predictions"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Historical auction results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_auctions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER,
                auction_id INTEGER,
                lot_number TEXT,
                product_name TEXT,
                brand TEXT,
                category TEXT,
                condition_name TEXT,
                retail_price REAL,
                starting_bid REAL,
                final_price REAL,
                instant_win_price REAL,
                total_bids INTEGER,
                unique_bidders INTEGER,
                auction_duration_hours REAL,
                warehouse_location TEXT,
                dimensions TEXT,
                is_tested INTEGER,
                has_damage INTEGER,
                closing_date TEXT,
                day_of_week INTEGER,
                hour_of_day INTEGER,
                month INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Price predictions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER,
                auction_id INTEGER,
                predicted_price REAL,
                confidence_score REAL,
                model_used TEXT,
                prediction_factors TEXT,
                actual_price REAL,
                prediction_accuracy REAL,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                auction_end_date TEXT
            )
        ''')
        
        # Bidding strategies
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bidding_strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER,
                auction_id INTEGER,
                strategy_type TEXT,
                recommended_max_bid REAL,
                optimal_bid_time TEXT,
                win_probability REAL,
                expected_roi REAL,
                risk_level TEXT,
                strategy_factors TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Model performance tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                training_date DATETIME,
                training_samples INTEGER,
                mae REAL,
                rmse REAL,
                r2_score REAL,
                cross_val_score REAL,
                feature_importance TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def extract_features(self, lot_data: Dict) -> Dict:
        """Extract features from lot data for ML model"""
        features = {}
        
        # Basic features
        features['retail_price'] = lot_data.get('retail_price', 0)
        features['instant_win_price'] = lot_data.get('instant_win_price', 0)
        features['unique_bidders'] = lot_data.get('unique_bidders', 0)
        features['total_bids'] = lot_data.get('total_bids', 0)
        
        # Price ratios
        if features['retail_price'] > 0:
            features['instant_win_ratio'] = features['instant_win_price'] / features['retail_price']
        else:
            features['instant_win_ratio'] = 0
        
        # Product features
        product_name = lot_data.get('product_name', '').upper()
        features['brand'] = self.extract_brand(product_name)
        features['category'] = self.extract_category(product_name)
        
        # Condition features
        features['condition_name'] = lot_data.get('condition_name', 'UNKNOWN')
        features['is_tested'] = 1 if lot_data.get('is_tested') else 0
        features['has_damage'] = 1 if lot_data.get('damaged_note') else 0
        
        # Location features
        features['warehouse_location'] = lot_data.get('warehouse_location', 'UNKNOWN')
        
        # Timing features
        close_date = lot_data.get('expected_close_date')
        if close_date:
            try:
                dt = datetime.fromisoformat(close_date.replace('Z', '+00:00'))
                features['day_of_week'] = dt.weekday()
                features['hour_of_day'] = dt.hour
                features['month'] = dt.month
            except:
                features['day_of_week'] = 0
                features['hour_of_day'] = 18
                features['month'] = 1
        else:
            features['day_of_week'] = 0
            features['hour_of_day'] = 18
            features['month'] = 1
        
        # Competition features
        features['bidder_competition'] = min(features['unique_bidders'] / 10.0, 1.0)
        features['bid_intensity'] = features['total_bids'] / max(features['unique_bidders'], 1)
        
        return features
    
    def extract_brand(self, product_name: str) -> str:
        """Extract brand from product name"""
        brands = ['APPLE', 'SONY', 'SAMSUNG', 'NINTENDO', 'DYSON', 'BOSE', 
                 'DEWALT', 'MILWAUKEE', 'ECOVACS', 'ROOMBA', 'SHARK', 'BISSELL']
        
        for brand in brands:
            if brand in product_name:
                return brand
        return 'OTHER'
    
    def extract_category(self, product_name: str) -> str:
        """Extract category from product name"""
        categories = {
            'ELECTRONICS': ['IPHONE', 'IPAD', 'MACBOOK', 'TV', 'SPEAKER', 'HEADPHONE', 'CAMERA'],
            'GAMING': ['NINTENDO', 'XBOX', 'PLAYSTATION', 'SWITCH', 'GAME'],
            'APPLIANCES': ['VACUUM', 'CLEANER', 'ROBOT', 'DYSON', 'SHARK', 'BISSELL'],
            'TOOLS': ['DEWALT', 'MILWAUKEE', 'DRILL', 'SAW', 'TOOL'],
            'AUDIO': ['SPEAKER', 'HEADPHONE', 'BOSE', 'SONY', 'BEATS']
        }
        
        for category, keywords in categories.items():
            if any(keyword in product_name for keyword in keywords):
                return category
        return 'OTHER'
    
    def prepare_training_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data from historical auctions"""
        conn = sqlite3.connect(self.db_path)
        
        # Get historical data
        query = '''
            SELECT * FROM historical_auctions 
            WHERE final_price > 0 AND retail_price > 0
            ORDER BY closing_date DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("⚠️  No historical data available for training")
            return pd.DataFrame(), pd.Series()
        
        # Prepare features
        feature_columns = [
            'retail_price', 'instant_win_price', 'unique_bidders', 'total_bids',
            'instant_win_ratio', 'is_tested', 'has_damage', 'day_of_week',
            'hour_of_day', 'month', 'bidder_competition', 'bid_intensity'
        ]
        
        # Calculate derived features
        df['instant_win_ratio'] = df['instant_win_price'] / df['retail_price'].replace(0, 1)
        df['bidder_competition'] = np.minimum(df['unique_bidders'] / 10.0, 1.0)
        df['bid_intensity'] = df['total_bids'] / df['unique_bidders'].replace(0, 1)
        
        # Encode categorical features
        categorical_features = ['brand', 'category', 'condition_name', 'warehouse_location']
        
        for feature in categorical_features:
            if feature in df.columns:
                le = LabelEncoder()
                df[f'{feature}_encoded'] = le.fit_transform(df[feature].fillna('UNKNOWN'))
                feature_columns.append(f'{feature}_encoded')
                self.encoders[feature] = le
        
        # Select features and target
        X = df[feature_columns].fillna(0)
        y = df['final_price']
        
        self.feature_columns = feature_columns
        
        return X, y
    
    def train_models(self) -> Dict:
        """Train multiple ML models for price prediction"""
        if not ML_AVAILABLE:
            print("❌ Machine learning libraries not available")
            return {}
        
        print("🤖 Training predictive pricing models...")
        
        X, y = self.prepare_training_data()
        
        if X.empty:
            print("❌ No training data available")
            return {}
        
        print(f"📊 Training on {len(X)} historical auctions")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['main'] = scaler
        
        results = {}
        
        # Train each model type
        for model_name, model in self.model_types.items():
            print(f"  Training {model_name}...")
            
            try:
                # Train model
                if model_name == 'linear':
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                
                # Calculate metrics
                mae = mean_absolute_error(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                r2 = r2_score(y_test, y_pred)
                
                # Cross validation
                if model_name == 'linear':
                    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
                else:
                    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
                
                cv_mean = cv_scores.mean()
                
                # Feature importance
                if hasattr(model, 'feature_importances_'):
                    feature_importance = dict(zip(self.feature_columns, model.feature_importances_))
                else:
                    feature_importance = {}
                
                results[model_name] = {
                    'mae': mae,
                    'rmse': rmse,
                    'r2_score': r2,
                    'cv_score': cv_mean,
                    'feature_importance': feature_importance
                }
                
                # Save model
                self.models[model_name] = model
                
                # Save to database
                self.save_model_performance(model_name, len(X_train), mae, rmse, r2, cv_mean, feature_importance)
                
                print(f"    ✅ {model_name}: R² = {r2:.3f}, MAE = ${mae:.2f}, RMSE = ${rmse:.2f}")
                
            except Exception as e:
                print(f"    ❌ Error training {model_name}: {e}")
                results[model_name] = {'error': str(e)}
        
        # Save models to disk
        self.save_models_to_disk()
        
        return results
    
    def predict_price(self, lot_data: Dict, model_name: str = 'simple') -> Dict:
        """Predict final price for a lot using simple heuristics"""
        # Extract features
        features = self.extract_features(lot_data)
        
        # Simple prediction based on heuristics (fallback when ML not available)
        retail_price = features.get('retail_price', 0)
        instant_win_price = features.get('instant_win_price', 0)
        unique_bidders = features.get('unique_bidders', 0)
        
        # Base prediction on instant win price with adjustments
        if instant_win_price > 0:
            base_prediction = instant_win_price * 0.7  # Typically sells for 70% of instant win
        elif retail_price > 0:
            base_prediction = retail_price * 0.4  # Typically sells for 40% of retail
        else:
            base_prediction = 50  # Default minimum
        
        # Adjust for competition
        competition_multiplier = 1.0 + (unique_bidders * 0.05)  # 5% increase per bidder
        predicted_price = base_prediction * competition_multiplier
        
        # Adjust for condition
        if features.get('has_damage'):
            predicted_price *= 0.8  # 20% discount for damage
        
        if not features.get('is_tested'):
            predicted_price *= 0.9  # 10% discount for untested
        
        # Calculate confidence score
        confidence_score = self.calculate_confidence(features, model_name)
        
        # Generate prediction factors
        prediction_factors = self.analyze_prediction_factors(features, model_name)
        
        return {
            'predicted_price': max(0, predicted_price),
            'confidence_score': confidence_score,
            'model_used': model_name,
            'prediction_factors': prediction_factors,
            'features_used': features
        }
    
    def calculate_confidence(self, features: Dict, model_name: str) -> float:
        """Calculate confidence score for prediction"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on data quality
        if features.get('retail_price', 0) > 0:
            confidence += 0.1
        
        if features.get('unique_bidders', 0) > 0:
            confidence += 0.1
        
        if features.get('brand') != 'OTHER':
            confidence += 0.1
        
        if features.get('is_tested', 0) == 1:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def analyze_prediction_factors(self, features: Dict, model_name: str) -> Dict:
        """Analyze factors influencing the prediction"""
        factors = {}
        
        # Price factors
        retail_price = features.get('retail_price', 0)
        instant_win_price = features.get('instant_win_price', 0)
        
        if retail_price > 0 and instant_win_price > 0:
            discount = ((retail_price - instant_win_price) / retail_price) * 100
            factors['discount_percentage'] = discount
            
            if discount > 50:
                factors['price_attractiveness'] = 'HIGH'
            elif discount > 30:
                factors['price_attractiveness'] = 'MEDIUM'
            else:
                factors['price_attractiveness'] = 'LOW'
        
        # Competition factors
        bidders = features.get('unique_bidders', 0)
        if bidders > 10:
            factors['competition_level'] = 'HIGH'
        elif bidders > 5:
            factors['competition_level'] = 'MEDIUM'
        else:
            factors['competition_level'] = 'LOW'
        
        # Brand factors
        brand = features.get('brand', 'OTHER')
        premium_brands = ['APPLE', 'SONY', 'SAMSUNG', 'NINTENDO', 'DYSON', 'BOSE']
        factors['brand_premium'] = brand in premium_brands
        
        # Condition factors
        factors['condition_risk'] = features.get('has_damage', 0) == 1
        factors['tested_status'] = features.get('is_tested', 0) == 1
        
        return factors
    
    def generate_bidding_strategy(self, lot_data: Dict, max_budget: float = None) -> Dict:
        """Generate optimal bidding strategy for a lot"""
        # Get price prediction
        prediction = self.predict_price(lot_data)
        
        if 'error' in prediction:
            return prediction
        
        predicted_price = prediction['predicted_price']
        confidence = prediction['confidence_score']
        
        # Calculate recommended max bid
        retail_price = lot_data.get('retail_price', 0)
        instant_win_price = lot_data.get('instant_win_price', 0)
        
        # Base recommendation on predicted price with safety margin
        safety_margin = 1.0 - (confidence * 0.3)  # Lower confidence = higher margin
        recommended_max_bid = predicted_price * safety_margin
        
        # Apply budget constraint
        if max_budget:
            recommended_max_bid = min(recommended_max_bid, max_budget)
        
        # Calculate win probability
        win_probability = self.calculate_win_probability(lot_data, recommended_max_bid)
        
        # Calculate expected ROI
        if recommended_max_bid > 0:
            expected_roi = ((retail_price - recommended_max_bid) / recommended_max_bid) * 100
        else:
            expected_roi = 0
        
        # Determine risk level
        risk_factors = []
        if lot_data.get('damaged_note'):
            risk_factors.append('DAMAGE')
        if not lot_data.get('is_tested'):
            risk_factors.append('UNTESTED')
        if lot_data.get('unique_bidders', 0) > 10:
            risk_factors.append('HIGH_COMPETITION')
        
        if len(risk_factors) >= 2:
            risk_level = 'HIGH'
        elif len(risk_factors) == 1:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        # Determine strategy type
        if expected_roi > 50 and risk_level == 'LOW':
            strategy_type = 'AGGRESSIVE'
        elif expected_roi > 30 and risk_level in ['LOW', 'MEDIUM']:
            strategy_type = 'MODERATE'
        elif expected_roi > 15:
            strategy_type = 'CONSERVATIVE'
        else:
            strategy_type = 'AVOID'
        
        # Optimal bid timing
        close_date = lot_data.get('expected_close_date')
        if close_date:
            optimal_bid_time = 'LAST_5_MINUTES'  # Generally optimal for auctions
        else:
            optimal_bid_time = 'UNKNOWN'
        
        strategy = {
            'strategy_type': strategy_type,
            'recommended_max_bid': recommended_max_bid,
            'optimal_bid_time': optimal_bid_time,
            'win_probability': win_probability,
            'expected_roi': expected_roi,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'predicted_price': predicted_price,
            'confidence_score': confidence
        }
        
        # Save strategy to database
        self.save_bidding_strategy(lot_data, strategy)
        
        return strategy
    
    def calculate_win_probability(self, lot_data: Dict, bid_amount: float) -> float:
        """Calculate probability of winning with given bid amount"""
        instant_win_price = lot_data.get('instant_win_price', 0)
        unique_bidders = lot_data.get('unique_bidders', 0)
        
        # Base probability on bid amount vs instant win price
        if instant_win_price > 0:
            bid_ratio = bid_amount / instant_win_price
            base_probability = min(bid_ratio, 1.0)
        else:
            base_probability = 0.5
        
        # Adjust for competition
        competition_factor = max(0.1, 1.0 - (unique_bidders * 0.05))
        
        win_probability = base_probability * competition_factor
        
        return min(win_probability, 0.95)  # Cap at 95%
    
    def save_model_performance(self, model_name: str, training_samples: int, 
                             mae: float, rmse: float, r2: float, cv_score: float, 
                             feature_importance: Dict):
        """Save model performance metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO model_performance 
            (model_name, training_date, training_samples, mae, rmse, r2_score, 
             cross_val_score, feature_importance)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
        ''', (model_name, training_samples, mae, rmse, r2, cv_score, 
              json.dumps(feature_importance)))
        
        conn.commit()
        conn.close()
    
    def save_bidding_strategy(self, lot_data: Dict, strategy: Dict):
        """Save bidding strategy to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bidding_strategies 
            (lot_id, auction_id, strategy_type, recommended_max_bid, 
             optimal_bid_time, win_probability, expected_roi, risk_level, 
             strategy_factors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lot_data.get('id'),
            lot_data.get('auction_id'),
            strategy['strategy_type'],
            strategy['recommended_max_bid'],
            strategy['optimal_bid_time'],
            strategy['win_probability'],
            strategy['expected_roi'],
            strategy['risk_level'],
            json.dumps(strategy)
        ))
        
        conn.commit()
        conn.close()
    
    def save_models_to_disk(self):
        """Save trained models to disk"""
        model_data = {
            'models': self.models,
            'scalers': self.scalers,
            'encoders': self.encoders,
            'feature_columns': self.feature_columns
        }
        
        with open(f"{self.model_path}/pricing_models.pkl", 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Models saved to {self.model_path}/pricing_models.pkl")
    
    def load_models_from_disk(self) -> bool:
        """Load trained models from disk"""
        model_file = f"{self.model_path}/pricing_models.pkl"
        
        if not os.path.exists(model_file):
            return False
        
        try:
            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)
            
            self.models = model_data.get('models', {})
            self.scalers = model_data.get('scalers', {})
            self.encoders = model_data.get('encoders', {})
            self.feature_columns = model_data.get('feature_columns', [])
            
            print(f"✅ Models loaded from {model_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False

def main():
    """Main function for testing"""
    print("🤖 PREDICTIVE PRICING MODEL")
    print("="*50)
    
    model = PredictivePricingModel()
    
    # Test prediction with sample lot
    test_lot = {
        'id': 35863830,
        'auction_id': 48796,
        'product_name': 'ECOVACS DEEBOT X8 PRO OMNI Robot Vacuum and Mop',
        'retail_price': 1299.99,
        'instant_win_price': 1040.00,
        'unique_bidders': 6,
        'total_bids': 0,
        'condition_name': 'OPEN BOX',
        'is_tested': True,
        'damaged_note': 'Very dirty - lots of moisture',
        'expected_close_date': '2025-06-15T18:30:20.000Z'
    }
    
    print(f"\n🔮 PRICE PREDICTION TEST")
    print(f"Product: {test_lot['product_name']}")
    print(f"Retail: ${test_lot['retail_price']:,.2f}")
    print(f"Instant Win: ${test_lot['instant_win_price']:,.2f}")
    
    prediction = model.predict_price(test_lot)
    print(f"\n📊 Prediction Results:")
    print(f"Predicted Price: ${prediction.get('predicted_price', 0):,.2f}")
    print(f"Confidence: {prediction.get('confidence_score', 0):.1%}")
    print(f"Model Used: {prediction.get('model_used', 'N/A')}")
    
    # Generate bidding strategy
    strategy = model.generate_bidding_strategy(test_lot, max_budget=800)
    print(f"\n🎯 BIDDING STRATEGY:")
    print(f"Strategy Type: {strategy.get('strategy_type', 'N/A')}")
    print(f"Recommended Max Bid: ${strategy.get('recommended_max_bid', 0):,.2f}")
    print(f"Win Probability: {strategy.get('win_probability', 0):.1%}")
    print(f"Expected ROI: {strategy.get('expected_roi', 0):,.1f}%")
    print(f"Risk Level: {strategy.get('risk_level', 'N/A')}")

if __name__ == "__main__":
    main() 