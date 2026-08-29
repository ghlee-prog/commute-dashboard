/**
 * iPhone Safari PWA Commute Dashboard Main Logic
 * Integrated with Naver Maps Direction5 API
 */

// Application State
const state = {
  weather: null,
  commute: null,
  smarthome: null,
  selectedRouteId: 'route_naver_traoptimal',
  nextArrivalSeconds: 180,
  countdownInterval: null,
  isRefreshing: false
};

// --- Web Audio Tactile Feedback ---
function playHapticSound(type = 'click') {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    if (type === 'off') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(180, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(80, ctx.currentTime + 0.12);
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.01, ctx.currentTime + 0.12);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.12);
    } else if (type === 'success') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.01, ctx.currentTime + 0.15);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.15);
    } else {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(600, ctx.currentTime);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.04);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.04);
    }
  } catch (e) {
    // Silent fail if audio is locked before user interaction
  }

  // Mobile Vibration API if available
  if (navigator.vibrate) {
    if (type === 'off') {
      navigator.vibrate([40, 30, 40]);
    } else {
      navigator.vibrate(25);
    }
  }
}

// --- Toast Notification ---
function showToast(message, type = 'info') {
  const toast = document.getElementById('toast-notification');
  const toastMsg = document.getElementById('toast-message');
  const toastIcon = document.getElementById('toast-icon');

  if (!toast || !toastMsg) return;

  toastMsg.textContent = message;
  
  if (type === 'success') {
    toast.className = 'fixed top-4 left-1/2 -translate-x-1/2 z-50 px-4 py-2.5 rounded-full bg-emerald-950/90 border border-emerald-500/50 text-emerald-200 text-sm font-medium shadow-2xl flex items-center gap-2 backdrop-blur-md toast-slide toast-visible';
    toastIcon.innerHTML = `<svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>`;
  } else if (type === 'warning') {
    toast.className = 'fixed top-4 left-1/2 -translate-x-1/2 z-50 px-4 py-2.5 rounded-full bg-amber-950/90 border border-amber-500/50 text-amber-200 text-sm font-medium shadow-2xl flex items-center gap-2 backdrop-blur-md toast-slide toast-visible';
    toastIcon.innerHTML = `<svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>`;
  } else {
    toast.className = 'fixed top-4 left-1/2 -translate-x-1/2 z-50 px-4 py-2.5 rounded-full bg-slate-900/95 border border-slate-700 text-slate-200 text-sm font-medium shadow-2xl flex items-center gap-2 backdrop-blur-md toast-slide toast-visible';
    toastIcon.innerHTML = `<svg class="w-4 h-4 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`;
  }

  setTimeout(() => {
    toast.classList.remove('toast-visible');
    toast.classList.add('toast-hidden');
  }, 3200);
}

// --- Live Clock & Greeting ---
function updateClockAndGreeting() {
  const now = new Date();
  const timeEl = document.getElementById('current-time-text');
  const dateEl = document.getElementById('current-date-text');
  const greetingEl = document.getElementById('greeting-text');

  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');

  if (timeEl) timeEl.textContent = `${hours}:${minutes}:${seconds}`;

  if (dateEl) {
    const days = ['일', '월', '화', '수', '목', '금', '토'];
    const month = now.getMonth() + 1;
    const date = now.getDate();
    const dayName = days[now.getDay()];
    dateEl.textContent = `${month}월 ${date}일 (${dayName})`;
  }

  if (greetingEl) {
    const h = now.getHours();
    if (h >= 5 && h < 11) {
      greetingEl.textContent = '좋은 아침입니다! 광주 ➔ 안양 안전운전 하세요 ☀️';
    } else if (h >= 11 && h < 14) {
      greetingEl.textContent = '점심시간이 다가옵니다. 오늘도 힘내세요! 🥪';
    } else if (h >= 14 && h < 18) {
      greetingEl.textContent = '오후 업무도 화이팅! 곧 안전한 퇴근길 되세요 💪';
    } else if (h >= 18 && h < 22) {
      greetingEl.textContent = '오늘 하루도 수고 많으셨습니다 🌙';
    } else {
      greetingEl.textContent = '편안한 밤 되세요. 내일도 파이팅! ✨';
    }
  }
}

// --- API Calls ---
async function fetchWeather() {
  try {
    const res = await fetch('/api/weather');
    if (!res.ok) throw new Error('Weather fetch failed');
    state.weather = await res.json();
    renderWeather();
  } catch (err) {
    console.error('Weather error:', err);
  }
}

async function fetchCommute() {
  try {
    const res = await fetch('/api/commute');
    if (!res.ok) throw new Error('Commute fetch failed');
    state.commute = await res.json();
    
    // Pick current selected route or default
    const currentRoute = state.commute.routes.find(r => r.id === state.selectedRouteId) || state.commute.routes[0];
    if (currentRoute) {
      state.selectedRouteId = currentRoute.id;
      state.nextArrivalSeconds = currentRoute.next_arrival_seconds;
    }
    renderCommute();
  } catch (err) {
    console.error('Commute error:', err);
  }
}

async function fetchSmartHome() {
  try {
    const res = await fetch('/api/smarthome/status');
    if (!res.ok) throw new Error('SmartHome fetch failed');
    state.smarthome = await res.json();
    renderSmartHome();
  } catch (err) {
    console.error('SmartHome error:', err);
  }
}

// --- Render Functions ---
function renderWeather() {
  const w = state.weather;
  if (!w) return;

  const locHeader = document.getElementById('weather-location-header');
  const tempEl = document.getElementById('weather-temp');
  const conditionEl = document.getElementById('weather-condition');
  const outfitTipEl = document.getElementById('weather-outfit-tip');
  const umbrellaBadgeEl = document.getElementById('umbrella-badge');
  const pm10BadgeEl = document.getElementById('pm10-badge');
  const pm25BadgeEl = document.getElementById('pm25-badge');
  const hourlyContainer = document.getElementById('hourly-forecast-container');

  if (locHeader) locHeader.textContent = `오늘 날씨 · ${w.location}`;
  if (tempEl) tempEl.innerHTML = `${w.current_temp}<span class="text-3xl text-slate-400 font-light">°C</span>`;
  if (conditionEl) conditionEl.textContent = `${w.condition} · 체감 ${w.feels_like}°C (최고 ${w.max_temp}°/최저 ${w.min_temp}°)`;
  if (outfitTipEl) outfitTipEl.textContent = w.outfit_tip;

  if (umbrellaBadgeEl) {
    if (w.umbrella_needed) {
      umbrellaBadgeEl.className = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 pulse-badge';
      umbrellaBadgeEl.innerHTML = `<span>☔</span> 우산 챙기세요!`;
      umbrellaBadgeEl.classList.remove('hidden');
    } else {
      umbrellaBadgeEl.className = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700';
      umbrellaBadgeEl.innerHTML = `<span>🌂</span> 우산 불필요 (강수 ${w.rain_probability}%)`;
    }
  }

  if (pm10BadgeEl) {
    const isGood = w.air_quality.pm10_status === '좋음';
    pm10BadgeEl.className = `px-2 py-0.5 rounded-md text-xs font-medium ${isGood ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60' : 'bg-amber-950/80 text-amber-300 border border-amber-800/60'}`;
    pm10BadgeEl.textContent = `미세 ${w.air_quality.pm10} ㎍ (${w.air_quality.pm10_status})`;
  }

  if (pm25BadgeEl) {
    const isGood = w.air_quality.pm25_status === '좋음';
    pm25BadgeEl.className = `px-2 py-0.5 rounded-md text-xs font-medium ${isGood ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60' : 'bg-amber-950/80 text-amber-300 border border-amber-800/60'}`;
    pm25BadgeEl.textContent = `초미세 ${w.air_quality.pm25} ㎍ (${w.air_quality.pm25_status})`;
  }

  // 3-hour Interval Forecast Pills (Now ~ 15 Hours)
  if (hourlyContainer && w.hourly_forecast) {
    hourlyContainer.innerHTML = w.hourly_forecast.map((h, idx) => `
      <div class="flex-shrink-0 flex flex-col items-center justify-between py-2.5 px-2 rounded-2xl ${idx === 0 ? 'bg-indigo-600/25 border border-indigo-500/50 text-indigo-100 shadow-md' : 'bg-slate-800/60 border border-slate-700/60 text-slate-300'} text-center flex-1 min-w-[56px] transition-all">
        <span class="text-[11px] font-bold ${idx === 0 ? 'text-indigo-300' : 'text-slate-400'}">${h.time}</span>
        <div class="my-1 text-lg">
          ${h.icon === 'sun' ? '☀️' : h.icon === 'cloud-sun' ? '⛅' : h.icon === 'cloud' ? '☁️' : '🌧️'}
        </div>
        <span class="text-xs font-black text-white">${h.temp}°</span>
        <span class="text-[10px] text-sky-400 font-semibold mt-0.5">${h.rain_pop}%</span>
      </div>
    `).join('');
  }
}

function renderCommute() {
  const c = state.commute;
  if (!c) return;

  const currentRoute = c.routes.find(r => r.id === state.selectedRouteId) || c.routes[0];
  
  const originEl = document.getElementById('commute-origin');
  const destEl = document.getElementById('commute-destination');
  const mainDurationEl = document.getElementById('commute-main-duration');
  const arrivalTimeEl = document.getElementById('commute-arrival-time');
  const trafficStatusBadge = document.getElementById('commute-traffic-status');
  const alertEl = document.getElementById('commute-live-alert');
  
  const distanceText = document.getElementById('commute-distance-text');
  const tollText = document.getElementById('commute-toll-text');
  const taxiText = document.getElementById('commute-taxi-text');
  
  const segmentsContainer = document.getElementById('commute-segments-container');
  const tabsContainer = document.getElementById('commute-tabs-container');

  if (originEl) originEl.textContent = c.origin;
  if (destEl) destEl.textContent = c.destination;
  if (mainDurationEl) mainDurationEl.innerHTML = `${currentRoute.total_duration_min}<span class="text-base font-normal text-slate-400 ml-0.5">분</span>`;
  if (arrivalTimeEl) arrivalTimeEl.textContent = `${currentRoute.estimated_arrival_time} 도착 예정 (지금 출발 시)`;

  if (trafficStatusBadge) {
    const isSmooth = currentRoute.traffic_status.includes('원활');
    trafficStatusBadge.className = `inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${isSmooth ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'}`;
    trafficStatusBadge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full ${isSmooth ? 'bg-emerald-400' : 'bg-amber-400'} mr-1 animate-pulse"></span>${currentRoute.traffic_status}`;
  }

  // Metrics Grid
  if (distanceText) distanceText.textContent = `${currentRoute.distance_km} km`;
  if (tollText) tollText.textContent = currentRoute.toll_fare > 0 ? `${currentRoute.toll_fare.toLocaleString()}원` : '무료';
  if (taxiText) taxiText.textContent = currentRoute.taxi_fare > 0 ? `${currentRoute.taxi_fare.toLocaleString()}원` : '-';

  if (alertEl && c.live_traffic_alert) {
    alertEl.textContent = `📢 ${c.live_traffic_alert}`;
  }

  // Render Mode Tabs
  if (tabsContainer) {
    tabsContainer.innerHTML = c.routes.map(r => {
      const isSelected = r.id === currentRoute.id;
      let label = '최적경로';
      let icon = '✨';
      if (r.id === 'route_naver_trafast') {
        label = '빠른길';
        icon = '⚡';
      } else if (r.id === 'route_car_free') {
        label = '무료도로';
        icon = '🛣️';
      } else if (r.mode === 'bus') {
        label = '대중교통';
        icon = '🚌';
      }

      return `
        <button onclick="selectCommuteRoute('${r.id}')" 
          class="flex-1 py-2 px-2 rounded-xl text-xs font-medium transition-all flex items-center justify-center gap-1 ${isSelected ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-bold' : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'} btn-tactile">
          <span>${icon}</span>
          <span>${label}</span>
          <span class="text-[11px] opacity-85">${r.total_duration_min}분</span>
        </button>
      `;
    }).join('');
  }

  // Render Segments Timeline
  if (segmentsContainer && currentRoute.segments) {
    segmentsContainer.innerHTML = currentRoute.segments.map((s, idx) => `
      <div class="flex items-start gap-3 relative pb-3 last:pb-0">
        ${idx < currentRoute.segments.length - 1 ? '<div class="absolute left-3.5 top-6 bottom-0 w-0.5 bg-slate-700"></div>' : ''}
        <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${s.type === 'car' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40' : s.type === 'bus' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/40' : 'bg-slate-700 text-slate-300'} z-10">
          ${s.type === 'car' ? '🚗' : s.type === 'bus' ? '🚌' : '🚶'}
        </div>
        <div class="flex-1 pt-0.5">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-200">${s.name}</span>
            <span class="text-[11px] font-medium text-slate-400">${s.duration_min}분</span>
          </div>
          ${s.detail ? `<p class="text-[11px] text-slate-400 mt-0.5 leading-tight">${s.detail}</p>` : ''}
        </div>
      </div>
    `).join('');
  }
}

function selectCommuteRoute(routeId) {
  playHapticSound('click');
  state.selectedRouteId = routeId;
  renderCommute();
}

function renderSmartHome() {
  const sh = state.smarthome;
  if (!sh) return;

  const masterBtn = document.getElementById('master-off-button');
  const masterBtnText = document.getElementById('master-off-text');
  const masterBtnSubtext = document.getElementById('master-off-subtext');
  const masterBtnIcon = document.getElementById('master-off-icon');
  const activeCountBadge = document.getElementById('smarthome-active-count');
  const powerWattsEl = document.getElementById('smarthome-power-watts');
  const savingsWonEl = document.getElementById('smarthome-savings-won');
  const devicesGrid = document.getElementById('smarthome-devices-grid');

  if (activeCountBadge) {
    activeCountBadge.textContent = sh.all_off ? '전체 꺼짐' : `${sh.active_count}개 켜짐`;
    activeCountBadge.className = `px-2.5 py-0.5 rounded-full text-xs font-bold ${sh.all_off ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-amber-950 text-amber-300 border border-amber-800 animate-pulse'}`;
  }

  if (powerWattsEl) powerWattsEl.textContent = `${sh.total_active_power_watts}W`;
  if (savingsWonEl) savingsWonEl.textContent = `월 약 ${sh.estimated_daily_savings_won.toLocaleString()}원`;

  // Master Off/On Button State
  if (masterBtn) {
    if (sh.all_off) {
      masterBtn.className = 'w-full py-4 px-6 rounded-2xl btn-master-all-off-state text-white font-bold text-base shadow-xl flex items-center justify-center gap-3 transition-all btn-tactile';
      if (masterBtnText) masterBtnText.textContent = '모든 조명이 꺼져있습니다';
      if (masterBtnSubtext) masterBtnSubtext.textContent = '터치하여 조명 다시 켜기';
      if (masterBtnIcon) masterBtnIcon.innerHTML = `
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
        </svg>
      `;
    } else {
      masterBtn.className = 'w-full py-4 px-6 rounded-2xl btn-master-off text-white font-bold text-base shadow-2xl flex items-center justify-center gap-3 transition-all btn-tactile';
      if (masterBtnText) masterBtnText.textContent = '출근 전 전체 조명 끄기';
      if (masterBtnSubtext) masterBtnSubtext.textContent = `켜진 기기 ${sh.active_count}개 일괄 소등 (${sh.total_active_power_watts}W 절약)`;
      if (masterBtnIcon) masterBtnIcon.innerHTML = `
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      `;
    }
  }

  // Device list grid
  if (devicesGrid && sh.devices) {
    devicesGrid.innerHTML = sh.devices.map(d => `
      <div onclick="toggleSmartDevice('${d.id}')"
        class="flex items-center justify-between p-3.5 rounded-2xl border transition-all cursor-pointer ${d.is_on ? 'bg-slate-800/80 border-amber-500/40 text-white shadow-md' : 'bg-slate-900/50 border-slate-800/80 text-slate-400'} glass-card-interactive">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center text-base ${d.is_on ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-slate-800 text-slate-500'}">
            ${d.type === 'plug' ? '🔌' : d.room === '침실' ? '🛏️' : d.room === '주방' ? '🍳' : '💡'}
          </div>
          <div>
            <div class="text-xs font-bold text-slate-200">${d.name}</div>
            <div class="text-[11px] text-slate-400">${d.room} · ${d.power_watts}W</div>
          </div>
        </div>
        <!-- iOS Toggle Switch Look -->
        <div class="w-12 h-6.5 rounded-full p-0.5 transition-colors duration-200 flex items-center ${d.is_on ? 'bg-amber-400 justify-end' : 'bg-slate-700 justify-start'}">
          <div class="w-5.5 h-5.5 rounded-full bg-white shadow-md transform transition-transform"></div>
        </div>
      </div>
    `).join('');
  }
}

async function handleMasterToggle() {
  if (!state.smarthome) return;
  const willTurnOn = state.smarthome.all_off;

  playHapticSound(willTurnOn ? 'click' : 'off');

  try {
    const res = await fetch('/api/smarthome/toggle-all', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ turn_on: willTurnOn })
    });
    if (!res.ok) throw new Error('Toggle all failed');
    state.smarthome = await res.json();
    renderSmartHome();

    if (!willTurnOn) {
      showToast('모든 조명이 꺼졌습니다. 광주 ➔ 안양 안전운전 되세요! 💡❌', 'success');
    } else {
      showToast('모든 조명을 다시 켰습니다. ✨', 'info');
    }
  } catch (err) {
    console.error('Master toggle error:', err);
    showToast('스마트홈 제어 중 오류가 발생했습니다.', 'warning');
  }
}

async function toggleSmartDevice(deviceId) {
  playHapticSound('click');
  try {
    const res = await fetch(`/api/smarthome/device/${deviceId}/toggle`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Toggle device failed');
    state.smarthome = await res.json();
    renderSmartHome();
  } catch (err) {
    console.error('Device toggle error:', err);
  }
}

// --- Refresh All Dashboard Data ---
async function refreshDashboard(showNotification = true) {
  if (state.isRefreshing) return;
  state.isRefreshing = true;

  const refreshIcon = document.getElementById('refresh-icon');
  if (refreshIcon) refreshIcon.classList.add('animate-spin');

  playHapticSound('click');

  await Promise.allSettled([
    fetchWeather(),
    fetchCommute(),
    fetchSmartHome()
  ]);

  if (refreshIcon) {
    setTimeout(() => refreshIcon.classList.remove('animate-spin'), 600);
  }

  state.isRefreshing = false;
  if (showNotification) {
    showToast('대시보드 데이터가 최신으로 갱신되었습니다 🔄', 'info');
  }
}

// --- iOS Safari Add to Home Screen Modal ---
function checkPWAStatus() {
  const isStandalone = window.navigator.standalone || window.matchMedia('(display-mode: standalone)').matches;
  const pwaBanner = document.getElementById('pwa-install-banner');
  
  if (isStandalone) {
    if (pwaBanner) pwaBanner.style.display = 'none';
  } else {
    if (pwaBanner) pwaBanner.classList.remove('hidden');
  }
}

function openPWAGuide() {
  playHapticSound('click');
  const modal = document.getElementById('pwa-guide-modal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }
}

function closePWAGuide() {
  playHapticSound('click');
  const modal = document.getElementById('pwa-guide-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
  // 1. Clock & Greeting
  updateClockAndGreeting();
  setInterval(updateClockAndGreeting, 1000);

  // 2. Initial Data Fetch
  refreshDashboard(false);

  // 3. Auto refresh every 45 seconds
  setInterval(() => {
    refreshDashboard(false);
  }, 45000);

  // 4. PWA & Service Worker Registration
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then((reg) => console.log('Service Worker Registered!', reg.scope))
      .catch((err) => console.warn('Service Worker registration error:', err));
  }

  // 5. Check PWA installation state
  checkPWAStatus();
});
