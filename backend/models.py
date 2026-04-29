from pydantic import BaseModel
from typing import List, Optional

class ForecastRequest(BaseModel):
    store_id: int
    sku_id: int
    history: Optional[List[float]] = None 
    horizon: int = 12
    # Simulation Overrides
    price_override: Optional[float] = None
    promo_override: Optional[bool] = None
    # Financial Inputs
    cost_price: Optional[float] = 0.0

class ForecastResponse(BaseModel):
    forecast: List[float]
    confidence_upper: List[float]
    confidence_lower: List[float]
    rmse: float
    r2: float
    feature_importance: dict
    # Financial Metrics
    projected_revenue: float
    projected_profit: float
