from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
import pandas as pd
import os
import joblib

from src.data_model import SupplyChainInput

app = FastAPI(
    title="Global Supply Chain Disruption Mitigation API",
    description="API for predicting mitigation actions for supply chain disruptions",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(BASE_DIR, "model.pkl")
columns_path = os.path.join(BASE_DIR, "columns.pkl")

if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found at {model_path}")
if not os.path.exists(columns_path):
    raise FileNotFoundError(f"Columns file not found at {columns_path}")

with open(model_path, "rb") as f:
    model = pickle.load(f)

columns = joblib.load(columns_path)


def preprocess(sample: pd.DataFrame) -> pd.DataFrame:
    sample_encoded = pd.get_dummies(sample)
    sample_encoded = sample_encoded.reindex(columns=columns, fill_value=0)
    return sample_encoded


@app.get("/")
def index():
    return {"message": "Welcome to the Global Supply Chain Disruption Mitigation API"}


@app.post("/predict")
def model_predict(input_data: SupplyChainInput):
    sample = pd.DataFrame({
        "Origin_City": [input_data.origin_city.value],
        "Destination_City": [input_data.destination_city.value],
        "Route_Type": [input_data.route_type.value],
        "Transportation_Mode": [input_data.transportation_mode.value],
        "Product_Category": [input_data.product_category.value],
        "Delivery_Status": [input_data.delivery_status.value],
        "Disruption_Event": [
            input_data.disruption_event.value if input_data.disruption_event else "No Disruption"
        ],

        "Base_Lead_Time_Days": [input_data.base_lead_time_days],
        "Scheduled_Lead_Time_Days": [input_data.scheduled_lead_time_days],
        "Actual_Lead_Time_Days": [input_data.actual_lead_time_days],
        "Delay_Days": [input_data.delay_days],
        "Geopolitical_Risk_Index": [input_data.geopolitical_risk_index],
        "Weather_Severity_Index": [input_data.weather_severity_index],
        "Inflation_Rate_Pct": [input_data.inflation_rate_pct],
        "Shipping_Cost_USD": [input_data.shipping_cost_usd],
        "Order_Weight_Kg": [input_data.order_weight_kg],
    })

    sample = preprocess(sample)

    try:
        predicted_value = model.predict(sample)[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model prediction failed: {e}")

    return {"predicted_mitigation_action": predicted_value}
