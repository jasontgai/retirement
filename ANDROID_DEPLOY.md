# 안드로이드 배포 가이드

Streamlit 웹앱을 안드로이드 어플처럼 만들고 배포하는 4가지 방법입니다.
난이도가 낮은 순으로 정리했습니다.

---

## 방법 1: 같은 WiFi에서 접속 (가장 쉬움, 30분)

**용도**: 본인/가족이 집에서 사용

### 단계
1. PC에서 백엔드 + 프론트엔드 실행
   ```powershell
   .\run.ps1
   ```
2. PC의 IP 확인 (PowerShell):
   ```powershell
   ipconfig | findstr IPv4
   ```
   → 예: `192.168.0.10`
3. 안드로이드 폰 크롬에서 접속:
   ```
   http://192.168.0.10:8501
   ```
4. 크롬 우측 상단 ⋮ → **"홈 화면에 추가"** 누르면 어플 아이콘 생성

**장점**: 설정 없음, 즉시 가능
**단점**: PC 켜져 있어야 함, 외부 접속 안 됨

---

## 방법 2: 클라우드 배포 + PWA (지인 배포 가능, 1~2시간)

**용도**: 지인에게 URL 공유, 어디서든 접속

### 단계 (Streamlit Cloud 무료 플랜 사용)

1. **GitHub에 코드 업로드**
   ```bash
   git init
   git add .
   git commit -m "init"
   git remote add origin https://github.com/<본인>/retirement_app.git
   git push -u origin main
   ```

2. **백엔드 배포** (Render.com 또는 Railway.app 무료):
   - Render.com 가입 → New Web Service → GitHub 연결
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn backend.api:app --host 0.0.0.0 --port $PORT`
   - 배포 후 URL 메모: 예) `https://retirement-api.onrender.com`

3. **프론트엔드 배포** (Streamlit Community Cloud 무료):
   - https://share.streamlit.io 가입
   - GitHub 연결, `frontend/app.py` 선택
   - **Secrets** 설정 추가:
     ```toml
     API_BASE = "https://retirement-api.onrender.com"
     ```
   - 배포 URL: 예) `https://retirement-planner.streamlit.app`

4. **지인 공유**
   - URL 카톡으로 공유
   - 받은 사람: 크롬에서 접속 → ⋮ → **"홈 화면에 추가"**
   - 어플처럼 동작 (PWA)

**장점**: 무료, 어디서든 접속, 자동 HTTPS
**단점**: 무료 플랜은 트래픽 적을 때 절전모드 (첫 접속 30초 지연)

---

## 방법 3: PWA → APK 변환 (진짜 어플 파일, 30분)

**용도**: APK 파일을 직접 카톡으로 보내고 싶을 때

### 전제 조건
방법 2의 클라우드 배포가 완료되어 있어야 함 (HTTPS URL 필요)

### 단계 (PWABuilder 사용 - Microsoft 공식 무료 도구)

1. https://www.pwabuilder.com 접속
2. 배포한 Streamlit URL 입력 → "Start"
3. PWA 점수 체크 (Manifest, Service Worker 등)
4. 부족한 항목이 있으면 자동 생성 옵션 클릭
5. **"Package For Stores"** → **Android** 탭 클릭
6. 옵션 설정:
   - Package ID: 예) `com.yourname.retirement`
   - App name: `은퇴설계`
   - Signing key: "New" 선택 (자동 생성)
7. **Generate** → APK + 서명키 ZIP 다운로드

### 안드로이드 폰에 설치
1. APK 파일을 카톡/메일로 폰에 전송
2. 파일 매니저에서 APK 탭
3. "출처를 알 수 없는 앱 설치 허용" → 설치
4. 끝!

**장점**: 진짜 APK 파일, 오프라인 동작 가능 (Service Worker)
**단점**: WebView 기반이라 진짜 네이티브 앱은 아님

---

## 방법 4: TWA (Trusted Web Activity, Play Store용)

**용도**: 나중에 Play Store에 올리고 싶을 때

PWABuilder에서 생성한 APK는 사실 TWA 방식입니다. Play Store 등록 시:
- 개발자 등록비 $25 (1회)
- Digital Asset Links 설정 필요 (도메인 소유권 증명)
- 자세한 가이드: https://web.dev/articles/using-a-pwa-in-your-android-app

이 단계까지는 지인 배포에서는 불필요합니다.

---

## 보안/배포 체크리스트

### 사내/지인 배포 시
- [ ] 백엔드 CORS는 특정 도메인만 허용으로 변경
- [ ] API 키 없이 접근 가능하므로 입력 데이터 검증 강화
- [ ] 민감정보(자산/연금)가 서버에 저장되지 않도록 stateless 유지
- [ ] HTTPS 필수 (Streamlit Cloud, Render는 자동 제공)
- [ ] 백엔드 rate limiting (slowapi 같은 것 추가 권장)

### 운영 환경 권장 설정
- 백엔드: Gunicorn + Uvicorn workers (`gunicorn backend.api:app -w 4 -k uvicorn.workers.UvicornWorker`)
- 프론트엔드: Streamlit `--server.headless true --server.enableCORS false`
- 로깅: 파일 또는 외부 서비스 (Sentry 등)
- 모니터링: 헬스체크 엔드포인트 활용

---

## 향후 진짜 안드로이드 네이티브 앱으로 가려면

PWA로 시작해서 사용성이 검증되면 다음 단계 추천:

1. **Flutter** (가장 추천)
   - 현재 만든 FastAPI 백엔드 그대로 재사용
   - UI만 Flutter로 다시 작성
   - iOS/안드로이드 동시 빌드

2. **Kivy/BeeWare** (Python 유지)
   - Python으로 안드로이드 APK 빌드 가능
   - UI가 머터리얼 디자인 대비 다소 투박

3. **React Native + Expo**
   - JS 한 코드로 iOS/안드로이드
   - PWABuilder로 시작했다가 마이그레이션 가능

---

## 문제 해결

### 휴대폰에서 PC 접속 안 됨
- Windows 방화벽에서 8000, 8501 포트 인바운드 허용
- 같은 WiFi인지 확인
- PC IP 다시 확인 (`ipconfig`)

### Streamlit Cloud에서 백엔드 호출 실패
- `API_BASE` Secrets 설정 확인
- 백엔드 CORS `allow_origins` 확인
- Render 무료 플랜은 첫 호출 시 30초 콜드스타트

### PWA 홈화면 추가 메뉴 안 보임
- HTTPS 필수 (localhost 또는 https://만 가능)
- manifest.json 정상 응답 확인
- 크롬 DevTools → Application → Manifest 진단
