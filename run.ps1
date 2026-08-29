# PowerShell Startup Script for Commute Dashboard PWA

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "       🌅 PWA 출근 대시보드 서버를 시작합니다       " -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Cyan

# Check dependencies
Write-Host "[1/3] Python 환경 및 패키지 확인 중..." -ForegroundColor Gray
python -m pip install -r requirements.txt --quiet

# Find Local IP address for mobile iPhone access
$localIp = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*", "Ethernet*", "이더넷*", "무선*" -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike "169.254*" -and $_.IPAddress -notlike "127.*" } | Select-Object -First 1).IPAddress

Write-Host "[2/3] 서버 주소 확인:" -ForegroundColor Green
Write-Host "  - PC 로컬 접속:   http://localhost:8000" -ForegroundColor White
if ($localIp) {
    Write-Host "  - 아이폰(동일 Wi-Fi): http://${localIp}:8000" -ForegroundColor Yellow
}

Write-Host "`n[3/3] FastAPI 백엔드 서버 가동 중 (종료: Ctrl + C)..." -ForegroundColor Cyan
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
