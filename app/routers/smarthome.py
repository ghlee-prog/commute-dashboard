from datetime import datetime
from typing import Dict
from fastapi import APIRouter, HTTPException
from app.models import SmartDevice, SmartHomeStatusResponse, ToggleAllRequest, ToggleDeviceRequest

router = APIRouter(prefix="/api/smarthome", tags=["smarthome"])

# 인메모리 스마트홈 디바이스 상태 저장소
_SMART_DEVICES: Dict[str, SmartDevice] = {
    "light_living_main": SmartDevice(
        id="light_living_main",
        name="거실 메인등",
        room="거실",
        type="light",
        is_on=True,
        power_watts=45,
        icon="lamp-ceiling"
    ),
    "light_living_mood": SmartDevice(
        id="light_living_mood",
        name="거실 무드등",
        room="거실",
        type="light",
        is_on=True,
        power_watts=15,
        icon="lamp"
    ),
    "light_bedroom": SmartDevice(
        id="light_bedroom",
        name="침실 조명",
        room="침실",
        type="light",
        is_on=True,
        power_watts=30,
        icon="bed-double"
    ),
    "light_kitchen": SmartDevice(
        id="light_kitchen",
        name="주방 다운라이트",
        room="주방",
        type="light",
        is_on=True,
        power_watts=25,
        icon="utensils"
    ),
    "light_study": SmartDevice(
        id="light_study",
        name="서재 조명",
        room="서재",
        type="light",
        is_on=False,
        power_watts=20,
        icon="briefcase"
    ),
    "plug_standby": SmartDevice(
        id="plug_standby",
        name="대기전력 차단 플러그",
        room="거실",
        type="plug",
        is_on=True,
        power_watts=18,
        icon="plug-zap"
    )
}

_last_action = "대시보드 초기화 완료"

def _calculate_status() -> SmartHomeStatusResponse:
    devices_list = list(_SMART_DEVICES.values())
    active_devices = [d for d in devices_list if d.is_on]
    active_count = len(active_devices)
    total_power = sum(d.power_watts for d in active_devices)
    all_off = (active_count == 0)
    
    # 8시간 외출 기준 예상 절감 전력 금액 (kWh당 약 120원 가정)
    saved_power_watts = sum(d.power_watts for d in devices_list if not d.is_on)
    estimated_savings = int((saved_power_watts * 8 / 1000) * 120 * 30)  # 월 환산 예상

    return SmartHomeStatusResponse(
        total_devices=len(devices_list),
        active_count=active_count,
        all_off=all_off,
        total_active_power_watts=total_power,
        estimated_daily_savings_won=estimated_savings,
        devices=devices_list,
        last_action=_last_action,
        updated_at=datetime.now().strftime("%H:%M:%S")
    )

@router.get("/status", response_model=SmartHomeStatusResponse)
async def get_smarthome_status():
    return _calculate_status()

@router.post("/toggle-all", response_model=SmartHomeStatusResponse)
async def toggle_all_devices(payload: ToggleAllRequest = ToggleAllRequest(turn_on=False)):
    global _last_action
    target_state = payload.turn_on
    for device in _SMART_DEVICES.values():
        device.is_on = target_state
    
    if not target_state:
        _last_action = f"출근 모드: 전체 {len(_SMART_DEVICES)}개 기기 일괄 소등 완료 💡❌"
    else:
        _last_action = f"전체 {len(_SMART_DEVICES)}개 기기 켜짐 💡✨"
    
    return _calculate_status()

@router.post("/device/{device_id}/toggle", response_model=SmartHomeStatusResponse)
async def toggle_single_device(device_id: str, payload: ToggleDeviceRequest = None):
    global _last_action
    if device_id not in _SMART_DEVICES:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    device = _SMART_DEVICES[device_id]
    if payload and payload.is_on is not None:
        device.is_on = payload.is_on
    else:
        device.is_on = not device.is_on
        
    state_str = "켜짐" if device.is_on else "꺼짐"
    _last_action = f"'{device.name}' {state_str}"
    
    return _calculate_status()

@router.post("/reset", response_model=SmartHomeStatusResponse)
async def reset_devices():
    global _last_action
    _SMART_DEVICES["light_living_main"].is_on = True
    _SMART_DEVICES["light_living_mood"].is_on = True
    _SMART_DEVICES["light_bedroom"].is_on = True
    _SMART_DEVICES["light_kitchen"].is_on = True
    _SMART_DEVICES["light_study"].is_on = False
    _SMART_DEVICES["plug_standby"].is_on = True
    _last_action = "디바이스 상태 초기화됨 (아침 출근 전 상태)"
    return _calculate_status()
