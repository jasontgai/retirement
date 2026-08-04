"""서버 시작 스크립트 - restart.bat에서 호출"""
import subprocess, time, os, urllib.request, sys, socket

APPDIR = os.path.dirname(os.path.abspath(__file__))
PYTHON  = os.path.join(APPDIR, r'.venv\Scripts\python.exe')
CADDY   = os.path.join(APPDIR, 'caddy.exe')
LOGDIR  = os.path.join(APPDIR, 'logs')
BACKEND_PORT  = 9080
FRONTEND_PORT = 8501

os.makedirs(LOGDIR, exist_ok=True)

NO_WINDOW = subprocess.CREATE_NO_WINDOW


def kill_port(port):
    r = subprocess.run(
        f'netstat -ano | findstr ":{port}"',
        shell=True, capture_output=True, text=True, encoding='cp949', errors='ignore'
    )
    for line in r.stdout.splitlines():
        if 'LISTENING' in line:
            pid = line.strip().split()[-1]
            if pid.isdigit():
                subprocess.run(['taskkill.exe', '/F', '/PID', pid], capture_output=True)

def wait_port_free(port, timeout=15):
    """포트가 완전히 해제될 때까지 대기"""
    for _ in range(timeout):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('127.0.0.1', port))
            s.close()
            return True
        except OSError:
            time.sleep(1)
    return False


def wait_for_port(port, timeout=30):
    for _ in range(timeout):
        try:
            urllib.request.urlopen(f'http://localhost:{port}', timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False


print('=' * 50)
print('  은퇴설계 서버 시작')
print('=' * 50)

# 1. 기존 프로세스 정리
print('\n[1/4] 기존 서버 종료 중...')
kill_port(BACKEND_PORT)
kill_port(FRONTEND_PORT)
kill_port(8443)
subprocess.run(['taskkill.exe', '/F', '/IM', 'caddy.exe'], capture_output=True)
print('      포트 해제 대기 중...', end='', flush=True)
for p in [BACKEND_PORT, FRONTEND_PORT]:
    wait_port_free(p)
print(' OK')
time.sleep(1)

# 2. 백엔드 시작 (백그라운드, 로그 파일)
print(f'[2/4] 백엔드 시작 (port {BACKEND_PORT})...')
be_log = open(os.path.join(LOGDIR, 'backend.log'), 'a', encoding='utf-8')
be = subprocess.Popen(
    [PYTHON, '-m', 'uvicorn', 'backend.api:app',
     '--host', '127.0.0.1', '--port', str(BACKEND_PORT)],
    cwd=APPDIR,
    stdout=be_log, stderr=be_log,
    creationflags=NO_WINDOW,
)
print(f'      PID: {be.pid}')

print('      백엔드 응답 대기 중', end='', flush=True)
for i in range(20):
    try:
        urllib.request.urlopen(f'http://localhost:{BACKEND_PORT}/health', timeout=1)
        print(' OK')
        break
    except Exception:
        print('.', end='', flush=True)
        time.sleep(1)
else:
    print('\n[오류] 백엔드 응답 없음. logs/backend.log 확인하세요.')
    sys.exit(1)

# 3. 프론트엔드 시작 (백그라운드, 로그 파일)
print(f'[3/4] 프론트엔드 시작 (port {FRONTEND_PORT})...')
fe_log = open(os.path.join(LOGDIR, 'frontend.log'), 'a', encoding='utf-8')
fe = subprocess.Popen(
    [PYTHON, '-m', 'streamlit', 'run', 'frontend/app.py',
     '--server.port', str(FRONTEND_PORT),
     '--server.headless', 'true'],
    cwd=APPDIR,
    stdout=fe_log, stderr=fe_log,
    creationflags=NO_WINDOW,
)
print(f'      PID: {fe.pid}')

print('      프론트엔드 응답 대기 중', end='', flush=True)
for i in range(30):
    try:
        urllib.request.urlopen(f'http://localhost:{FRONTEND_PORT}', timeout=1)
        print(' OK')
        break
    except Exception:
        print('.', end='', flush=True)
        time.sleep(1)
else:
    print('\n[경고] 프론트엔드 응답 없음 (아직 초기화 중일 수 있음)')

# 4. Caddy 시작 (백그라운드, 로그 파일)
print(f'[4/4] Caddy 시작 (HTTPS :8443)...')
if os.path.exists(CADDY):
    caddy_log = open(os.path.join(LOGDIR, 'caddy.log'), 'a', encoding='utf-8')
    subprocess.Popen(
        [CADDY, 'run', '--config', 'Caddyfile'],
        cwd=APPDIR,
        stdout=caddy_log, stderr=caddy_log,
        creationflags=NO_WINDOW,
        env=os.environ.copy(),
    )
    print('      Caddy 시작됨')
else:
    print('      [경고] caddy.exe 없음 — HTTPS 비활성')

print()
print('=' * 50)
print(f'  Frontend : http://localhost:{FRONTEND_PORT}')
print(f'  Backend  : http://localhost:{BACKEND_PORT}')
print(f'  외부접속 : https://kairang.pe.kr:8443')
print()
print('  로그 위치:')
print(f'    백엔드  : logs/backend.log')
print(f'    프론트  : logs/frontend.log')
print(f'    접속기록: logs/access.log')
print('=' * 50)
