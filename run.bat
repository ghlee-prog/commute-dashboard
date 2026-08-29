@echo off
chcp 65001 > nul
title PWA 출근 대시보드 서버
echo =====================================================
echo        출근 대시보드 PWA (FastAPI + Tailwind CSS)
echo =====================================================
echo.
echo [1/2] 필수 패키지 점검 중...
pip install -r requirements.txt --quiet
echo.
echo [2/2] 서버 시작 중: http://localhost:8000
echo 아이폰과 동일한 Wi-Fi에 연결된 경우 IP주소:8000 으로 접속 가능합니다.
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
