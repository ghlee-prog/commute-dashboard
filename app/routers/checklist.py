from typing import Dict
from fastapi import APIRouter, HTTPException
from app.models import ChecklistItem, ChecklistResponse

router = APIRouter(prefix="/api/checklist", tags=["checklist"])

_CHECKLIST: Dict[str, ChecklistItem] = {
    "badge": ChecklistItem(
        id="badge",
        name="회사 사원증 / 출입카드",
        icon="id-card",
        checked=False,
        essential=True,
        tag="필수"
    ),
    "earbuds": ChecklistItem(
        id="earbuds",
        name="에어팟 / 무선 이어폰",
        icon="headphones",
        checked=False,
        essential=True,
        tag="출근 메이트"
    ),
    "wallet": ChecklistItem(
        id="wallet",
        name="지갑 / 신용카드 (교통카드)",
        icon="credit-card",
        checked=True,
        essential=True,
        tag="필수"
    ),
    "phone": ChecklistItem(
        id="phone",
        name="스마트폰 완충 확인",
        icon="smartphone",
        checked=True,
        essential=True,
        tag="배터리"
    ),
    "tumbler": ChecklistItem(
        id="tumbler",
        name="텀블러 / 보온병",
        icon="cup-soda",
        checked=False,
        essential=False,
        tag="선택"
    ),
    "keys": ChecklistItem(
        id="keys",
        name="현관 도어락 확인 & 열쇠",
        icon="key",
        checked=True,
        essential=False,
        tag="보안"
    )
}

def _get_response() -> ChecklistResponse:
    items = list(_CHECKLIST.values())
    checked = [i for i in items if i.checked]
    return ChecklistResponse(
        total_items=len(items),
        checked_items=len(checked),
        all_checked=len(checked) == len(items),
        items=items
    )

@router.get("", response_model=ChecklistResponse)
async def get_checklist():
    return _get_response()

@router.post("/toggle/{item_id}", response_model=ChecklistResponse)
async def toggle_checklist_item(item_id: str):
    if item_id not in _CHECKLIST:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    _CHECKLIST[item_id].checked = not _CHECKLIST[item_id].checked
    return _get_response()

@router.post("/reset", response_model=ChecklistResponse)
async def reset_checklist():
    for item in _CHECKLIST.values():
        item.checked = False
    return _get_response()
