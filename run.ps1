# 은퇴설계 어플 실행 스크립트 (PowerShell)
# 사용법: .\run.ps1

# 1) 백엔드 실행 (별도 창)
Write-Host "백엔드 API 서버 시작 (포트 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload"

# 잠시 대기
Start-Sleep -Seconds 3

# 2) 프론트엔드 실행 (현재 창)
Write-Host "Streamlit 프론트엔드 시작 (포트 8501)..." -ForegroundColor Green
Write-Host "PC 브라우저: http://localhost:8501" -ForegroundColor Yellow
Write-Host "휴대폰 접속: http://<PC IP>:8501  (같은 WiFi)" -ForegroundColor Yellow
streamlit run frontend/app.py --server.address=0.0.0.0 --server.port=8501
