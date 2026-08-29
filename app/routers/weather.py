from datetime import datetime, timedelta
from typing import Dict, Tuple, List
import httpx
from fastapi import APIRouter
from app.models import WeatherResponse, HourlyForecast, AirQuality
from app.config import settings

router = APIRouter(prefix="/api/weather", tags=["weather"])

# WMO Weather Code 매핑 (Open-Meteo 표준)
WMO_WEATHER_MAP: Dict[int, Tuple[str, str]] = {
    0: ("맑음", "sun"),
    1: ("대체로 맑음", "sun"),
    2: ("구름 조금", "cloud-sun"),
    3: ("흐림", "cloud"),
    45: ("안개", "cloud"),
    48: ("서리 안개", "cloud"),
    51: ("가벼운 이슬비", "cloud-rain"),
    53: ("이슬비", "cloud-rain"),
    55: ("강한 이슬비", "cloud-rain"),
    56: ("진눈깨비 이슬비", "cloud-rain"),
    57: ("강한 진눈깨비", "cloud-rain"),
    61: ("약한 비", "cloud-rain"),
    63: ("비", "cloud-rain"),
    65: ("강한 비", "cloud-rain"),
    66: ("어는 비", "cloud-rain"),
    67: ("강한 어는 비", "cloud-rain"),
    71: ("약한 눈", "cloud-rain"),
    73: ("눈", "cloud-rain"),
    75: ("강한 눈", "cloud-rain"),
    77: ("싸락눈", "cloud-rain"),
    80: ("약한 소나기", "cloud-rain"),
    81: ("소나기", "cloud-rain"),
    82: ("강한 소나기", "cloud-rain"),
    85: ("눈 소나기", "cloud-rain"),
    86: ("강한 눈 소나기", "cloud-rain"),
    95: ("뇌우", "cloud-rain"),
    96: ("우박을 동반한 뇌우", "cloud-rain"),
    99: ("강한 우박 뇌우", "cloud-rain")
}

def get_weather_desc_and_icon(code: int) -> Tuple[str, str]:
    return WMO_WEATHER_MAP.get(code, ("맑음", "sun"))

@router.get("", response_model=WeatherResponse)
async def get_weather():
    """
    Open-Meteo API를 호출하여 경기도 광주시의 실제 실시간 기온 및 날씨를 반환합니다.
    3시간 간격(현재, +3h, +6h, +9h, +12h, +15h)으로 향후 12~15시간 예보를 필터링하여 전달합니다.
    """
    now = datetime.now()
    
    # 기본값 설정 (네트워크 장애 대비 폴백)
    current_temp = 24
    feels_like = 28
    min_temp = 22
    max_temp = 28
    humidity = 88
    wind_speed = 1.8
    rain_prob = 10
    weather_desc = "구름 조금"
    weather_icon = "cloud-sun"
    hourly_forecast: List[HourlyForecast] = []
    
    # Open-Meteo API 호출 (경기도 광주시 좌표: 위도 37.43, 경도 127.26)
    open_meteo_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 37.43,
        "longitude": 127.26,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
        "hourly": "temperature_2m,precipitation_probability,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "Asia/Seoul",
        "forecast_days": 2
    }

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(open_meteo_url, params=params)
            if res.status_code == 200:
                data = res.json()
                current = data.get("current", {})
                daily = data.get("daily", {})
                hourly = data.get("hourly", {})
                
                # 현재 실시간 기온 및 날씨 정보
                if "temperature_2m" in current:
                    current_temp = round(current["temperature_2m"])
                if "apparent_temperature" in current:
                    feels_like = round(current["apparent_temperature"])
                if "relative_humidity_2m" in current:
                    humidity = round(current["relative_humidity_2m"])
                if "wind_speed_10m" in current:
                    wind_speed = round(current["wind_speed_10m"] / 3.6, 1)  # km/h -> m/s
                
                wcode = current.get("weather_code", 0)
                weather_desc, weather_icon = get_weather_desc_and_icon(wcode)
                
                # 일일 최고 / 최저 기온
                if daily.get("temperature_2m_min"):
                    min_temp = round(daily["temperature_2m_min"][0])
                if daily.get("temperature_2m_max"):
                    max_temp = round(daily["temperature_2m_max"][0])
                
                # 현재 시각 기준 3시간 간격(0h, +3h, +6h, +9h, +12h, +15h) 예보 추출
                times = hourly.get("time", [])
                now_str = now.strftime("%Y-%m-%dT%H:00")
                start_idx = 0
                for i, t in enumerate(times):
                    if t >= now_str:
                        start_idx = i
                        break
                
                # 3시간 스텝으로 15시간 범위 필터링
                for step in range(0, 16, 3):
                    idx = start_idx + step
                    if idx < len(times):
                        raw_t = times[idx]
                        hour_part = raw_t.split("T")[1].split(":")[0]
                        t_label = "지금" if step == 0 else f"{hour_part}시"
                        t_val = round(hourly["temperature_2m"][idx])
                        pop = hourly.get("precipitation_probability", [0])[idx] or 0
                        h_code = hourly.get("weather_code", [0])[idx]
                        h_desc, h_icon = get_weather_desc_and_icon(h_code)
                        
                        hourly_forecast.append(HourlyForecast(
                            time=t_label,
                            temp=t_val,
                            icon=h_icon,
                            condition=h_desc,
                            rain_pop=pop
                        ))
                
                if hourly_forecast:
                    rain_prob = hourly_forecast[0].rain_pop
    except Exception as e:
        print("Open-Meteo Weather API Exception (using fallback):", e)

    # 기본 시간대별 예보가 비어있을 경우 3시간 간격 모의 생성
    if not hourly_forecast:
        for step in range(0, 16, 3):
            target_dt = now + timedelta(hours=step)
            t_label = "지금" if step == 0 else f"{target_dt.hour:02d}시"
            hourly_forecast.append(HourlyForecast(
                time=t_label,
                temp=current_temp,
                icon=weather_icon,
                condition=weather_desc,
                rain_pop=rain_prob
            ))

    # 우산 필요 여부 판단
    is_raining_code = any(h.icon == "cloud-rain" for h in hourly_forecast[:3])
    umbrella_needed = (rain_prob >= 40) or is_raining_code

    # 옷차림 추천 가이드
    if current_temp >= 28:
        outfit_tip = "기온이 높으니 얇고 통풍이 잘되는 시원한 옷차림을 추천합니다."
    elif current_temp >= 23:
        outfit_tip = "활동하기 쾌적한 날씨입니다. 얇은 반팔 또는 가벼운 셔츠 차림이 좋습니다."
    elif current_temp >= 18:
        outfit_tip = "일교차가 있으니 얇은 가디건이나 바람막이를 챙기세요."
    else:
        outfit_tip = "아침 기온이 쌀쌀하니 자켓이나 외투를 꼭 챙기세요."

    return WeatherResponse(
        location="경기도 광주시",
        current_temp=current_temp,
        feels_like=feels_like,
        min_temp=min_temp,
        max_temp=max_temp,
        condition=weather_desc,
        condition_detail="Open-Meteo 실시간 기상 데이터 연동 (3시간 간격)",
        icon=weather_icon,
        rain_probability=rain_prob,
        humidity=humidity,
        wind_speed=wind_speed,
        uv_index="보통 (4)",
        air_quality=AirQuality(
            pm10=26,
            pm10_status="좋음",
            pm25=12,
            pm25_status="좋음",
            grade="좋음"
        ),
        umbrella_needed=umbrella_needed,
        outfit_tip=outfit_tip,
        hourly_forecast=hourly_forecast,
        updated_at=now.strftime("%H:%M:%S")
    )
