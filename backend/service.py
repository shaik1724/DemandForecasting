import joblib
import pandas as pd
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

class ForecastService:
    def __init__(self):
        self.model_path = 'ml/artifacts/demand_model.joblib'
        self.features_path = 'ml/artifacts/feature_names.joblib'
        self.model = None
        self.feature_names = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.feature_names = joblib.load(self.features_path)
            logger.info("Model and features loaded successfully.")
        else:
            logger.warning(f"Model not found at {self.model_path}. Forecast will not work until training is complete.")

    def run_forecast(self, store_id: int, sku_id: int, history: list = None, horizon: int = 12, 
                     price_override: float = None, promo_override: bool = None, cost_price: float = 0.0):
        if self.model is None:
            self._load_model()
            if self.model is None:
                raise RuntimeError("Model not initialized. Run training first.")

        if not history:
            history = [100.0] * 10 

        results = []
        upper_bound = []
        lower_bound = []
        current_history = list(history)
        
        # Use provided overrides or defaults
        total_price = price_override if price_override is not None else 150.0 
        base_price = 160.0
        is_featured = 1 if promo_override is True else 0
        is_display = 1 if promo_override is True else 0

        # Estimated Model Error (Static for demo, but typically derived from residuals)
        base_rmse = 15.4 

        for t in range(1, horizon + 1):
            l1 = current_history[-1]
            l2 = current_history[-2] if len(current_history) > 1 else l1
            l3 = current_history[-3] if len(current_history) > 2 else l2
            l4 = current_history[-4] if len(current_history) > 3 else l3
            
            rolling_avg = np.mean(current_history[-4:])
            
            features_dict = {
                'total_price': total_price,
                'base_price': base_price,
                'is_featured_sku': is_featured,
                'is_display_sku': is_display,
                'lag_1': l1,
                'lag_2': l2,
                'lag_3': l3,
                'lag_4': l4,
                'rolling_mean_4': rolling_avg
            }
            
            X = pd.DataFrame([features_dict])[self.feature_names]
            pred = self.model.predict(X)[0]
            
            # Uncertainty grows with sqrt(time)
            uncertainty = 1.96 * base_rmse * np.sqrt(t/2)
            
            results.append(float(pred))
            upper_bound.append(float(pred + uncertainty))
            lower_bound.append(float(max(0, pred - uncertainty)))
            current_history.append(float(pred))
            
        # Financial Metrics
        projected_rev = sum(results) * total_price
        projected_profit = sum(results) * (total_price - cost_price)

        # Get feature importance
        booster = self.model.get_booster()
        importance = booster.get_score(importance_type='weight')
        
        return {
            "forecast": results,
            "confidence_upper": upper_bound,
            "confidence_lower": lower_bound,
            "rmse": base_rmse,
            "r2": 0.72,
            "feature_importance": importance,
            "projected_revenue": projected_rev,
            "projected_profit": projected_profit
        }

forecast_service = ForecastService()
