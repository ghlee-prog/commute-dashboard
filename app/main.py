import os
import logging
from pathlib import Path
import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.routers import weather, smarthome, checklist

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Commute Dashboard",
    version="1.4.0",
    description="iPhone Safari PWA 출근 대시보드"
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

# 정적 파일 마운트
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/manifest.json")
async def get_manifest():
    manifest_file = STATIC_DIR / "manifest.json"
    if manifest_file.exists():
        return FileResponse(manifest_file, media_type="application/manifest+json")
    return {"error": "manifest not found"}

@app.get("/sw.js")
async def get_service_worker():
    sw_file = STATIC_DIR / "sw.js"
    if sw_file.exists():
        return FileResponse(sw_file, media_type="application/javascript")
    return {"error": "sw not found"}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>Commute Dashboard Initializing...</h1>")

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "app": "Commute Dashboard",
        "version": "1.4.0"
    }

# ==============================================================================
# SmartThings 엘리베이터 호출 API
# ==============================================================================
@app.post("/api/elevator")
async def call_elevator():
    st_token = os.getenv("ST_TOKEN", "").strip()
    if not st_token:
        logging.warning("ST_TOKEN 환경변수가 설정되지 않았습니다.")
        return {"success": False, "message": "ST_TOKEN 환경 변수가 설정되지 않았습니다."}

    headers = {
        "Authorization": f"Bearer {st_token}",
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. 장면 목록 조회
            res = await client.get("https://api.smartthings.com/v1/scenes", headers=headers)
            if res.status_code != 200:
                logging.error(f"SmartThings scenes fetch error: {res.status_code} {res.text}")
                return {"success": False, "message": f"장면 목록 조회 실패 (상태 코드: {res.status_code})"}

            data = res.json()
            items = data.get("items", [])

            # 2. sceneName에 "엘리베이터"가 포함된 장면 찾기
            target_scene = None
            for item in items:
                scene_name = item.get("sceneName", "")
                if "엘리베이터" in scene_name:
                    target_scene = item
                    break

            if not target_scene:
                logging.warning("장면 목록 중 '엘리베이터'가 포함된 장면을 찾지 못했습니다.")
                return {"success": False, "message": "'엘리베이터' 장면을 찾을 수 없습니다."}

            scene_id = target_scene.get("sceneId")
            if not scene_id:
                return {"success": False, "message": "유효한 sceneId를 찾을 수 없습니다."}

            # 3. 장면 실행
            exec_res = await client.post(
                f"https://api.smartthings.com/v1/scenes/{scene_id}/execute",
                headers=headers
            )
            if exec_res.status_code in [200, 204]:
                return {
                    "success": True,
                    "message": f"'{target_scene.get('sceneName')}' 장면이 성공적으로 실행되었습니다.",
                    "sceneId": scene_id
                }
            else:
                logging.error(f"SmartThings scene execute error: {exec_res.status_code} {exec_res.text}")
                return {"success": False, "message": f"장면 실행 실패 (상태 코드: {exec_res.status_code})"}

    except Exception as e:
        logging.error(f"SmartThings API Exception: {e}")
        return {"success": False, "message": f"호출 중 오류 발생: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
