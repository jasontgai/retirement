"""서버 시작 스크립트 - restart.bat에서 호출"""
import subprocess, time, os, urllib.request, sys

APPDIR = os.path.dirname(os.path.abspath(__file__))
PYTHON  = os.path.join(APPDIR, r'.venv\Scripts\python.exe')
BACKEND_PORT = 9080
FRONTEND_PORT = 8501


def kill_port(port):
    r = subprocess.run(
        f'netstat -ano | findstr ":{port} "',
        shell=True, capture_output=True, text=True, encoding='cp949', errors='ignore'
    )
    for line in r.stdout.splitlines():
        if 'LISTENING' in line:
            pid = line.strip().split()[-1]
            if pid.isdigit():
                subprocess.run(['taskkill.exe', '/F', '/PID', pid], capture_output=True)


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
print('\n[1/3] 기존 서버 종료 중...')
kill_port(BACKEND_PORT)
kill_port(FRONTEND_PORT)
time.sleep(2)

# 2. 백엔드 시작 (새 콘솔 창)
print(f'[2/3] 백엔드 시작 (port {BACKEND_PORT})...')
be = subprocess.Popen(
    [PYTHON, '-m', 'uvicorn', 'backend.api:app',
     '--host', '0.0.0.0', '--port', str(BACKEND_PORT), '--reload'],
    cwd=APPDIR,
    creationflags=subprocess.CREATE_NEW_CONSOLE,
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
    print('\n[오류] 백엔드가 응답하지 않습니다. 백엔드 창에서 오류를 확인하세요.')
    sys.exit(1)

# 3. 프론트엔드 시작 (새 콘솔 창)
print(f'[3/3] 프론트엔드 시작 (port {FRONTEND_PORT})...')
fe = subprocess.Popen(
    [PYTHON, '-m', 'streamlit', 'run', 'frontend/app.py',
     '--server.port', str(FRONTEND_PORT),
     '--server.headless', 'true'],
    cwd=APPDIR,
    creationflags=subprocess.CREATE_NEW_CONSOLE,
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

print()
print('=' * 50)
print(f'  Frontend : http://localhost:{FRONTEND_PORT}')
print(f'  Backend  : http://localhost:{BACKEND_PORT}/docs')
print('=' * 50)
