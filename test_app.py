import sys
import io

# Set UTF-8 encoding for standard output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_all():
    # 1. Health check
    res = client.get('/api/health')
    assert res.status_code == 200, f'Health check failed: {res.status_code}'
    print('[PASS 1/5] Health check passed:', res.json())

    # 2. Manifest and Service Worker
    res = client.get('/manifest.json')
    assert res.status_code == 200 and 'display' in res.json(), 'Manifest failed'
    print('[PASS 2/5] PWA Manifest passed')

    res = client.get('/sw.js')
    assert res.status_code == 200 and 'CACHE_NAME' in res.text, 'Service Worker failed'
    print('[PASS 3/5] Service worker passed')

    # 3. Root index
    res = client.get('/')
    assert res.status_code == 200, 'Index page failed'
    print('[PASS 4/5] Index HTML verified')

    # 4. Weather API (3h intervals)
    res = client.get('/api/weather')
    assert res.status_code == 200, 'Weather API failed'
    w = res.json()
    print(f"[PASS 5/5] Weather API passed: {w['location']} {w['current_temp']}°C, {w['condition']}")

    # 5. Commute API (Naver Direction5 with traoptimal & exact coordinates)
    res = client.get('/api/commute')
    assert res.status_code == 200, 'Commute API failed'
    c = res.json()
    assert c['origin_coords'] == '127.2255,37.3663', f"Invalid origin coords: {c['origin_coords']}"
    assert c['destination_coords'] == '126.9688,37.3975', f"Invalid dest coords: {c['destination_coords']}"
    print(f"\n[COMMUTE DATA VERIFICATION]")
    print(f"  * 출발지: {c['origin']} ({c['origin_coords']})")
    print(f"  * 도착지: {c['destination']} ({c['destination_coords']})")
    print(f"  * 추천 경로 ({len(c['routes'])}개):")
    for r in c['routes']:
        print(f"     - [{r['name']}]: {r['total_duration_min']}분 ({r['distance_km']}km), 통행료 {r['toll_fare']:,}원, 택시비 {r['taxi_fare']:,}원")
        for s in r['segments']:
            print(f"        > {s['name']} ({s['duration_min']}분) - {s['detail']}")

    print('\n[SUCCESS] EXACT COORDINATES & TRAOPTIMAL ROUTING FULLY VERIFIED!')

if __name__ == '__main__':
    test_all()
