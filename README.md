# 은퇴설계 어플 (Streamlit + FastAPI)

한국 연금/세법 기반 은퇴설계 모바일 어플입니다.
PC에서 백엔드 + 프론트엔드를 실행하면 안드로이드 폰에서 어플처럼 사용할 수 있습니다.

## 아키텍처

```
┌─────────────────────────┐
│   안드로이드 폰         │
│   (크롬 / PWA / APK)    │
└────────┬────────────────┘
         │ HTTP
         ▼
┌─────────────────────────┐
│   Streamlit Frontend    │  포트 8501
│   (frontend/app.py)     │
└────────┬────────────────┘
         │ HTTP API
         ▼
┌─────────────────────────┐
│   FastAPI Backend       │  포트 8000
│   (backend/api.py)      │
└────────┬────────────────┘
         │ import
         ▼
┌─────────────────────────┐
│   계산 엔진 (modules/)  │
│   - 국민연금 / 사적연금 │
│   - 주택연금 / 세금     │
│   - 건보료 / 분석엔진   │
└─────────────────────────┘
```

## 디렉토리 구조

```
retirement_app/
├── backend/
│   └── api.py                 # FastAPI 서버 (REST API)
├── frontend/
│   ├── app.py                 # Streamlit 모바일 UI
│   └── static/
│       └── manifest.json      # PWA 설정 (홈화면 추가용)
├── modules/                   # 1단계 계산 엔진 (재활용)
│   ├── models.py
│   ├── analyzer.py
│   ├── national_pension.py
│   ├── private_pension.py
│   ├── house_pension.py
│   └── tax_calculator.py
├── config/
│   └── tax_config.py          # 세법/연금 상수 (매년 업데이트)
├── deploy/
│   └── ANDROID_DEPLOY.md      # ★ 안드로이드 배포 4가지 방법 가이드
├── requirements.txt
├── run.sh                     # Linux/Mac 실행
├── run.ps1                    # Windows 실행
└── main.py                    # CLI 데모 (이전 버전, 참고용)
```

## 빠른 시작

### 1) 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 2) 어플 실행
**Windows:**
```powershell
.\run.ps1
```

**Linux/Mac:**
```bash
chmod +x run.sh && ./run.sh
```

또는 수동으로 (두 개의 터미널):
```bash
# 터미널 1
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload

# 터미널 2
streamlit run frontend/app.py --server.address=0.0.0.0
```

### 3) 안드로이드 폰에서 접속
1. PC IP 확인: `ipconfig` (Windows) 또는 `ifconfig` (Mac/Linux)
2. 폰 크롬에서 `http://<PC IP>:8501` 접속
3. 크롬 메뉴 ⋮ → **"홈 화면에 추가"** → 어플처럼 사용

## API 문서

백엔드 실행 후: http://localhost:8000/docs (Swagger 자동 생성)

| 엔드포인트 | 설명 |
|---|---|
| `GET /health` | 헬스체크 |
| `POST /analyze` | 전체 은퇴설계 분석 (메인) |
| `GET /pension/start-age/{birth_year}` | 국민연금 정상 수급연령 |
| `POST /pension/scenarios` | 수급 시기별 시나리오 비교 |
| `POST /house-pension` | 주택연금 추정 |
| `POST /house-pension/compare` | 주택연금 vs 매각 비교 |
| `POST /tax/income` | 종합소득세 계산 |
| `POST /tax/health` | 건강보험료 계산 |
| `POST /tax/dependent` | 피부양자 자격 확인 |

## UI 구성 (5개 탭)

1. **본인** — 출생년도, 은퇴희망 연령, 현재 소득
2. **연금** — 국민연금/퇴직연금/IRP/연금저축 등록
3. **자산** — 부동산/금융/회원권/차량/부채 (서브탭)
4. **지출** — 은퇴 후 월 예상 지출
5. **분석** — 종합 분석 결과 + 핵심 제언

## 안드로이드 배포 방법 (요약)

자세한 내용은 `deploy/ANDROID_DEPLOY.md` 참고.

| 방법 | 난이도 | 용도 |
|---|---|---|
| **WiFi 접속** | ⭐ | 본인/가족 |
| **Streamlit Cloud + PWA** | ⭐⭐ | 지인 URL 공유 |
| **PWABuilder → APK** | ⭐⭐⭐ | APK 직접 공유 ★ 추천 |
| **TWA + Play Store** | ⭐⭐⭐⭐⭐ | 정식 배포 |

지인 배포 목적이면 **PWA → APK 변환**이 가장 깔끔합니다:
1. 코드를 GitHub에 올리고
2. 백엔드는 Render.com (무료), 프론트는 Streamlit Cloud (무료) 배포
3. https://www.pwabuilder.com 에서 URL 입력 → APK 다운로드
4. APK를 카톡으로 공유

## 보안 주의사항

⚠️ 현재 설정은 **개발/테스트용**입니다. 실제 배포 시:

- `backend/api.py`의 `allow_origins=["*"]`를 특정 도메인으로 변경
- 입력값 검증 강화 (음수, 비현실적 값)
- HTTPS 필수 (Streamlit Cloud는 자동)
- 사용자 정보는 서버에 저장하지 않음 (현재도 stateless)
- Rate limiting 추가 (slowapi 등)

## 향후 확장

이 구조의 장점은 **백엔드(modules + backend)는 그대로 두고 프론트만 갈아끼울 수 있다**는 것입니다.

- 진짜 네이티브 앱 → Flutter, React Native, Kivy 중 하나로 프론트 재구현
- 백엔드는 그대로 재사용
- DB 추가 (사용자 프로필 저장) — Oracle/MySQL 등 익숙하신 DB 사용
- Stata 연동 → 백엔드에 새 엔드포인트 추가하여 몬테카를로 시뮬레이션

## ⚠️ 면책

본 시스템은 참고용 추정치입니다. 정확한 금액은 다음에서 확인:
- 국민연금: https://www.nps.or.kr
- 주택연금: https://www.hf.go.kr
- 건강보험: https://www.nhis.or.kr

실제 은퇴설계는 재무설계사·세무사 상담을 권장합니다.
