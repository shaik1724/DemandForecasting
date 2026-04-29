import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

def preprocess_data(df):
    """Basic preprocessing as seen in the notebook."""
    # Convert types
    df['total_price'] = pd.to_numeric(df['total_price'], errors='coerce')
    df['base_price'] = pd.to_numeric(df['base_price'], errors='coerce')
    df['units_sold'] = pd.to_numeric(df['units_sold'], errors='coerce')
    
    # Fill missing values
    df['total_price'] = df['total_price'].fillna(df['total_price'].mean())
    
    # Create unique key for grouping (optional but kept for alignment)
    df['key'] = df['week'].astype(str) + '_' + df['store_id'].astype(str)
    
    return df

def feature_engineering(df):
    """Create lag features and other predictors."""
    # Group by store and SKU to create meaningful lags
    df = df.sort_values(by=['store_id', 'sku_id', 'week'])
    
    # Creating 4 weeks of lags as per the 'day_1-4' logic in notebook
    for i in range(1, 5):
        df[f'lag_{i}'] = df.groupby(['store_id', 'sku_id'])['units_sold'].shift(i)
    
    # Rolling averages
    df['rolling_mean_4'] = df.groupby(['store_id', 'sku_id'])['units_sold'].transform(lambda x: x.shift(1).rolling(window=4).mean())
    
    # Drop rows with NaN lags
    df = df.dropna()
    
    # Selecting features
    features = ['total_price', 'base_price', 'is_featured_sku', 'is_display_sku', 
                'lag_1', 'lag_2', 'lag_3', 'lag_4', 'rolling_mean_4']
    target = 'units_sold'
    
    return df[features], df[target], features

def train():
    data_path = 'data/data.csv'
    if not os.path.exists(data_path):
        print(f"Data file not found at {data_path}")
        return

    print("Loading data...")
    df = pd.read_csv(data_path)
    
    print("Preprocessing...")
    df = preprocess_data(df)
    
    print("Feature Engineering...")
    X, y, feature_names = feature_engineering(df)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training XGBoost Model with {len(X_train)} samples...")
    model = xgb.XGBRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluation
    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    
    print(f"Model trained. RMSE: {rmse:.4f}, R2: {r2:.4f}")
    
    # Save artifacts
    os.makedirs('ml/artifacts', exist_ok=True)
    model_path = 'ml/artifacts/demand_model.joblib'
    joblib.dump(model, model_path)
    
    # Save feature names to ensure inference uses correct order
    joblib.dump(feature_names, 'ml/artifacts/feature_names.joblib')
    
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train()
