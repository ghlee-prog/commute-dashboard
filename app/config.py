import os
from pydantic import BaseModel

class AppSettings(BaseModel):
    app_title: str = "출근 대시보드"
    app_version: str = "1.3.0"
    
    # 기본 위치 및 출근 경로 설정 (더샵오포센트리체 -> 안양메가밸리)
    default_location_name: str = "경기도 광주시"
    commute_origin: str = "경기 광주시 더샵오포센트리체 (정문)"
    commute_origin_coords: str = "127.2255,37.3663"
    commute_destination: str = "경기 안양시 안양메가밸리 (입구)"
    commute_destination_coords: str = "126.9688,37.3975"
    target_arrival_time: str = "09:00"

settings = AppSettings()
