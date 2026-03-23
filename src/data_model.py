from pydantic import BaseModel
from pyparsing import Optional
from enum import Enum

class RouteType(str, Enum):
    atlantic = "Atlantic"
    commodity = "Commodity"
    intra_asia = "Intra-Asia"
    pacific = "Pacific"
    suez = "Suez"


class TransportationMode(str, Enum):
    air = "Air"
    sea = "Sea"


class ProductCategory(str, Enum):
    auto_parts = "Auto Parts"
    consumer_electronics = "Consumer Electronics"
    perishable_foods = "Perishable Foods"
    pharmaceuticals = "Pharmaceuticals"
    raw_materials = "Raw Materials"
    semiconductors = "Semiconductors"
    textiles = "Textiles"


class DeliveryStatus(str, Enum):
    on_time = "On Time"
    late = "Late"


class OriginCity(str, Enum):
    mumbai_in = "Mumbai, IN"
    shenzhen_cn = "Shenzhen, CN"
    shanghai_cn = "Shanghai, CN"
    tokyo_jp = "Tokyo, JP"
    hamburg_de = "Hamburg, DE"
    santos_br = "Santos, BR"

class DestinationCity(str, Enum):
    los_angeles_us = "Los Angeles, US"
    new_york_us = "New York, US"
    rotterdam_nl = "Rotterdam, NL"
    singapore_sg = "Singapore, SG"
    felixstowe_uk = "Felixstowe, UK"
    shanghai_cn = "Shanghai, CN"

class DisruptionEvent(str, Enum):
    no_disruption = "No Disruption"
    severe_weather_typhoon = "Severe Weather (Typhoon/Storm)"
    geopolitical_conflict_diversion = "Geopolitical Conflict (Route Diversion)"
    port_congestion = "Port Congestion"

class DeliveryStatus(str, Enum):
    on_time = "On Time"
    late = "Late"


class DisruptionEvent(str, Enum):
    no_disruption = "No Disruption"
    port_congestion = "Port Congestion"
    severe_weather = "Severe Weather"
    geopolitical_conflict = "Geopolitical Conflict"



class SupplyChainInput(BaseModel):
    origin_city: OriginCity
    destination_city: DestinationCity

    route_type: RouteType
    transportation_mode: TransportationMode
    product_category: ProductCategory
    delivery_status: DeliveryStatus
    disruption_event: DisruptionEvent

    base_lead_time_days: int
    scheduled_lead_time_days: int
    actual_lead_time_days: int
    delay_days: int

    geopolitical_risk_index: float
    weather_severity_index: float
    inflation_rate_pct: float
    shipping_cost_usd: float
    order_weight_kg: int