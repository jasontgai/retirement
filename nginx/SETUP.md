# HTTPS 설정 가이드 (Windows + Caddy)

## 전제 조건
- Windows 11 PC (개발 PC = 서버)
- 도메인 `kairang.pe.kr` DNS A 레코드가 집 공인 IP를 가리키는 상태
- 공유기 포트포워딩: 외부 80, 443 → 이 PC의 내부 IP
- 외부 8501, 9080 포트포워딩은 **삭제** (직접 노출 차단)

> 공인 IP 확인: 브라우저에서 https://ip.pe.kr

---

## 1단계: DNS 설정

도메인 관리 업체(가비아·후이즈·닷홈 등) 관리 페이지에서:

| 타입 | 호스트명 | 값 |
|:---:|:---:|:---:|
| A | `retired` | 집 공인 IP |

설정 후 전파까지 수 분~수십 분 소요됩니다.

---

## 2단계: 공유기 포트포워딩 설정

공유기 관리 페이지 (보통 192.168.0.1 또는 192.168.1.1) 접속 후:

| 외부 포트 | 내부 IP | 내부 포트 | 처리 |
|:---:|:---:|:---:|:---:|
| 80 | 이 PC의 내부 IP | 80 | ✅ 추가 |
| 443 | 이 PC의 내부 IP | 443 | ✅ 추가 |
| 8501 | — | — | ❌ 삭제/차단 |
| 9080 | — | — | ❌ 삭제/차단 |

> 이 PC 내부 IP 확인: `ipconfig` → IPv4 주소 (예: 192.168.0.10)

---

## 3단계: Caddy 다운로드

1. https://caddyserver.com/download 접속
2. **Windows** / **amd64** 선택 → 다운로드
3. `caddy.exe`를 프로젝트 폴더에 복사:
   ```
   c:\Users\jason004\retirement_app\caddy.exe
   ```

---

## 4단계: Windows 방화벽 설정

PowerShell을 **관리자 권한**으로 실행 후:

```powershell
# 80, 443 허용 (Caddy)
netsh advfirewall firewall add rule name="Caddy HTTP"  dir=in action=allow protocol=tcp localport=80
netsh advfirewall firewall add rule name="Caddy HTTPS" dir=in action=allow protocol=tcp localport=443

# 8501, 9080 외부 접근 차단 (로컬네트워크 제외)
netsh advfirewall firewall add rule name="Block Streamlit" dir=in action=block protocol=tcp localport=8501 remoteip=!LocalSubnet
netsh advfirewall firewall add rule name="Block FastAPI"   dir=in action=block protocol=tcp localport=9080 remoteip=!LocalSubnet
```

---

## 5단계: logs 폴더 생성

```powershell
mkdir c:\Users\jason004\retirement_app\logs
```

---

## 6단계: 앱 실행

PowerShell에서:

```powershell
cd c:\Users\jason004\retirement_app
python start_servers.py
```

백엔드(9080)와 Streamlit(8501)이 **127.0.0.1**에만 바인딩되어 시작됩니다.

---

## 7단계: Caddy 실행 (관리자 권한 PowerShell)

```powershell
cd c:\Users\jason004\retirement_app
.\caddy.exe run
```

- 처음 실행 시 Windows 방화벽 허용 팝업 → **허용** 클릭
- Caddy가 Let's Encrypt에서 `kairang.pe.kr` 인증서를 자동 발급 (1~2분)
- 터미널에 `certificate obtained successfully` 메시지 확인

---

## 8단계: 접속 확인

| 주소 | 결과 |
|---|---|
| https://kairang.pe.kr | ✅ 자물쇠(HTTPS) + Streamlit 앱 |
| http://kairang.pe.kr | ✅ 자동으로 HTTPS 리다이렉트 |
| http://kairang.pe.kr:8501 | ❌ 연결 안 됨 (차단 확인) |

---

## Caddy 부팅 시 자동 시작 (선택)

```powershell
# 관리자 권한 PowerShell
cd c:\Users\jason004\retirement_app
.\caddy.exe service install
.\caddy.exe service start
```

Windows 서비스로 등록되어 PC 재부팅 후에도 자동 실행됩니다.

---

## 접근 로그 확인

```powershell
Get-Content c:\Users\jason004\retirement_app\logs\access.log -Tail 50 -Wait
```

---

## 집 IP가 바뀔 때 (DDNS 미사용 시)

통신사 회선은 공인 IP가 변경될 수 있습니다.
IP가 바뀌면 도메인 관리 업체에서 A 레코드를 새 IP로 수정해야 합니다.

자동화하려면 **Cloudflare**로 DNS를 이전 후 아래 스크립트를 작업 스케줄러에 등록:

```powershell
# update_dns.ps1 — 매 시간 실행하여 IP 변경 시 Cloudflare에 자동 업데이트
$CF_TOKEN  = "Cloudflare API 토큰"
$ZONE_ID   = "Zone ID"
$RECORD_ID = "A 레코드 ID"
$DOMAIN    = "kairang.pe.kr"

$current_ip = (Invoke-RestMethod "https://ip.pe.kr/json").ip
$headers = @{ Authorization = "Bearer $CF_TOKEN"; "Content-Type" = "application/json" }
$body = @{ type="A"; name=$DOMAIN; content=$current_ip; ttl=120 } | ConvertTo-Json
Invoke-RestMethod "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" `
    -Method PUT -Headers $headers -Body $body
```

---

## 현재 설정 파일 위치

| 파일 | 역할 |
|---|---|
| `Caddyfile` | Caddy 리버스프록시 설정 |
| `.streamlit/config.toml` | Streamlit 서버 바인딩 설정 |
| `.env` | ALLOWED_ORIGINS, STREAMLIT_URL |
| `start_servers.py` | 앱 시작 (127.0.0.1 바인딩) |
