from datetime import datetime, timedelta
from fastapi import APIRouter
from app.models import CommuteResponse, CommuteRoute, TransitSegment
from app.config import settings

router = APIRouter(prefix="/api/commute", tags=["commute"])

@router.get("", response_model=CommuteResponse)
async def get_commute_info():
    now = datetime.now()
    
    # 1. 지하철 추천 경로 (2호선)
    subway_duration = 34
    subway_arrival_dt = now + timedelta(minutes=subway_duration)
    subway_segments = [
        TransitSegment(
            type="walk",
            name="도보 이동",
            duration_min=5,
            icon="footprints",
            color="emerald",
            detail="교대역 6번 출구로 이동 (320m)"
        ),
        TransitSegment(
            type="subway",
            name="지하철 2호선 (외선순환)",
            duration_min=22,
            icon="train",
            color="green",
            detail="교대역 탑승 ➔ 강남역 ➔ 역삼역 하차 (4개역 이동)"
        ),
        TransitSegment(
            type="walk",
            name="도보 이동",
            duration_min=7,
            icon="footprints",
            color="emerald",
            detail="역삼역 3번 출구 ➔ 테헤란로 IT 타워 (450m)"
        )
    ]
    
    subway_route = CommuteRoute(
        id="route_subway",
        name="지하철 2호선 최적",
        mode="subway",
        total_duration_min=subway_duration,
        traffic_status="원활",
        traffic_color="emerald",
        departure_time=now.strftime("%H:%M"),
        estimated_arrival_time=subway_arrival_dt.strftime("%H:%M"),
        recommended=True,
        next_arrival_seconds=180,  # 3분 남음
        next_arrival_text="3분 후 교대역 도착 예정 (잠실행)",
        segments=subway_segments
    )
    
    # 2. 버스 경로
    bus_duration = 43
    bus_arrival_dt = now + timedelta(minutes=bus_duration)
    bus_segments = [
        TransitSegment(
            type="walk",
            name="도보 이동",
            duration_min=6,
            icon="footprints",
            color="emerald",
            detail="서초유스센터 정류장으로 이동"
        ),
        TransitSegment(
            type="bus",
            name="간선 740번 버스",
            duration_min=30,
            icon="bus",
            color="blue",
            detail="8개 정류장 이동 ➔ 역삼역.포스코P&S타워 하차"
        ),
        TransitSegment(
            type="walk",
            name="도보 이동",
            duration_min=7,
            icon="footprints",
            color="emerald",
            detail="도보 400m 이동"
        )
    ]
    
    bus_route = CommuteRoute(
        id="route_bus",
        name="간선 740번 버스",
        mode="bus",
        total_duration_min=bus_duration,
        traffic_status="보통 (정체 구간 일부)",
        traffic_color="amber",
        departure_time=now.strftime("%H:%M"),
        estimated_arrival_time=bus_arrival_dt.strftime("%H:%M"),
        recommended=False,
        next_arrival_seconds=360,
        next_arrival_text="6분 후 정류장 도착 (빈자리 12석)",
        segments=bus_segments
    )
    
    # 3. 자가용 / 택시
    car_duration = 29
    car_arrival_dt = now + timedelta(minutes=car_duration)
    car_route = CommuteRoute(
        id="route_car",
        name="자가용 / 택시 (테헤란로)",
        mode="car",
        total_duration_min=car_duration,
        traffic_status="서초대로 구간 정체 서행",
        traffic_color="amber",
        departure_time=now.strftime("%H:%M"),
        estimated_arrival_time=car_arrival_dt.strftime("%H:%M"),
        recommended=False,
        next_arrival_seconds=0,
        next_arrival_text="테헤란로 진입로 평균 속도 22km/h",
        segments=[
            TransitSegment(
                type="car",
                name="서초대로 ➔ 테헤란로",
                duration_min=29,
                icon="car",
                color="indigo",
                detail="총 거리 5.8km | 예상 통행료 0원"
            )
        ]
    )

    # 9시 정각 출근 기준 추천 출발 시간
    rec_departure = (now.replace(hour=8, minute=20) if now.hour < 9 else now).strftime("%H:%M")

    return CommuteResponse(
        origin=settings.commute_origin,
        destination=settings.commute_destination,
        target_time=settings.target_arrival_time,
        recommended_departure_time=rec_departure,
        routes=[subway_route, bus_route, car_route],
        live_traffic_alert="2호선 전 구간 정시 운행 중 (지연 없음)",
        updated_at=now.strftime("%H:%M:%S")
    )
