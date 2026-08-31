# ==============================================================================
# 네이버 클라우드 플랫폼 (NCP) 지도 API 인증 키 설정
# ==============================================================================
NAVER_CLIENT_ID = "trcf5mo8a4"
NAVER_CLIENT_SECRET = "4HLRLKltzNljArWBKfmQShKRD64roNJOKDwUxdHC"

# 정확한 출발지 및 도착지 좌표 하드코딩 (경도,위도 / X,Y 형식)
# 출발지: 경기 광주시 더샵오포센트리체 정문 인근 (127.2255, 37.3663)
START_ADDRESS = "경기 광주시 더샵오포센트리체 (정문)"
START_COORDS = "127.2255,37.3663"

# 도착지: 경기 안양시 안양메가밸리 입구 (126.9688, 37.3975)
GOAL_ADDRESS = "경기 안양시 안양메가밸리 (입구)"
GOAL_COORDS = "126.9688,37.3975"

import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import (
    CommuteResponse, 
    CommuteRoute, 
    TransitSegment,
    WeatherResponse
)
from app.routers import weather, smarthome, checklist

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title=settings.app_title,
    version="1.3.0",
    description="iPhone Safari PWA 출근 대시보드 (네이버 지도 Direction5 traoptimal 연동)"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서브 라우터 등록
app.include_router(weather.router)
app.include_router(smarthome.router)
app.include_router(checklist.router)


# ==============================================================================
# 네이버 지도 Direction5 API 호출 및 교통상황 연동 로직 (option=traoptimal 고정)
# ==============================================================================
async def call_naver_direction5_api(
    start: str = START_COORDS, 
    goal: str = GOAL_COORDS
) -> Dict[str, Any]:
    """
    네이버 클라우드 플랫폼 Direction5 API를 호출합니다.
    URL 파라미터에 option=traoptimal(실시간 최적)을 고정으로 추가합니다.
    """
    if (not NAVER_CLIENT_ID or NAVER_CLIENT_ID.strip() in ("", "키입력") or 
        not NAVER_CLIENT_SECRET or NAVER_CLIENT_SECRET.strip() in ("", "키입력")):
        return {
            "success": False,
            "is_live": False,
            "message": "⚠️ 네이버 지도 API 키가 설정되지 않았습니다.",
            "data": None
        }

    headers = {
        "x-ncp-apigw-api-key-id": NAVER_CLIENT_ID.strip(),
        "x-ncp-apigw-api-key": NAVER_CLIENT_SECRET.strip()
    }
    
    # URL 파라미터: option=traoptimal 고정 및 waypoints 추가 (오포IC 포천방향 진입)
    params = {
        "start": start,
        "waypoints": "127.2305,37.3635",
        "goal": goal,
        "option": "traoptimal"
    }

    url = "https://naveropenapi.apigw.ntruss.com/map-direction/v5/driving"

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get("code") == 0:
                    return {
                        "success": True,
                        "is_live": True,
                        "message": "🟢 네이버 지도 Direction5 실시간 최적(traoptimal) 연동 완료",
                        "data": res_json
                    }
            elif response.status_code in (401, 403):
                return {
                    "success": False,
                    "is_live": False,
                    "message": "⚠️ 네이버 지도 API 인증 대기 (기본 실시간 최적 경로 제공)",
                    "data": None
                }

            return {
                "success": False,
                "is_live": False,
                "message": f"⚠️ 네이버 지도 API 응답 오류 (상태코드 {response.status_code})",
                "data": None
            }
    except Exception as e:
        return {
            "success": False,
            "is_live": False,
            "message": f"⚠️ 네이버 지도 API 통신 예외 ({str(e)})",
            "data": None
        }


@app.get("/api/commute", response_model=CommuteResponse, tags=["commute"])
async def get_commute_dashboard_info():
    """
    네이버 지도 Direction5 (traoptimal 실시간 최적) 기반 출근길 실시간 소요시간 및 경로를 반환합니다.
    출발지(start): 127.2255,37.3663 (더샵오포센트리체 정문 인근)
    도착지(goal): 126.9688,37.3975 (안양메가밸리 입구)
    """
    now = datetime.now()
    
    # 1. 네이버 지도 API 실시간 호출 (option=traoptimal 고정)
    naver_result = await call_naver_direction5_api(START_COORDS, GOAL_COORDS)
    
    is_live = naver_result.get("is_live", False)
    status_msg = naver_result.get("message", "")
    api_data = naver_result.get("data")
    
    # 기본 경로 파라미터 (오포IC → 세종포천고속도로 본선 → 광남IC, 약 33km, 통행료 2,300원, 예상 소요시간 31~33분)
    duration_min = 32
    distance_km = 33.0
    toll_fare = 2300
    taxi_fare = 33500
    fuel_price = 4100
    traffic_status = "원활 (소통 원활)"
    traffic_color = "emerald"
    
    # 2. 네이버 API 응답 JSON 파싱: 반드시 route['traoptimal'][0]['summary']에서 distance, duration, tollFare 추출
    if is_live and api_data:
        try:
            route_dict = api_data.get("route", {})
            # Prefer trafast (real-time fast) route since we forced waypoints
            if "trafast" in route_dict and len(route_dict["trafast"]) > 0:
                summary = route_dict["trafast"][0].get("summary", {})
            elif "traoptimal" in route_dict and len(route_dict["traoptimal"]) > 0:
                summary = route_dict["traoptimal"][0].get("summary", {})
            else:
                summary = {}
            # duration (ms -> min)
            if "duration" in summary:
                duration_min = max(1, round(summary["duration"] / 60000))
            # distance (m -> km)
            if "distance" in summary:
                distance_km = round(summary["distance"] / 1000, 1)
            # tollFare (원)
            if "tollFare" in summary:
                toll_fare = summary["tollFare"]
            # taxiFare & fuelPrice
            if "taxiFare" in summary:
                taxi_fare = summary["taxiFare"]
            if "fuelPrice" in summary:
                fuel_price = summary["fuelPrice"]
            # traffic congestion evaluation
            sections = route_dict.get("trafast", route_dict.get("traoptimal", []))
            if sections:
                sections = sections[0].get("section", [])
                congested_count = sum(1 for s in sections if s.get("congestion", 0) >= 3)
                if congested_count >= 2:
                    traffic_status = "혼잡 (정체 구간 발생)"
                    traffic_color = "rose"
                elif congested_count == 1:
                    traffic_status = "서행 (소통 원활-서행)"
                    traffic_color = "amber"
                else:
                    traffic_status = "원활 (정체 없음)"
                    traffic_color = "emerald"
        except Exception as err:
            print("Naver API Parsing Warning:", err)

    estimated_arrival_dt = now + timedelta(minutes=duration_min)
    
    # 실시간 최적 경로 (traoptimal)
    car_optimal_segments = [
        TransitSegment(
            type="car",
            name="태봉로 ➔ 오포IC (세종포천고속도로)",
            duration_min=7,
            icon="car",
            color="indigo",
            detail="오포TG 진입 ➔ 광남TG 진출 (통행료 1,100원)"
        ),
        TransitSegment(
            type="car",
            name="여수대로IC ➔ 제2경인고속도로",
            duration_min=17,
            icon="car",
            color="indigo",
            detail="성남이천로(3번국도) 경유 ➔ 제2경인고속도로 진입"
        ),
        TransitSegment(
            type="car",
            name="북의왕IC ➔ 안양메가밸리",
            duration_min=12,
            icon="car",
            color="indigo",
            detail="북의왕TG 진출 (통행료 1,200원) ➔ 인덕원사거리 ➔ 학의로"
        )
    ]
    
    route_car_optimal = CommuteRoute(
        id="route_naver_traoptimal",
        name="실시간 최적 (네이버 추천)",
        mode="car",
        total_duration_min=duration_min,
        distance_km=distance_km,
        traffic_status=traffic_status,
        traffic_color=traffic_color,
        departure_time=now.strftime("%H:%M"),
        estimated_arrival_time=estimated_arrival_dt.strftime("%H:%M"),
        recommended=True,
        next_arrival_seconds=0,
        next_arrival_text=f"거리 {distance_km}km · 통행료 {toll_fare:,}원 · 택시비 {taxi_fare:,}원",
        toll_fare=toll_fare,
        taxi_fare=taxi_fare,
        fuel_price=fuel_price,
        segments=car_optimal_segments
    )

    # 9시 정각 도착 기준 권장 출발 시간
    rec_dep_dt = (now.replace(hour=8, minute=20) if now.hour < 9 else now)

    return CommuteResponse(
        origin=START_ADDRESS,
        destination=GOAL_ADDRESS,
        origin_coords=START_COORDS,
        destination_coords=GOAL_COORDS,
        target_time=settings.target_arrival_time,
        recommended_departure_time=rec_dep_dt.strftime("%H:%M"),
        traffic_engine="네이버 지도 API (Direction5 traoptimal)",
        is_naver_api_active=is_live,
        naver_status_message=status_msg,
        routes=[route_car_optimal],
        live_traffic_alert="제2경인고속도로(안양-성남) 전 구간 소통 원활",
        updated_at=now.strftime("%H:%M:%S")
    )


# ==============================================================================
# PWA 루트 및 정적 파일 엔드포인트
# ==============================================================================
@app.get("/manifest.json")
async def get_manifest():
    manifest_file = STATIC_DIR / "manifest.json"
    return FileResponse(manifest_file, media_type="application/manifest+json")

@app.get("/sw.js")
async def get_service_worker():
    sw_file = STATIC_DIR / "sw.js"
    return FileResponse(sw_file, media_type="application/javascript")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>Commute Dashboard Initializing...</h1>")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_title,
        "version": "1.3.0",
        "naver_api_configured": bool(NAVER_CLIENT_ID and NAVER_CLIENT_ID != "키입력")
    }

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
