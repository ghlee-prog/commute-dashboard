from typing import List, Optional
from pydantic import BaseModel, Field

# --- Weather Models ---
class HourlyForecast(BaseModel):
    time: str
    temp: int
    icon: str
    condition: str
    rain_pop: int

class AirQuality(BaseModel):
    pm10: int
    pm10_status: str
    pm25: int
    pm25_status: str
    grade: str  # 좋음, 보통, 나쁨

class WeatherResponse(BaseModel):
    location: str
    current_temp: int
    feels_like: int
    min_temp: int
    max_temp: int
    condition: str
    condition_detail: str
    icon: str
    rain_probability: int
    humidity: int
    wind_speed: float
    uv_index: str
    air_quality: AirQuality
    umbrella_needed: bool
    outfit_tip: str
    hourly_forecast: List[HourlyForecast]
    updated_at: str

# --- Commute Models ---
class TransitSegment(BaseModel):
    type: str  # walk, subway, bus, car
    name: str  # e.g., "성남이천로", "제2경인고속도로"
    duration_min: int
    icon: str
    color: str
    detail: Optional[str] = None

class CommuteRoute(BaseModel):
    id: str
    name: str
    mode: str  # car, subway, bus
    total_duration_min: int
    distance_km: float
    traffic_status: str  # 원활, 서행, 정체
    traffic_color: str
    departure_time: str
    estimated_arrival_time: str
    recommended: bool
    next_arrival_seconds: int
    next_arrival_text: str
    toll_fare: int = 0
    taxi_fare: int = 0
    fuel_price: int = 0
    segments: List[TransitSegment]

class CommuteResponse(BaseModel):
    origin: str
    destination: str
    origin_coords: str
    destination_coords: str
    target_time: str
    recommended_departure_time: str
    traffic_engine: str = "네이버 지도 API (Direction5)"
    is_naver_api_active: bool = False
    naver_status_message: str = ""
    routes: List[CommuteRoute]
    live_traffic_alert: Optional[str] = None
    updated_at: str

# --- Smart Home Models ---
class SmartDevice(BaseModel):
    id: str
    name: str
    room: str
    type: str  # light, plug, switch
    is_on: bool
    power_watts: int
    icon: str

class SmartHomeStatusResponse(BaseModel):
    total_devices: int
    active_count: int
    all_off: bool
    total_active_power_watts: int
    estimated_daily_savings_won: int
    devices: List[SmartDevice]
    last_action: Optional[str] = None
    updated_at: str

class ToggleAllRequest(BaseModel):
    turn_on: bool = False

class ToggleDeviceRequest(BaseModel):
    is_on: Optional[bool] = None

# --- Checklist Models ---
class ChecklistItem(BaseModel):
    id: str
    name: str
    icon: str
    checked: bool
    essential: bool
    tag: str

class ChecklistResponse(BaseModel):
    total_items: int
    checked_items: int
    all_checked: bool
    items: List[ChecklistItem]
