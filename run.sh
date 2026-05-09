#!/bin/bash
# 은퇴설계 어플 실행 스크립트
# 사용법: chmod +x run.sh && ./run.sh

# 백엔드 백그라운드 실행
echo "백엔드 API 서버 시작 (포트 8000)..."
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 종료 처리
trap "echo '종료 중...'; kill $BACKEND_PID 2>/dev/null; exit" INT TERM EXIT

sleep 3

# 프론트엔드 실행
echo "Streamlit 프론트엔드 시작 (포트 8501)..."
echo "PC 브라우저: http://localhost:8501"
echo "휴대폰 접속: http://<PC IP>:8501 (같은 WiFi)"
streamlit run frontend/app.py --server.address=0.0.0.0 --server.port=8501
