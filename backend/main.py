from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.models import ForecastRequest, ForecastResponse
from backend.service import forecast_service
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Product Demand Forecasting API", version="1.0.0")

# Serve frontend static files
frontend_path = os.path.join(os.getcwd(), "frontend")
app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": forecast_service.model is not None}

@app.post("/forecast", response_model=ForecastResponse)
async def predict_demand(request: ForecastRequest):
    try:
        logger.info(f"Received forecast request for SKU {request.sku_id} at Store {request.store_id}")
        
        result_dict = forecast_service.run_forecast(
            store_id=request.store_id,
            sku_id=request.sku_id,
            history=request.history,
            horizon=request.horizon,
            price_override=request.price_override,
            promo_override=request.promo_override,
            cost_price=request.cost_price
        )
        
        return ForecastResponse(**result_dict)
        
    except Exception as e:
        logger.error(f"Error during forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
