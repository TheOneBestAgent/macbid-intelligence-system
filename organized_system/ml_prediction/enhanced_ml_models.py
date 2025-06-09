#!/usr/bin/env python3
"""
Enhanced ML Models with Historical Data
Advanced machine learning models for auction price prediction and bidding optimization
"""

import pandas as pd
import numpy as np
import sqlite3
import json
import pickle
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# ML imports
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.feature_selection import SelectKBest, f_regression
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️  ML libraries not available. Run: pip install scikit-learn pandas numpy")

@dataclass
class PredictionResult:
    lot_id: int
    predicted_final_price: float
    confidence_score: float
    price_range_low: float
    price_range_high: float
    optimal_bid: float
    win_probability: float
    model_used: str
    features_used: List[str]
    prediction_timestamp: str
    
@dataclass
class ModelPerformance:
    model_name: str
    mae: float  # Mean Absolute Error
    rmse: float  # Root Mean Square Error
    r2: float  # R-squared
    accuracy_within_10_percent: float
    accuracy_within_20_percent: float
    training_samples: int
    last_trained: str

class EnhancedMLModels:
    def __init__(self):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data_outputs/enhanced_ml_models.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_selectors = {}
        
        # Model configurations
        self.model_configs = {
            'random_forest': {
                'model': RandomForestRegressor(
                    n_estimators=100,
                    max_depth=15,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42
                ),
                'name': 'Random Forest'
            },
            'gradient_boosting': {
                'model': GradientBoostingRegressor(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42
                ),
                'name': 'Gradient Boosting'
            },
            'ridge_regression': {
                'model': Ridge(alpha=1.0),
                'name': 'Ridge Regression'
            }
        }
        
        # Initialize database
        self.init_database()
        
        # Performance tracking
        self.model_performance = {}
        
    def init_database(self):
        """Initialize ML models database"""
        os.makedirs('databases', exist_ok=True)
        
        self.conn = sqlite3.connect('databases/enhanced_ml_models.db')
        cursor = self.conn.cursor()
        
        # Historical auction data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_auctions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER NOT NULL,
                auction_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                brand TEXT NOT NULL,
                condition TEXT NOT NULL,
                starting_price REAL NOT NULL,
                final_price REAL NOT NULL,
                instant_win_price REAL NOT NULL,
                bidder_count INTEGER NOT NULL,
                bid_count INTEGER NOT NULL,
                auction_duration_hours REAL NOT NULL,
                day_of_week INTEGER NOT NULL,
                hour_of_day INTEGER NOT NULL,
                month INTEGER NOT NULL,
                is_weekend BOOLEAN NOT NULL,
                has_images BOOLEAN NOT NULL,
                description_length INTEGER NOT NULL,
                seller_rating REAL,
                location TEXT,
                shipping_cost REAL,
                created_at TEXT NOT NULL,
                ended_at TEXT NOT NULL
            )
        ''')
        
        # Model predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                predicted_price REAL NOT NULL,
                actual_price REAL,
                confidence_score REAL NOT NULL,
                prediction_error REAL,
                features_used TEXT NOT NULL,
                prediction_timestamp TEXT NOT NULL,
                actual_timestamp TEXT
            )
        ''')
        
        # Model performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                mae REAL NOT NULL,
                rmse REAL NOT NULL,
                r2 REAL NOT NULL,
                accuracy_10_percent REAL NOT NULL,
                accuracy_20_percent REAL NOT NULL,
                training_samples INTEGER NOT NULL,
                evaluation_date TEXT NOT NULL
            )
        ''')
        
        # Feature importance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feature_importance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                feature_name TEXT NOT NULL,
                importance_score REAL NOT NULL,
                rank INTEGER NOT NULL,
                evaluation_date TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
        self.logger.info("✅ Enhanced ML database initialized")
    
    def generate_synthetic_historical_data(self, num_samples: int = 1000) -> pd.DataFrame:
        """Generate synthetic historical auction data for training"""
        
        self.logger.info(f"🔄 Generating {num_samples} synthetic historical records...")
        
        np.random.seed(42)
        
        # Categories and brands
        categories = ['Electronics', 'Computers', 'Home & Garden', 'Clothing', 'Sports', 'Automotive']
        brands = ['Apple', 'Samsung', 'Sony', 'LG', 'Dell', 'HP', 'Nike', 'Adidas', 'Generic']
        conditions = ['New', 'Like New', 'Good', 'Fair', 'Poor']
        locations = ['Rock Hill', 'Gastonia', 'Charlotte', 'Columbia', 'Greenville']
        
        data = []
        
        for i in range(num_samples):
            # Basic attributes
            category = np.random.choice(categories)
            brand = np.random.choice(brands)
            condition = np.random.choice(conditions)
            location = np.random.choice(locations)
            
            # Price factors
            base_price = np.random.uniform(10, 2000)
            
            # Brand premium
            brand_multiplier = {
                'Apple': 1.5, 'Samsung': 1.3, 'Sony': 1.2, 'LG': 1.1,
                'Dell': 1.1, 'HP': 1.0, 'Nike': 1.2, 'Adidas': 1.1, 'Generic': 0.8
            }
            
            # Condition factor
            condition_multiplier = {
                'New': 1.0, 'Like New': 0.85, 'Good': 0.7, 'Fair': 0.5, 'Poor': 0.3
            }
            
            # Category factor
            category_multiplier = {
                'Electronics': 1.2, 'Computers': 1.3, 'Home & Garden': 0.9,
                'Clothing': 0.7, 'Sports': 0.8, 'Automotive': 1.1
            }
            
            # Calculate prices
            retail_price = base_price * brand_multiplier[brand] * category_multiplier[category]
            starting_price = retail_price * np.random.uniform(0.05, 0.3)
            
            # Auction dynamics
            bidder_count = np.random.poisson(8) + 1
            bid_count = bidder_count * np.random.poisson(2) + 1
            auction_duration = np.random.uniform(24, 168)  # 1-7 days
            
            # Time factors
            end_time = datetime.now() - timedelta(days=np.random.uniform(1, 365))
            day_of_week = end_time.weekday()
            hour_of_day = end_time.hour
            month = end_time.month
            is_weekend = day_of_week >= 5
            
            # Other factors
            has_images = np.random.choice([True, False], p=[0.8, 0.2])
            description_length = np.random.poisson(200) + 50
            seller_rating = np.random.uniform(3.0, 5.0)
            shipping_cost = np.random.uniform(5, 50)
            
            # Calculate final price with various factors
            competition_factor = min(1 + (bidder_count - 1) * 0.1, 2.0)
            time_factor = 1.1 if is_weekend else 1.0
            time_factor *= 1.05 if 18 <= hour_of_day <= 22 else 0.95  # Evening premium
            condition_factor = condition_multiplier[condition]
            image_factor = 1.1 if has_images else 0.9
            
            final_price = starting_price * competition_factor * time_factor * condition_factor * image_factor
            final_price *= np.random.uniform(0.8, 1.2)  # Add some randomness
            
            # Ensure final price is reasonable
            final_price = max(starting_price, min(final_price, retail_price * 0.8))
            
            data.append({
                'lot_id': 1000000 + i,
                'auction_id': 50000 + i,
                'product_name': f"{brand} {category} Item {i}",
                'category': category,
                'brand': brand,
                'condition': condition,
                'starting_price': round(starting_price, 2),
                'final_price': round(final_price, 2),
                'instant_win_price': round(retail_price, 2),
                'bidder_count': bidder_count,
                'bid_count': bid_count,
                'auction_duration_hours': round(auction_duration, 2),
                'day_of_week': day_of_week,
                'hour_of_day': hour_of_day,
                'month': month,
                'is_weekend': is_weekend,
                'has_images': has_images,
                'description_length': description_length,
                'seller_rating': round(seller_rating, 2),
                'location': location,
                'shipping_cost': round(shipping_cost, 2),
                'created_at': (end_time - timedelta(hours=auction_duration)).isoformat(),
                'ended_at': end_time.isoformat()
            })
        
        df = pd.DataFrame(data)
        
        # Store in database
        df.to_sql('historical_auctions', self.conn, if_exists='replace', index=False)
        
        self.logger.info(f"✅ Generated and stored {len(df)} historical records")
        return df
    
    def load_historical_data(self) -> pd.DataFrame:
        """Load historical auction data"""
        
        try:
            df = pd.read_sql_query("SELECT * FROM historical_auctions", self.conn)
            
            if len(df) == 0:
                self.logger.info("No historical data found, generating synthetic data...")
                df = self.generate_synthetic_historical_data()
            
            self.logger.info(f"📊 Loaded {len(df)} historical auction records")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            return self.generate_synthetic_historical_data()
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Prepare features for ML models"""
        
        self.logger.info("🔧 Preparing features for ML models...")
        
        # Create feature dataframe
        features_df = df.copy()
        
        # Encode categorical variables
        categorical_columns = ['category', 'brand', 'condition', 'location']
        
        for col in categorical_columns:
            if col not in self.encoders:
                self.encoders[col] = LabelEncoder()
                features_df[f'{col}_encoded'] = self.encoders[col].fit_transform(features_df[col])
            else:
                features_df[f'{col}_encoded'] = self.encoders[col].transform(features_df[col])
        
        # Create derived features
        features_df['price_per_bidder'] = features_df['starting_price'] / (features_df['bidder_count'] + 1)
        features_df['bids_per_bidder'] = features_df['bid_count'] / (features_df['bidder_count'] + 1)
        features_df['competition_intensity'] = features_df['bid_count'] / features_df['auction_duration_hours']
        features_df['starting_price_ratio'] = features_df['starting_price'] / features_df['instant_win_price']
        features_df['seller_rating_normalized'] = (features_df['seller_rating'] - 3.0) / 2.0
        features_df['description_length_log'] = np.log1p(features_df['description_length'])
        features_df['shipping_cost_ratio'] = features_df['shipping_cost'] / features_df['starting_price']
        
        # Time-based features
        features_df['is_prime_time'] = ((features_df['hour_of_day'] >= 18) & 
                                       (features_df['hour_of_day'] <= 22)).astype(int)
        features_df['is_holiday_season'] = ((features_df['month'] == 11) | 
                                           (features_df['month'] == 12)).astype(int)
        
        # Select feature columns
        feature_columns = [
            'starting_price', 'instant_win_price', 'bidder_count', 'bid_count',
            'auction_duration_hours', 'day_of_week', 'hour_of_day', 'month',
            'is_weekend', 'has_images', 'description_length', 'seller_rating',
            'shipping_cost', 'category_encoded', 'brand_encoded', 'condition_encoded',
            'location_encoded', 'price_per_bidder', 'bids_per_bidder',
            'competition_intensity', 'starting_price_ratio', 'seller_rating_normalized',
            'description_length_log', 'shipping_cost_ratio', 'is_prime_time',
            'is_holiday_season'
        ]
        
        # Ensure all columns exist
        available_columns = [col for col in feature_columns if col in features_df.columns]
        
        self.logger.info(f"✅ Prepared {len(available_columns)} features")
        return features_df[available_columns], available_columns
    
    def train_models(self) -> Dict[str, ModelPerformance]:
        """Train all ML models with historical data"""
        
        if not ML_AVAILABLE:
            self.logger.error("ML libraries not available")
            return {}
        
        self.logger.info("🤖 Training enhanced ML models...")
        
        # Load and prepare data
        df = self.load_historical_data()
        features_df, feature_columns = self.prepare_features(df)
        
        X = features_df
        y = df['final_price']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        self.scalers['main'] = StandardScaler()
        X_train_scaled = self.scalers['main'].fit_transform(X_train)
        X_test_scaled = self.scalers['main'].transform(X_test)
        
        # Feature selection
        self.feature_selectors['main'] = SelectKBest(f_regression, k=min(15, len(feature_columns)))
        X_train_selected = self.feature_selectors['main'].fit_transform(X_train_scaled, y_train)
        X_test_selected = self.feature_selectors['main'].transform(X_test_scaled)
        
        # Get selected feature names
        selected_features = [feature_columns[i] for i in self.feature_selectors['main'].get_support(indices=True)]
        
        performance_results = {}
        
        # Train each model
        for model_key, config in self.model_configs.items():
            try:
                self.logger.info(f"Training {config['name']}...")
                
                model = config['model']
                
                # Train model
                model.fit(X_train_selected, y_train)
                
                # Make predictions
                y_pred = model.predict(X_test_selected)
                
                # Calculate metrics
                mae = mean_absolute_error(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                r2 = r2_score(y_test, y_pred)
                
                # Calculate accuracy within percentage ranges
                percentage_errors = np.abs((y_test - y_pred) / y_test) * 100
                accuracy_10 = np.mean(percentage_errors <= 10) * 100
                accuracy_20 = np.mean(percentage_errors <= 20) * 100
                
                # Store model
                self.models[model_key] = model
                
                # Create performance object
                performance = ModelPerformance(
                    model_name=config['name'],
                    mae=mae,
                    rmse=rmse,
                    r2=r2,
                    accuracy_within_10_percent=accuracy_10,
                    accuracy_within_20_percent=accuracy_20,
                    training_samples=len(X_train),
                    last_trained=datetime.now().isoformat()
                )
                
                performance_results[model_key] = performance
                self.model_performance[model_key] = performance
                
                # Store performance in database
                self.store_model_performance(performance)
                
                # Store feature importance if available
                if hasattr(model, 'feature_importances_'):
                    self.store_feature_importance(config['name'], selected_features, model.feature_importances_)
                
                self.logger.info(f"✅ {config['name']} trained - R²: {r2:.3f}, MAE: ${mae:.2f}")
                
            except Exception as e:
                self.logger.error(f"❌ Error training {config['name']}: {e}")
        
        # Save models
        self.save_models()
        
        self.logger.info(f"🤖 Training complete! {len(performance_results)} models trained")
        return performance_results
    
    def store_model_performance(self, performance: ModelPerformance):
        """Store model performance in database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO model_performance 
            (model_name, mae, rmse, r2, accuracy_10_percent, accuracy_20_percent, training_samples, evaluation_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            performance.model_name, performance.mae, performance.rmse, performance.r2,
            performance.accuracy_within_10_percent, performance.accuracy_within_20_percent,
            performance.training_samples, performance.last_trained
        ))
        self.conn.commit()
    
    def store_feature_importance(self, model_name: str, features: List[str], importances: np.ndarray):
        """Store feature importance in database"""
        cursor = self.conn.cursor()
        
        # Clear existing importance for this model
        cursor.execute('DELETE FROM feature_importance WHERE model_name = ?', (model_name,))
        
        # Store new importance scores
        for rank, (feature, importance) in enumerate(sorted(zip(features, importances), 
                                                           key=lambda x: x[1], reverse=True)):
            cursor.execute('''
                INSERT INTO feature_importance 
                (model_name, feature_name, importance_score, rank, evaluation_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (model_name, feature, float(importance), rank + 1, datetime.now().isoformat()))
        
        self.conn.commit()
    
    def predict_auction_price(self, lot_data: Dict) -> PredictionResult:
        """Predict auction final price using ensemble of models"""
        
        if not self.models:
            self.logger.warning("No trained models available, training now...")
            self.train_models()
        
        try:
            # Prepare features for prediction
            features_dict = self.prepare_prediction_features(lot_data)
            
            # Get feature vector
            feature_vector = self.create_feature_vector(features_dict)
            
            # Make predictions with all models
            predictions = {}
            confidences = {}
            
            for model_key, model in self.models.items():
                try:
                    # Scale features
                    scaled_features = self.scalers['main'].transform([feature_vector])
                    selected_features = self.feature_selectors['main'].transform(scaled_features)
                    
                    # Make prediction
                    prediction = model.predict(selected_features)[0]
                    predictions[model_key] = prediction
                    
                    # Calculate confidence based on model performance
                    performance = self.model_performance.get(model_key)
                    if performance:
                        # Higher R² and lower error = higher confidence
                        confidence = performance.r2 * (1 - min(performance.mae / prediction, 0.5))
                        confidences[model_key] = max(0.1, min(confidence, 1.0))
                    else:
                        confidences[model_key] = 0.5
                        
                except Exception as e:
                    self.logger.warning(f"Error with model {model_key}: {e}")
                    continue
            
            if not predictions:
                raise Exception("No models could make predictions")
            
            # Ensemble prediction (weighted average)
            total_weight = sum(confidences.values())
            ensemble_prediction = sum(pred * confidences[key] for key, pred in predictions.items()) / total_weight
            ensemble_confidence = sum(confidences.values()) / len(confidences)
            
            # Calculate prediction range
            pred_values = list(predictions.values())
            price_range_low = min(pred_values) * 0.9
            price_range_high = max(pred_values) * 1.1
            
            # Calculate optimal bid (conservative approach)
            optimal_bid = ensemble_prediction * 0.85  # Bid 85% of predicted final price
            
            # Calculate win probability based on current price and prediction
            current_price = lot_data.get('current_price', 1.0)
            if ensemble_prediction > current_price:
                win_probability = min(0.9, ensemble_confidence * (ensemble_prediction / current_price - 1))
            else:
                win_probability = 0.1
            
            # Determine best model used
            best_model_key = max(confidences.keys(), key=lambda k: confidences[k])
            best_model_name = self.model_configs[best_model_key]['name']
            
            result = PredictionResult(
                lot_id=lot_data.get('lot_id', 0),
                predicted_final_price=round(ensemble_prediction, 2),
                confidence_score=round(ensemble_confidence * 100, 1),
                price_range_low=round(price_range_low, 2),
                price_range_high=round(price_range_high, 2),
                optimal_bid=round(optimal_bid, 2),
                win_probability=round(win_probability * 100, 1),
                model_used=f"Ensemble ({best_model_name} lead)",
                features_used=list(features_dict.keys()),
                prediction_timestamp=datetime.now().isoformat()
            )
            
            # Store prediction
            self.store_prediction(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {e}")
            
            # Fallback prediction
            current_price = lot_data.get('current_price', 1.0)
            return PredictionResult(
                lot_id=lot_data.get('lot_id', 0),
                predicted_final_price=current_price * 2.0,
                confidence_score=30.0,
                price_range_low=current_price * 1.5,
                price_range_high=current_price * 3.0,
                optimal_bid=current_price * 1.8,
                win_probability=50.0,
                model_used="Fallback",
                features_used=[],
                prediction_timestamp=datetime.now().isoformat()
            )
    
    def prepare_prediction_features(self, lot_data: Dict) -> Dict:
        """Prepare features for a single lot prediction"""
        
        # Extract and prepare features
        features = {
            'starting_price': lot_data.get('current_price', 1.0),
            'instant_win_price': lot_data.get('instant_win_price', 100.0),
            'bidder_count': lot_data.get('bidder_count', 1),
            'bid_count': lot_data.get('bid_count', 0),
            'auction_duration_hours': 24.0,  # Default
            'day_of_week': datetime.now().weekday(),
            'hour_of_day': datetime.now().hour,
            'month': datetime.now().month,
            'is_weekend': datetime.now().weekday() >= 5,
            'has_images': True,  # Assume true
            'description_length': 150,  # Default
            'seller_rating': 4.0,  # Default
            'shipping_cost': 15.0,  # Default
        }
        
        # Encode categorical features
        category = lot_data.get('category', 'Electronics')
        brand = lot_data.get('brand', 'Generic')
        condition = lot_data.get('condition', 'Good')
        location = lot_data.get('location', 'Rock Hill')
        
        # Use existing encoders or create defaults
        try:
            features['category_encoded'] = self.encoders.get('category', LabelEncoder()).transform([category])[0] if 'category' in self.encoders else 0
        except:
            features['category_encoded'] = 0
            
        try:
            features['brand_encoded'] = self.encoders.get('brand', LabelEncoder()).transform([brand])[0] if 'brand' in self.encoders else 0
        except:
            features['brand_encoded'] = 0
            
        try:
            features['condition_encoded'] = self.encoders.get('condition', LabelEncoder()).transform([condition])[0] if 'condition' in self.encoders else 0
        except:
            features['condition_encoded'] = 0
            
        try:
            features['location_encoded'] = self.encoders.get('location', LabelEncoder()).transform([location])[0] if 'location' in self.encoders else 0
        except:
            features['location_encoded'] = 0
        
        # Derived features
        features['price_per_bidder'] = features['starting_price'] / (features['bidder_count'] + 1)
        features['bids_per_bidder'] = features['bid_count'] / (features['bidder_count'] + 1)
        features['competition_intensity'] = features['bid_count'] / features['auction_duration_hours']
        features['starting_price_ratio'] = features['starting_price'] / features['instant_win_price']
        features['seller_rating_normalized'] = (features['seller_rating'] - 3.0) / 2.0
        features['description_length_log'] = np.log1p(features['description_length'])
        features['shipping_cost_ratio'] = features['shipping_cost'] / features['starting_price']
        features['is_prime_time'] = 1 if 18 <= features['hour_of_day'] <= 22 else 0
        features['is_holiday_season'] = 1 if features['month'] in [11, 12] else 0
        
        return features
    
    def create_feature_vector(self, features_dict: Dict) -> List[float]:
        """Create feature vector from features dictionary"""
        
        # Expected feature order (should match training)
        feature_order = [
            'starting_price', 'instant_win_price', 'bidder_count', 'bid_count',
            'auction_duration_hours', 'day_of_week', 'hour_of_day', 'month',
            'is_weekend', 'has_images', 'description_length', 'seller_rating',
            'shipping_cost', 'category_encoded', 'brand_encoded', 'condition_encoded',
            'location_encoded', 'price_per_bidder', 'bids_per_bidder',
            'competition_intensity', 'starting_price_ratio', 'seller_rating_normalized',
            'description_length_log', 'shipping_cost_ratio', 'is_prime_time',
            'is_holiday_season'
        ]
        
        vector = []
        for feature in feature_order:
            value = features_dict.get(feature, 0.0)
            if isinstance(value, bool):
                value = float(value)
            vector.append(value)
        
        return vector
    
    def store_prediction(self, result: PredictionResult):
        """Store prediction in database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO model_predictions 
            (lot_id, model_name, predicted_price, confidence_score, features_used, prediction_timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            result.lot_id, result.model_used, result.predicted_final_price,
            result.confidence_score, json.dumps(result.features_used), result.prediction_timestamp
        ))
        self.conn.commit()
    
    def save_models(self):
        """Save trained models to disk"""
        os.makedirs('ml_prediction/saved_models', exist_ok=True)
        
        # Save models
        for model_key, model in self.models.items():
            joblib.dump(model, f'ml_prediction/saved_models/{model_key}_model.pkl')
        
        # Save scalers and encoders
        joblib.dump(self.scalers, 'ml_prediction/saved_models/scalers.pkl')
        joblib.dump(self.encoders, 'ml_prediction/saved_models/encoders.pkl')
        joblib.dump(self.feature_selectors, 'ml_prediction/saved_models/feature_selectors.pkl')
        
        self.logger.info("💾 Models saved to disk")
    
    def load_models(self):
        """Load trained models from disk"""
        try:
            # Load models
            for model_key in self.model_configs.keys():
                model_path = f'ml_prediction/saved_models/{model_key}_model.pkl'
                if os.path.exists(model_path):
                    self.models[model_key] = joblib.load(model_path)
            
            # Load scalers and encoders
            if os.path.exists('ml_prediction/saved_models/scalers.pkl'):
                self.scalers = joblib.load('ml_prediction/saved_models/scalers.pkl')
            if os.path.exists('ml_prediction/saved_models/encoders.pkl'):
                self.encoders = joblib.load('ml_prediction/saved_models/encoders.pkl')
            if os.path.exists('ml_prediction/saved_models/feature_selectors.pkl'):
                self.feature_selectors = joblib.load('ml_prediction/saved_models/feature_selectors.pkl')
            
            self.logger.info(f"📂 Loaded {len(self.models)} models from disk")
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not load models: {e}")
            return False
    
    def get_model_performance_report(self) -> Dict:
        """Generate comprehensive model performance report"""
        
        # Get performance from database
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT model_name, mae, rmse, r2, accuracy_10_percent, accuracy_20_percent, 
                   training_samples, evaluation_date
            FROM model_performance 
            ORDER BY evaluation_date DESC
        ''')
        
        performance_data = cursor.fetchall()
        
        # Get feature importance
        cursor.execute('''
            SELECT model_name, feature_name, importance_score, rank
            FROM feature_importance 
            WHERE rank <= 10
            ORDER BY model_name, rank
        ''')
        
        feature_importance_data = cursor.fetchall()
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'models_trained': len(self.models),
            'performance_summary': {},
            'feature_importance': {},
            'best_model': None,
            'recommendations': []
        }
        
        # Process performance data
        best_r2 = -1
        for row in performance_data:
            model_name, mae, rmse, r2, acc_10, acc_20, samples, date = row
            
            report['performance_summary'][model_name] = {
                'mae': mae,
                'rmse': rmse,
                'r2': r2,
                'accuracy_within_10_percent': acc_10,
                'accuracy_within_20_percent': acc_20,
                'training_samples': samples,
                'last_trained': date
            }
            
            if r2 > best_r2:
                best_r2 = r2
                report['best_model'] = model_name
        
        # Process feature importance
        for row in feature_importance_data:
            model_name, feature_name, importance, rank = row
            
            if model_name not in report['feature_importance']:
                report['feature_importance'][model_name] = []
            
            report['feature_importance'][model_name].append({
                'feature': feature_name,
                'importance': importance,
                'rank': rank
            })
        
        # Generate recommendations
        if best_r2 > 0.7:
            report['recommendations'].append("Models show good predictive performance (R² > 0.7)")
        elif best_r2 > 0.5:
            report['recommendations'].append("Models show moderate performance - consider feature engineering")
        else:
            report['recommendations'].append("Models need improvement - collect more data or try different algorithms")
        
        return report
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'conn'):
            self.conn.close()
        self.logger.info("🧹 Enhanced ML models cleanup complete")

def main():
    """Test the enhanced ML models"""
    
    print("🤖 ENHANCED ML MODELS TEST")
    print("="*50)
    
    if not ML_AVAILABLE:
        print("❌ ML libraries not available. Please install: pip install scikit-learn pandas numpy")
        return
    
    # Initialize ML system
    ml_system = EnhancedMLModels()
    
    try:
        # Train models
        print("\n🤖 Training ML models...")
        performance = ml_system.train_models()
        
        print(f"\n📊 Model Performance:")
        for model_key, perf in performance.items():
            print(f"   {perf.model_name}:")
            print(f"     R²: {perf.r2:.3f}")
            print(f"     MAE: ${perf.mae:.2f}")
            print(f"     Accuracy (±10%): {perf.accuracy_within_10_percent:.1f}%")
        
        # Test prediction
        print(f"\n🎯 Testing Prediction:")
        test_lot = {
            'lot_id': 35863830,
            'current_price': 1.00,
            'instant_win_price': 1299.99,
            'bidder_count': 6,
            'bid_count': 0,
            'category': 'Electronics',
            'brand': 'ECOVACS',
            'condition': 'New'
        }
        
        prediction = ml_system.predict_auction_price(test_lot)
        
        print(f"   Lot ID: {prediction.lot_id}")
        print(f"   Predicted Final Price: ${prediction.predicted_final_price}")
        print(f"   Confidence: {prediction.confidence_score}%")
        print(f"   Optimal Bid: ${prediction.optimal_bid}")
        print(f"   Win Probability: {prediction.win_probability}%")
        print(f"   Model Used: {prediction.model_used}")
        
        # Generate performance report
        print(f"\n📋 Generating Performance Report:")
        report = ml_system.get_model_performance_report()
        print(f"   Best Model: {report['best_model']}")
        print(f"   Models Trained: {report['models_trained']}")
        
        if report['recommendations']:
            print(f"   Recommendations:")
            for rec in report['recommendations']:
                print(f"     - {rec}")
        
    finally:
        ml_system.cleanup()

if __name__ == "__main__":
    main() 