#!/bin/bash
# 은퇴설계 앱 실행 스크립트 (nginx 리버스프록시 환경)
# nginx 설정: nginx/retirement.conf 참고
# SSL 발급: sudo certbot --nginx -d kairang.pe.kr

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# .venv 활성화 (있는 경우)
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "================================================"
echo "  은퇴설계 서버 시작 (보안 모드)"
echo "================================================"

# 백엔드: 127.0.0.1만 바인딩 (외부 직접 접근 차단)
echo "백엔드 API 시작 (127.0.0.1:9080)..."
uvicorn backend.api:app \
    --host 127.0.0.1 \
    --port 9080 \
    --workers 2 \
    --no-access-log &
BACKEND_PID=$!

# 종료 시 프로세스 정리
trap "echo '종료 중...'; kill $BACKEND_PID 2>/dev/null; exit" INT TERM EXIT

# 백엔드 기동 대기
sleep 3

# 프론트엔드: .streamlit/config.toml에서 127.0.0.1:8443 바인딩
echo "Streamlit 프론트엔드 시작 (127.0.0.1:8443)..."
echo "  공개 접속: https://kairang.pe.kr  (nginx HTTPS)"
streamlit run frontend/app.py \
    --server.headless true \
    --server.address 127.0.0.1 \
    --server.port 8443
