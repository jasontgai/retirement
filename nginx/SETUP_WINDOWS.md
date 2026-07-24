# Windows 보안 설정 가이드 (Caddy + 방화벽)

> Linux 서버용 nginx 설정(SETUP.md)은 이 PC에 맞지 않습니다.
> Windows에서는 **Caddy**가 가장 간단합니다.

## Caddy란?
- exe 파일 하나 — 설치 불필요
- HTTPS 인증서를 Let's Encrypt에서 자동 발급·갱신
- Streamlit WebSocket 자동 지원
- Nginx보다 설정이 훨씬 단순

---

## 1단계: 공유기 포트포워딩 확인
공유기 설정에서:
- 외부 80 → 이 PC의 내부 IP:80
- 외부 443 → 이 PC의 내부 IP:443
- 외부 8501 포트포워딩 **삭제** (직접 노출 차단)
- 외부 9080 포트포워딩 **삭제** (직접 노출 차단)

> 내부 IP 확인: `ipconfig`에서 192.168.x.x

---

## 2단계: Windows 방화벽 설정
PowerShell을 **관리자 권한**으로 실행:

```powershell
# 80, 443 허용 (Caddy)
netsh advfirewall firewall add rule name="Caddy HTTP" dir=in action=allow protocol=tcp localport=80
netsh advfirewall firewall add rule name="Caddy HTTPS" dir=in action=allow protocol=tcp localport=443

# 8501, 9080 외부 접근 차단 (이미 127.0.0.1 바인딩이지만 이중 보호)
netsh advfirewall firewall add rule name="Block Streamlit External" dir=in action=block protocol=tcp localport=8501 remoteip=!LocalSubnet
netsh advfirewall firewall add rule name="Block FastAPI External" dir=in action=block protocol=tcp localport=9080 remoteip=!LocalSubnet
```

---

## 3단계: Caddy 다운로드

1. https://caddyserver.com/download 에서 **Windows amd64** 선택
2. `caddy.exe`를 프로젝트 폴더 `c:\Users\jason004\retirement_app\` 에 복사

---

## 4단계: 로그 폴더 생성
```powershell
mkdir c:\Users\jason004\retirement_app\logs
```

---

## 5단계: 앱 먼저 실행
```powershell
cd c:\Users\jason004\retirement_app
python start_servers.py
```

---

## 6단계: Caddy 실행 (관리자 권한 PowerShell)
```powershell
cd c:\Users\jason004\retirement_app
.\caddy.exe run
```

처음 실행 시 Windows 방화벽 허용 팝업 → **허용**을 클릭하세요.
Let's Encrypt에서 자동으로 SSL 인증서를 발급받습니다 (1~2분 소요).

---

## 7단계: 확인
- https://kairang.pe.kr 접속 → 자물쇠(HTTPS) + Streamlit 앱 표시
- http://kairang.pe.kr:8501 → 연결 안 됨 (차단 확인)

---

## Caddy 자동 시작 (부팅 시 자동 실행)
```powershell
# 서비스로 등록 (관리자 권한)
cd c:\Users\jason004\retirement_app
.\caddy.exe service install
.\caddy.exe service start
```
이후 PC 재부팅 후에도 Caddy가 자동으로 시작됩니다.

---

## 접근 로그 확인
```powershell
Get-Content c:\Users\jason004\retirement_app\logs\access.log -Tail 50
```
누가, 언제, 어떤 경로로 접속했는지 확인할 수 있습니다.
