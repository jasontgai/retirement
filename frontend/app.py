"""
은퇴설계 Streamlit 어플 (모바일 친화)
- 실행: streamlit run frontend/app.py
"""
import streamlit as st
import requests
import json
import math
import base64
import pandas as pd
import altair as alt
import logging as _logging
import os as _os
from datetime import date as _date, datetime as _datetime, timedelta as _timedelta
from urllib.parse import unquote

_LOG_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'frontend_debug.log')
_logging.basicConfig(
    filename=_LOG_PATH, level=_logging.DEBUG,
    format='%(asctime)s %(message)s', datefmt='%H:%M:%S',
    encoding='utf-8',
)
_log = _logging.getLogger('ret')

# ============================================================
# 설정
# ============================================================
try:
    API_BASE = st.secrets.get("API_BASE", "http://localhost:9080")
except Exception:
    try:
        from dotenv import load_dotenv as _lde
        import os as _os
        _lde(dotenv_path=_os.path.join(_os.path.dirname(_os.path.dirname(__file__)), '.env'), override=True)
        API_BASE = _os.getenv("BACKEND_URL", "http://localhost:9080")
    except Exception:
        API_BASE = "http://localhost:9080"

st.set_page_config(
    page_title="은퇴설계",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)
# ============================================================
# 공통 CSS
# ============================================================
st.markdown(f"""<style>
@font-face {{
    font-family: 'Material Icons';
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: url('{API_BASE}/static/fonts/material-icons.woff2') format('woff2');
}}
.material-icons {{
    font-family: 'Material Icons';
    font-weight: normal;
    font-style: normal;
    font-size: 24px;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    word-wrap: normal;
    direction: ltr;
    font-feature-settings: 'liga';
    -webkit-font-feature-settings: 'liga';
    -webkit-font-smoothing: antialiased;
}}
</style>""", unsafe_allow_html=True)

st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', 'Pretendard', sans-serif;
    }
    .stButton > button {
        width: 100%;
        height: 48px;
        border-radius: 24px;
        font-size: 16px;
        font-weight: 600;
        background-color: #1976d2;
        color: white;
        border: none;
    }
    .stButton > button:hover { background-color: #1565c0; }
    .stNumberInput input, .stTextInput input, .stSelectbox > div {
        border-radius: 12px !important;
        font-size: 16px !important;
    }
    div[data-testid="stExpander"] {
        border-radius: 16px;
        border: 1px solid rgba(128,128,128,0.2);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 480px;
    }
    div[data-testid="stMetric"] {
        background: rgba(25,118,210,0.1);
        padding: 16px;
        border-radius: 16px;
        margin-bottom: 8px;
    }
    button[data-baseweb="tab"] {
        font-size: 14px !important;
        padding: 10px 12px !important;
    }
    /* 인증 카드 */
    .auth-card {
        border-radius: 20px;
        padding: 32px 24px;
        border: 1px solid rgba(128,128,128,0.15);
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-top: 16px;
    }
    /* 사용자 배지 */
    .user-badge {
        background: linear-gradient(135deg, #1976d2, #42a5f5);
        color: white;
        border-radius: 16px;
        padding: 12px 16px;
        margin-bottom: 16px;
        font-size: 14px;
    }
    /* 위험 버튼 */
    .danger-btn > button {
        background-color: #d32f2f !important;
    }
    .danger-btn > button:hover {
        background-color: #b71c1c !important;
    }
    /* 아웃라인 버튼 */
    .outline-btn > button {
        background-color: transparent !important;
        color: #1976d2 !important;
        border: 2px solid #1976d2 !important;
    }
    .outline-btn > button:hover {
        background-color: rgba(25,118,210,0.08) !important;
    }
    /* Material Icons ligature 강제 활성화 (Android 15 / One UI 7 대응) */
    .material-icons,
    .material-icons-outlined,
    [class*="material-icon"] {
        font-feature-settings: 'liga' 1 !important;
        -webkit-font-feature-settings: 'liga' 1 !important;
        font-variant-ligatures: normal !important;
        -webkit-font-variant-ligatures: normal !important;
        text-rendering: optimizeLegibility !important;
    }
    /* Android: 설정 모달 깨진 테마 아이콘 숨김 */
    div[role="dialog"] img,
    div[role="dialog"] svg image,
    [data-testid="stThemeColorPickerIcon"] {
        display: none !important;
    }
    /* Android: expander 펼치기/접기 SVG 아이콘 텍스트로 대체 */
    div[data-testid="stExpanderToggleIcon"] svg,
    [data-testid="stExpander"] summary svg {
        display: none !important;
    }
    div[data-testid="stExpanderToggleIcon"]::after {
        content: "+";
        font-size: 20px;
        font-weight: 700;
        color: #1976d2;
        line-height: 1;
    }
    details[open] div[data-testid="stExpanderToggleIcon"]::after {
        content: "-";
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 세션 상태 초기화
# ============================================================
def init_state():
    defaults = {
        # 인증
        'token': None,
        'user_id': None,
        'user_name': None,
        'user_email': None,
        'is_admin': False,
        # 페이지: 'main' | 'account'
        'page': 'main',
        # 자산 입력
        'pensions': [],
        'real_estates': [],
        'financial_assets': [],
        'memberships': [],
        'vehicles': [],
        'debts': [],
        'insurances': [],
        'analysis_result': None,
        'editing_pension_idx': None,
        'editing_re_idx': None,
        'editing_fa_idx': None,
        'editing_ms_idx': None,
        'editing_v_idx': None,
        'editing_d_idx': None,
        'editing_ins_idx': None,
        'adj_payout': {},
        'adj_start_age': {},
        'adj_return_rate': {},
        'adj_balance': {},
        'adj_monthly_contrib': {},
        'adj_nps_balance': None,
        'adj_nps_monthly': None,
        'profile_id': None,      # None=아직 로드 시도 안함, 0=프로필 없음, n=프로필ID
        # 기본 정보
        'inp_birth_year': 1971,
        'inp_birth_month': 5,
        'inp_birth_day': 15,
        'inp_gender': '남',
        'inp_retirement_age': 60,
        'inp_lifespan': 90,
        'inp_dependents': 1,
        # 소득 정보
        'inp_salary': 8000,
        'inp_bonus': 0,
        'inp_is_employee': True,
        'inp_parttime_monthly': 0,
        'inp_parttime_until': 70,
        'inp_spouse_nps': 0,
        'inp_spouse_nps_age': 65,
        'inp_spouse_other': 0,
        'inp_spouse_other_age': 65,
        # 지출 정보
        'inp_living': 250,
        'inp_medical': 50,
        'inp_leisure': 80,
        'inp_family': 30,
        'inp_insurance': 30,
        'inp_other': 20,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── 쿠키 기반 세션 유지 (st.context.cookies + st.html JS 방식) ──────────
_COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30일(초)

def _save_session_to_cookie(token, user_id, user_name, user_email):
    """다음 렌더에서 JavaScript로 쿠키 저장"""
    st.session_state['_pending_cookie'] = {
        'action': 'set',
        'token':  token,
        'uid':    str(user_id),
        'name':   user_name.replace('"', ''),
        'email':  user_email.replace('"', ''),
    }

def _clear_session_cookie():
    """다음 렌더에서 JavaScript로 쿠키 삭제"""
    st.session_state['_pending_cookie'] = {'action': 'delete'}

def _flush_cookie_js():
    """보류 중인 쿠키 작업을 JavaScript로 실행 (렌더 초반에 호출)"""
    _pc = st.session_state.pop('_pending_cookie', None)
    if _pc is None:
        return
    _log.debug(f"[flush_cookie] action={_pc['action']}")
    _ma = _COOKIE_MAX_AGE
    if _pc['action'] == 'set':
        _js = f"""<script>
var a={_ma};
document.cookie="ret_token={_pc['token']};max-age="+a+";path=/;SameSite=Lax";
document.cookie="ret_uid={_pc['uid']};max-age="+a+";path=/;SameSite=Lax";
document.cookie="ret_name={_pc['name']};max-age="+a+";path=/;SameSite=Lax";
document.cookie="ret_email={_pc['email']};max-age="+a+";path=/;SameSite=Lax";
</script>"""
    else:
        _js = """<script>
["ret_token","ret_uid","ret_name","ret_email"].forEach(function(n){
    document.cookie=n+"=;max-age=0;path=/;SameSite=Lax";
});
</script>"""
    _log.debug(f"[flush_cookie] st.html 호출 전")
    st.html(f'<span style="display:none">{_js}</span>', unsafe_allow_javascript=True)
    _log.debug(f"[flush_cookie] st.html 호출 후")

# 보류 중인 쿠키 JS 실행 (로그인/로그아웃 직후 rerun 시 쿠키 기록)
_flush_cookie_js()

# 새로고침 후 쿠키에서 세션 복원 (st.context.cookies = HTTP 요청 헤더에서 직접 읽음)
_log.debug(f"[render] token={bool(st.session_state.token)} invalidated={st.session_state.get('session_invalidated')}")
if not st.session_state.token and not st.session_state.get('session_invalidated'):
    _ck = st.context.cookies
    _ck_token = _ck.get('ret_token')
    _log.debug(f"[cookie] ret_token={'있음' if _ck_token else '없음'}")
    if _ck_token:
        _ck_uid   = _ck.get('ret_uid', '0')
        _ck_name  = _ck.get('ret_name', '')
        _ck_email = _ck.get('ret_email', '')
        _revoked = False
        try:
            _verify_resp = requests.get(
                f"{API_BASE}/auth/me",
                headers={"Authorization": f"Bearer {_ck_token}"},
                timeout=5,
            )
            _log.debug(f"[auth/me] status={_verify_resp.status_code}")
            if _verify_resp.status_code in (401, 403):
                _revoked = True
            elif _verify_resp.status_code == 200:
                _me = _verify_resp.json()
                st.session_state.user_id    = _me.get('id') or int(_ck_uid or 0)
                st.session_state.user_name  = _me.get('name') or _ck_name or ''
                st.session_state.user_email = _me.get('email') or _ck_email or ''
                st.session_state.is_admin   = bool(_me.get('is_admin', False))
        except Exception as _e:
            _log.debug(f"[auth/me] 예외={_e}")
        if _revoked:
            _log.debug("[cookie] 토큰 만료 → 쿠키 삭제")
            _clear_session_cookie()
            st.session_state.session_invalidated = True
        else:
            st.session_state.token = _ck_token
            if not st.session_state.user_id:
                st.session_state.user_id    = int(_ck_uid or 0)
                st.session_state.user_name  = _ck_name or ''
                st.session_state.user_email = _ck_email or ''
            st.rerun()

# OAuth 콜백 처리 (소셜 로그인 완료 후 리다이렉트)
_qp = st.query_params
_log.debug(f"[qp] {dict(_qp)}")
if "token" in _qp and not st.session_state.token:
    st.session_state.token      = _qp["token"]
    st.session_state.user_id    = int(_qp.get("user_id", 0))
    st.session_state.user_name  = unquote(_qp.get("name", ""))
    st.session_state.user_email = unquote(_qp.get("email", ""))
    st.session_state.is_admin   = bool(int(_qp.get("is_admin", 0)))
    _save_session_to_cookie(st.session_state.token, st.session_state.user_id,
                            st.session_state.user_name, st.session_state.user_email)
    st.query_params.clear()
    st.rerun()
elif "oauth_error" in _qp:
    _err = unquote(_qp["oauth_error"])
    _log.debug(f"[oauth_error] {_err}")
    if "준비 중" in _err:
        st.info(f"ℹ️ {_err}")
    else:
        st.error(f"소셜 로그인 실패: {_err}")
    st.query_params.clear()


# ============================================================
# API 헬퍼
# ============================================================
def call_api(endpoint, payload=None, method="POST", form=False):
    url = f"{API_BASE}{endpoint}"
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, json=payload, headers=headers, timeout=30)
        elif method == "PUT":
            resp = requests.put(url, json=payload, headers=headers, timeout=30)
        elif form:
            resp = requests.post(url, data=payload, headers=headers, timeout=30)
        else:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        if resp.status_code == 204:
            return {}, None
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, f"서버 연결 실패. 백엔드가 켜져있는지 확인하세요. ({API_BASE})"
    except requests.exceptions.HTTPError:
        if resp.status_code == 401 and st.session_state.get('token') and '/auth/login' not in url:
            # 인증된 상태에서 토큰 만료/무효 → 세션 초기화 후 로그인 화면으로
            st.session_state.token = None
            st.session_state.session_invalidated = True
            _clear_session_cookie()
            st.rerun()
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return None, f"오류 {resp.status_code}: {detail}"
    except Exception as e:
        return None, f"오류: {str(e)}"


def _restore_from_profile(p: dict):
    """DB에서 불러온 프로필을 session_state에 복원"""
    pers = p.get('personal', {})
    inc  = p.get('current_income', {})
    exp  = p.get('expected_expense', {})

    st.session_state.inp_name            = pers.get('name', '')
    st.session_state.inp_birth_year      = pers.get('birth_year', 1971)
    st.session_state.inp_birth_month     = pers.get('birth_month', 5)
    st.session_state.inp_birth_day       = pers.get('birth_day', 15)
    st.session_state.inp_gender          = pers.get('gender', '남')
    st.session_state.inp_retirement_age  = pers.get('retirement_age', 60)
    st.session_state.inp_lifespan        = pers.get('expected_lifespan', 90)
    st.session_state.inp_dependents      = pers.get('dependents', 1)

    st.session_state.inp_salary          = inc.get('annual_salary', 80_000_000) // 10000
    st.session_state.inp_bonus           = inc.get('annual_bonus', 0) // 10000
    st.session_state.inp_is_employee     = inc.get('is_employee', True)
    st.session_state.inp_parttime_monthly = inc.get('parttime_monthly', 0) // 10000
    st.session_state.inp_parttime_until   = inc.get('parttime_until_age', 70)
    st.session_state.inp_spouse_nps      = pers.get('spouse_nps_monthly', 0) // 10000
    st.session_state.inp_spouse_nps_age  = pers.get('spouse_nps_start_age', 65)
    st.session_state.inp_spouse_other    = pers.get('spouse_other_monthly', 0) // 10000
    st.session_state.inp_spouse_other_age = pers.get('spouse_other_start_age', 65)

    st.session_state.inp_living          = exp.get('living_cost', 2_500_000) // 10000
    st.session_state.inp_medical         = exp.get('medical_cost', 500_000) // 10000
    st.session_state.inp_leisure         = exp.get('leisure_cost', 800_000) // 10000
    st.session_state.inp_family          = exp.get('family_support', 0) // 10000
    st.session_state.inp_insurance       = exp.get('insurance_premium', 300_000) // 10000
    st.session_state.inp_other           = exp.get('other', 200_000) // 10000

    st.session_state.pensions            = p.get('pensions', [])
    st.session_state.real_estates        = p.get('real_estates', [])
    st.session_state.financial_assets    = p.get('financial_assets', [])
    st.session_state.memberships         = p.get('memberships', [])
    st.session_state.vehicles            = p.get('vehicles', [])
    st.session_state.debts               = p.get('debts', [])
    st.session_state.insurances          = p.get('insurances', [])

    st.session_state.profile_id          = p.get('id', 0)


def fmt_won(amount):
    if amount is None:
        return "-"
    amount = int(amount)
    sign = "-" if amount < 0 else ""
    abs_amt = abs(amount)
    if abs_amt >= 100_000_000:
        eok = abs_amt // 100_000_000
        man = (abs_amt % 100_000_000) // 10_000
        if man:
            return f"{sign}{eok}억 {man:,}만원"
        return f"{sign}{eok}억원"
    elif abs_amt >= 10_000:
        return f"{sign}{abs_amt // 10_000:,}만원"
    else:
        return f"{sign}{abs_amt:,}원"


def _sl(label, mn, mx, val, step=1, key=None, fmt=""):
    """Slider (left 75%) + title/value (right 25%). fmt='won' expects 만원 units."""
    c1, c2 = st.columns([3, 1])
    with c1:
        # key가 이미 session_state에 있으면 value= 생략 (중복 설정 경고 방지)
        if key and key in st.session_state:
            v = st.slider(label, min_value=mn, max_value=mx,
                          step=step, key=key, label_visibility="collapsed")
        else:
            v = st.slider(label, min_value=mn, max_value=mx, value=val,
                          step=step, key=key, label_visibility="collapsed")
    with c2:
        if fmt == "won":
            disp = fmt_won(v * 10000)
        elif fmt:
            disp = f"{v}{fmt}"
        else:
            disp = str(v)
        st.caption(label)
        st.markdown(f"**{disp}**")
    return v


# ============================================================
# 인증 화면
# ============================================================
def _social_btn(label: str, url: str, bg: str, color: str = "white") -> str:
    return (
        f'<a href="{url}" target="_self" style="'
        f'display:block;text-align:center;text-decoration:none;'
        f'background:{bg};color:{color};font-size:15px;font-weight:600;'
        f'padding:13px 0;border-radius:24px;margin-bottom:8px;">'
        f'{label}</a>'
    )


def show_auth_screen():
    st.markdown("## 💰 은퇴설계")
    st.caption("연금·세금·건보료 종합 시뮬레이션")
    st.divider()

    # 소셜 로그인 (준비 중)
    # st.markdown("#### 소셜 계정으로 시작하기")
    # st.markdown(
    #     _social_btn("🟡  카카오로 시작하기",    f"{API_BASE}/auth/oauth/kakao",  "#FEE500", "#191919") +
    #     _social_btn("🟢  네이버로 시작하기",    f"{API_BASE}/auth/oauth/naver",  "#03C75A") +
    #     _social_btn("🔵  구글로 시작하기",      f"{API_BASE}/auth/oauth/google", "#4285F4"),
    #     unsafe_allow_html=True,
    # )
    # st.markdown("<p style='text-align:center;color:#999;font-size:13px;margin:12px 0'>또는 이메일로 로그인</p>",
    #             unsafe_allow_html=True)

    tab_login, tab_register, tab_reset = st.tabs(["🔑 로그인", "📝 회원가입", "🔓 비밀번호 찾기"])

    # --- 로그인 ---
    with tab_login:
        st.subheader("로그인")
        login_email    = st.text_input("이메일", placeholder="example@email.com", key="login_email")
        login_password = st.text_input("비밀번호", type="password", key="login_pw")
        login_submitted = st.button("로그인", width='stretch', key="btn_login")

        if login_submitted:
            if not login_email or not login_password:
                st.error("이메일과 비밀번호를 입력하세요.")
            else:
                login_result, login_err = call_api("/auth/login", {
                    "username": login_email,
                    "password": login_password,
                }, method="POST", form=True)
                if login_err:
                    msg = login_err.replace("오류: ", "", 1)
                    st.error(msg)
                else:
                    st.session_state.token      = login_result["access_token"]
                    st.session_state.user_id    = login_result["user_id"]
                    st.session_state.user_name  = login_result["name"]
                    st.session_state.user_email = login_email
                    st.session_state.is_admin   = bool(login_result.get("is_admin", False))
                    st.session_state.pop('session_invalidated', None)
                    _save_session_to_cookie(login_result["access_token"], login_result["user_id"],
                                            login_result["name"], login_email)
                    st.rerun()

    # --- 회원가입 ---
    with tab_register:
        st.subheader("회원가입")
        r_name  = st.text_input("이름", placeholder="홍길동", key="r_name")
        r_age   = st.number_input("현재 나이", min_value=20, max_value=75,
                                  value=45, step=1, key="r_age",
                                  help="나이에 맞는 대한민국 평균 데이터로 시뮬레이션을 시작합니다")
        r_email = st.text_input("이메일", placeholder="example@email.com", key="r_email")
        r_pw    = st.text_input("비밀번호 (6자 이상)", type="password", key="r_pw")
        r_pw2   = st.text_input("비밀번호 확인", type="password", key="r_pw2")
        reg_submitted = st.button("회원가입", width='stretch', key="btn_register")

        if reg_submitted:
            if not all([r_name, r_email, r_pw, r_pw2]):
                st.error("모든 항목을 입력하세요.")
            elif len(r_pw) < 6:
                st.error("비밀번호는 6자 이상이어야 합니다.")
            elif r_pw != r_pw2:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                reg_result, reg_err = call_api("/auth/register", {
                    "email": r_email,
                    "password": r_pw,
                    "name": r_name,
                })
                if reg_err:
                    st.error(reg_err)
                else:
                    st.session_state.token      = reg_result["access_token"]
                    st.session_state.user_id    = reg_result["user_id"]
                    st.session_state.user_name  = reg_result["name"]
                    st.session_state.user_email = r_email
                    st.session_state.profile_id  = 0
                    st.session_state.pop('session_invalidated', None)
                    st.session_state.pop('is_new_user', None)
                    # 입력 나이에 가장 가까운 연령대 평균으로 즉시 분석
                    _apply_national_avg(int(r_age))
                    st.session_state._reg_age         = int(r_age)
                    st.session_state.onboarding_done  = True
                    st.session_state.analysis_result  = None
                    st.session_state.inp_name = reg_result["name"]
                    _save_session_to_cookie(reg_result["access_token"], reg_result["user_id"],
                                            reg_result["name"], r_email)
                    st.rerun()

    # --- 비밀번호 찾기 ---
    with tab_reset:
        st.subheader("비밀번호 찾기")

        # 단계 관리: 'request' → 'confirm'
        if 'pw_reset_step' not in st.session_state:
            st.session_state.pw_reset_step = 'request'

        if st.session_state.pw_reset_step == 'request':
            st.caption("가입하신 이메일 주소를 입력하면 6자리 인증번호를 발송합니다.")
            reset_email = st.text_input("이메일", placeholder="example@email.com", key="reset_email_input")
            sent = st.button("인증번호 발송", width='stretch', key="btn_reset_send")
            if sent:
                if not reset_email:
                    st.error("이메일을 입력하세요.")
                else:
                    _, req_err = call_api("/auth/password-reset/request",
                                         {"email": reset_email})
                    if req_err:
                        st.error(f"오류: {req_err}")
                    else:
                        st.session_state.pw_reset_email = reset_email
                        st.session_state.pw_reset_step  = 'confirm'
                        st.rerun()

        else:
            _rst_email = st.session_state.get('pw_reset_email', '')
            st.info(f"📧 **{_rst_email}** 으로 발송된 6자리 인증번호를 입력하세요. (유효시간 15분)")
            rst_code  = st.text_input("인증번호 (6자리)", placeholder="123456",
                                      max_chars=6, key="rst_code_input")
            rst_pw1   = st.text_input("새 비밀번호 (6자 이상)", type="password", key="rst_pw1")
            rst_pw2   = st.text_input("새 비밀번호 확인",       type="password", key="rst_pw2")
            confirmed = st.button("비밀번호 변경", width='stretch', type="primary", key="btn_confirm_reset")

            if confirmed:
                if not rst_code or not rst_pw1 or not rst_pw2:
                    st.error("모든 항목을 입력하세요.")
                elif len(rst_pw1) < 6:
                    st.error("비밀번호는 6자 이상이어야 합니다.")
                elif rst_pw1 != rst_pw2:
                    st.error("비밀번호가 일치하지 않습니다.")
                else:
                    _, conf_err = call_api("/auth/password-reset/confirm", {
                        "email":        _rst_email,
                        "code":         rst_code,
                        "new_password": rst_pw1,
                    })
                    if conf_err:
                        st.error(conf_err)
                    else:
                        st.success("✅ 비밀번호가 변경되었습니다! 로그인 탭에서 새 비밀번호로 로그인하세요.")
                        st.session_state.pw_reset_step = 'request'

            if st.button("← 이메일 다시 입력", key="rst_back"):
                st.session_state.pw_reset_step = 'request'
                st.rerun()


# ============================================================
# 연령대별 2026 대한민국 평균 데이터 (통계청·국민연금공단 기준)
# ============================================================
# annual_return_rate: 소수형 (0.04 = 4%)
# balance/payout: 원 단위  /  salary/expense: 만원 단위
_AGE_AVG_DATA = {
    40: {
        'retirement_age': 60, 'lifespan': 85, 'dependents': 2, 'inflation': 2.5,
        'salary': 5500, 'bonus': 0, 'is_employee': True,
        'parttime_monthly': 0, 'parttime_until': 70,
        'living': 340, 'medical': 30, 'leisure': 100, 'family': 60, 'insurance': 30, 'other': 30,
        'pensions': [
            {'pension_type': '국민연금', 'name': '국민연금',
             'current_balance': 0, 'monthly_contribution': 206_000,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 600_000, 'payout_period_years': 0,
             'annual_return_rate': 0.0, 'contribution_years': 0},
            {'pension_type': '퇴직연금DC', 'name': '퇴직연금DC',
             'current_balance': 30_000_000, 'monthly_contribution': 380_000,
             'contribution_end_age': 60, 'expected_start_age': 60,
             'expected_monthly_payout': 0, 'payout_period_years': 20,
             'annual_return_rate': 0.04, 'contribution_years': 0},
            {'pension_type': 'IRP', 'name': 'IRP',
             'current_balance': 5_000_000, 'monthly_contribution': 150_000,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 0, 'payout_period_years': 20,
             'annual_return_rate': 0.03, 'contribution_years': 0},
        ],
        'financial_assets': [
            {'name': '예적금·펀드', 'asset_type': '예적금',
             'amount': 80_000_000, 'annual_return_rate': 0.025, 'is_taxable': True}
        ],
        'debts': [
            {'name': '주택담보대출', 'debt_type': '주담대',
             'balance': 200_000_000, 'interest_rate': 0.035, 'monthly_payment': 900_000},
            {'name': '신용대출', 'debt_type': '신용대출',
             'balance': 30_000_000, 'interest_rate': 0.055, 'monthly_payment': 400_000},
        ],
    },
    45: {
        'retirement_age': 60, 'lifespan': 85, 'dependents': 2, 'inflation': 2.5,
        'salary': 6000, 'bonus': 0, 'is_employee': True,
        'parttime_monthly': 0, 'parttime_until': 70,
        'living': 310, 'medical': 35, 'leisure': 90, 'family': 55, 'insurance': 30, 'other': 25,
        'pensions': [
            {'pension_type': '국민연금', 'name': '국민연금',
             'current_balance': 0, 'monthly_contribution': 225_000,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 720_000, 'payout_period_years': 0,
             'annual_return_rate': 0.0, 'contribution_years': 0},
            {'pension_type': '퇴직연금DC', 'name': '퇴직연금DC',
             'current_balance': 50_000_000, 'monthly_contribution': 400_000,
             'contribution_end_age': 60, 'expected_start_age': 60,
             'expected_monthly_payout': 0, 'payout_period_years': 20,
             'annual_return_rate': 0.04, 'contribution_years': 0},
            {'pension_type': 'IRP', 'name': 'IRP',
             'current_balance': 15_000_000, 'monthly_contribution': 200_000,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 0, 'payout_period_years': 20,
             'annual_return_rate': 0.03, 'contribution_years': 0},
        ],
        'financial_assets': [
            {'name': '예적금·펀드', 'asset_type': '예적금',
             'amount': 120_000_000, 'annual_return_rate': 0.025, 'is_taxable': True}
        ],
        'debts': [
            {'name': '주택담보대출', 'debt_type': '주담대',
             'balance': 180_000_000, 'interest_rate': 0.035, 'monthly_payment': 800_000},
            {'name': '신용대출', 'debt_type': '신용대출',
             'balance': 25_000_000, 'interest_rate': 0.055, 'monthly_payment': 350_000},
        ],
    },
    50: {
        'retirement_age': 60, 'lifespan': 85, 'dependents': 1, 'inflation': 2.5,
        'salary': 5800, 'bonus': 0, 'is_employee': True,
        'parttime_monthly': 0, 'parttime_until': 70,
        'living': 290, 'medical': 40, 'leisure': 80, 'family': 50, 'insurance': 30, 'other': 25,
        'pensions': [
            {'pension_type': '국민연금', 'name': '국민연금',
             'current_balance': 0, 'monthly_contribution': 218_000,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 840_000, 'payout_period_years': 0,
             'annual_return_rate': 0.0, 'contribution_years': 0},
            {'pension_type': '퇴직연금DC', 'name': '퇴직연금DC',
             'current_balance': 70_000_000, 'monthly_contribution': 390_000,
             'contribution_end_age': 60, 'expected_start_age': 60,
             'expected_monthly_payout': 0, 'payout_period_years': 20,
             'annual_return_rate': 0.04, 'contribution_years': 0},
            {'pension_type': 'IRP', 'name': 'IRP',
             'current_balance': 20_000_000, 'monthly_contribution': 200_000,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 0, 'payout_period_years': 20,
             'annual_return_rate': 0.03, 'contribution_years': 0},
        ],
        'financial_assets': [
            {'name': '예적금·펀드', 'asset_type': '예적금',
             'amount': 150_000_000, 'annual_return_rate': 0.025, 'is_taxable': True}
        ],
        'debts': [
            {'name': '주택담보대출', 'debt_type': '주담대',
             'balance': 150_000_000, 'interest_rate': 0.035, 'monthly_payment': 700_000},
            {'name': '신용대출', 'debt_type': '신용대출',
             'balance': 20_000_000, 'interest_rate': 0.055, 'monthly_payment': 300_000},
        ],
    },
    55: {
        'retirement_age': 62, 'lifespan': 85, 'dependents': 1, 'inflation': 2.5,
        'salary': 5000, 'bonus': 0, 'is_employee': True,
        'parttime_monthly': 0, 'parttime_until': 70,
        'living': 270, 'medical': 50, 'leisure': 70, 'family': 40, 'insurance': 25, 'other': 20,
        'pensions': [
            {'pension_type': '국민연금', 'name': '국민연금',
             'current_balance': 0, 'monthly_contribution': 188_000,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 900_000, 'payout_period_years': 0,
             'annual_return_rate': 0.0, 'contribution_years': 0},
            {'pension_type': '퇴직연금DC', 'name': '퇴직연금DC',
             'current_balance': 80_000_000, 'monthly_contribution': 200_000,
             'contribution_end_age': 60, 'expected_start_age': 60,
             'expected_monthly_payout': 0, 'payout_period_years': 20,
             'annual_return_rate': 0.04, 'contribution_years': 0},
            {'pension_type': 'IRP', 'name': 'IRP',
             'current_balance': 20_000_000, 'monthly_contribution': 200_000,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 0, 'payout_period_years': 20,
             'annual_return_rate': 0.03, 'contribution_years': 0},
        ],
        'financial_assets': [
            {'name': '예적금·펀드', 'asset_type': '예적금',
             'amount': 150_000_000, 'annual_return_rate': 0.025, 'is_taxable': True}
        ],
        'debts': [
            {'name': '주택담보대출', 'debt_type': '주담대',
             'balance': 120_000_000, 'interest_rate': 0.035, 'monthly_payment': 650_000},
            {'name': '신용대출', 'debt_type': '신용대출',
             'balance': 15_000_000, 'interest_rate': 0.055, 'monthly_payment': 250_000},
        ],
    },
    60: {
        'retirement_age': 65, 'lifespan': 85, 'dependents': 1, 'inflation': 2.5,
        'salary': 2500, 'bonus': 0, 'is_employee': True,
        'parttime_monthly': 0, 'parttime_until': 70,
        'living': 250, 'medical': 70, 'leisure': 60, 'family': 30, 'insurance': 20, 'other': 20,
        'pensions': [
            {'pension_type': '국민연금', 'name': '국민연금',
             'current_balance': 0, 'monthly_contribution': 0,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 900_000, 'payout_period_years': 0,
             'annual_return_rate': 0.0, 'contribution_years': 0},
            {'pension_type': '퇴직연금DC', 'name': '퇴직연금DC',
             'current_balance': 90_000_000, 'monthly_contribution': 0,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 0, 'payout_period_years': 20,
             'annual_return_rate': 0.04, 'contribution_years': 0},
            {'pension_type': 'IRP', 'name': 'IRP',
             'current_balance': 15_000_000, 'monthly_contribution': 0,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 0, 'payout_period_years': 20,
             'annual_return_rate': 0.03, 'contribution_years': 0},
        ],
        'financial_assets': [
            {'name': '예적금·펀드', 'asset_type': '예적금',
             'amount': 130_000_000, 'annual_return_rate': 0.025, 'is_taxable': True}
        ],
        'debts': [
            {'name': '주택담보대출', 'debt_type': '주담대',
             'balance': 80_000_000, 'interest_rate': 0.035, 'monthly_payment': 500_000},
            {'name': '신용대출', 'debt_type': '신용대출',
             'balance': 10_000_000, 'interest_rate': 0.055, 'monthly_payment': 200_000},
        ],
    },
    65: {
        'retirement_age': 65, 'lifespan': 85, 'dependents': 0, 'inflation': 2.5,
        'salary': 0, 'bonus': 0, 'is_employee': False,
        'parttime_monthly': 0, 'parttime_until': 70,
        'living': 230, 'medical': 90, 'leisure': 50, 'family': 20, 'insurance': 15, 'other': 15,
        'pensions': [
            {'pension_type': '국민연금', 'name': '국민연금',
             'current_balance': 0, 'monthly_contribution': 0,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 900_000, 'payout_period_years': 0,
             'annual_return_rate': 0.0, 'contribution_years': 0},
            {'pension_type': '퇴직연금DC', 'name': '퇴직연금DC',
             'current_balance': 70_000_000, 'monthly_contribution': 0,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 0, 'payout_period_years': 20,
             'annual_return_rate': 0.04, 'contribution_years': 0},
            {'pension_type': 'IRP', 'name': 'IRP',
             'current_balance': 10_000_000, 'monthly_contribution': 0,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 0, 'payout_period_years': 20,
             'annual_return_rate': 0.03, 'contribution_years': 0},
        ],
        'financial_assets': [
            {'name': '예적금·펀드', 'asset_type': '예적금',
             'amount': 100_000_000, 'annual_return_rate': 0.025, 'is_taxable': True}
        ],
        'debts': [
            {'name': '주택담보대출', 'debt_type': '주담대',
             'balance': 40_000_000, 'interest_rate': 0.035, 'monthly_payment': 300_000},
        ],
    },
    70: {
        'retirement_age': 70, 'lifespan': 88, 'dependents': 0, 'inflation': 2.5,
        'salary': 0, 'bonus': 0, 'is_employee': False,
        'parttime_monthly': 0, 'parttime_until': 75,
        'living': 210, 'medical': 110, 'leisure': 40, 'family': 10, 'insurance': 10, 'other': 10,
        'pensions': [
            {'pension_type': '국민연금', 'name': '국민연금',
             'current_balance': 0, 'monthly_contribution': 0,
             'contribution_end_age': 60, 'expected_start_age': 65,
             'expected_monthly_payout': 950_000, 'payout_period_years': 0,
             'annual_return_rate': 0.0, 'contribution_years': 0},
            {'pension_type': '퇴직연금DC', 'name': '퇴직연금DC',
             'current_balance': 50_000_000, 'monthly_contribution': 0,
             'contribution_end_age': 60, 'expected_start_age': 70,
             'expected_monthly_payout': 0, 'payout_period_years': 15,
             'annual_return_rate': 0.04, 'contribution_years': 0},
        ],
        'financial_assets': [
            {'name': '예적금·펀드', 'asset_type': '예적금',
             'amount': 80_000_000, 'annual_return_rate': 0.02, 'is_taxable': True}
        ],
        'debts': [],
    },
}

_AGE_BRACKETS = sorted(_AGE_AVG_DATA.keys())


def _nearest_bracket(age: int) -> int:
    """가장 가까운 미래 연령대 구간 반환 (ceiling 방식)"""
    for b in _AGE_BRACKETS:
        if b >= age:
            return b
    return _AGE_BRACKETS[-1]


def _apply_national_avg(current_age: int):
    """연령에 맞는 2026 국가 평균 데이터를 session_state에 적용"""
    bracket = _nearest_bracket(current_age)
    avg = _AGE_AVG_DATA[bracket]
    ss = st.session_state
    _cur_year = __import__('datetime').date.today().year

    ss.inp_birth_year     = _cur_year - current_age
    ss.inp_birth_month    = 1
    ss.inp_birth_day      = 1
    ss.inp_gender         = '남'
    ss.inp_retirement_age = avg['retirement_age']
    ss.inp_lifespan       = avg['lifespan']
    ss.inp_dependents     = avg['dependents']
    ss.inp_salary         = avg['salary']
    ss.inp_bonus          = avg['bonus']
    ss.inp_is_employee    = avg['is_employee']
    ss.inp_parttime_monthly = avg['parttime_monthly']
    ss.inp_parttime_until   = avg['parttime_until']
    ss.inp_spouse_nps       = 0
    ss.inp_spouse_nps_age   = 65
    ss.inp_spouse_other     = 0
    ss.inp_spouse_other_age = 65
    ss.inp_living     = avg['living']
    ss.inp_medical    = avg['medical']
    ss.inp_leisure    = avg['leisure']
    ss.inp_family     = avg['family']
    ss.inp_insurance  = avg['insurance']
    ss.inp_other      = avg['other']
    ss.pensions          = [p.copy() for p in avg['pensions']]
    ss.financial_assets  = [a.copy() for a in avg['financial_assets']]
    ss.debts             = [d.copy() for d in avg['debts']]
    ss.real_estates      = []
    ss.memberships       = []
    ss.vehicles          = []
    ss.insurances        = []
    # 적용된 연령대 저장 (배너 표시용)
    ss._avg_bracket      = bracket


# ============================================================
# 회원정보 관리 페이지
# ============================================================
def show_account_page():
    # 상단 뒤로가기
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button("뒤로"):
            st.session_state.page = 'main'
            st.rerun()
    with col_title:
        st.subheader("회원정보 관리")

    st.divider()

    # 현재 계정 정보
    st.markdown(f"""
    <div class="user-badge">
        👤 &nbsp;<b>{st.session_state.user_name}</b><br>
        📧 &nbsp;{st.session_state.user_email}
    </div>
    """, unsafe_allow_html=True)

    # --- 이름 변경 ---
    with st.expander("✏️ 이름 변경", expanded=False):
        with st.form("update_name_form"):
            new_name = st.text_input("새 이름", value=st.session_state.user_name)
            cur_pw_name = st.text_input("현재 비밀번호 확인", type="password", key="cur_pw_name")
            if st.form_submit_button("이름 변경", width='stretch'):
                if not new_name or not cur_pw_name:
                    st.error("모든 항목을 입력하세요.")
                else:
                    result, err = call_api("/auth/me", {
                        "current_password": cur_pw_name,
                        "new_name": new_name,
                    }, method="PUT")
                    if err:
                        st.error(err)
                    else:
                        st.session_state.user_name = result["name"]
                        st.success("이름이 변경되었습니다.")
                        st.rerun()

    # --- 비밀번호 변경 ---
    with st.expander("🔒 비밀번호 변경", expanded=False):
        with st.form("update_pw_form"):
            cur_pw = st.text_input("현재 비밀번호", type="password", key="cur_pw")
            new_pw = st.text_input("새 비밀번호 (6자 이상)", type="password", key="new_pw")
            new_pw2 = st.text_input("새 비밀번호 확인", type="password", key="new_pw2")
            if st.form_submit_button("비밀번호 변경", width='stretch'):
                if not all([cur_pw, new_pw, new_pw2]):
                    st.error("모든 항목을 입력하세요.")
                elif len(new_pw) < 6:
                    st.error("비밀번호는 6자 이상이어야 합니다.")
                elif new_pw != new_pw2:
                    st.error("새 비밀번호가 일치하지 않습니다.")
                else:
                    result, err = call_api("/auth/me", {
                        "current_password": cur_pw,
                        "new_password": new_pw,
                    }, method="PUT")
                    if err:
                        st.error(err)
                    else:
                        st.success("비밀번호가 변경되었습니다.")

    # --- 회원 탈퇴 ---
    with st.expander("⚠️ 회원 탈퇴", expanded=False):
        st.warning("탈퇴 시 모든 프로필과 분석 데이터가 **영구 삭제**됩니다.")
        with st.form("delete_account_form"):
            del_pw = st.text_input("비밀번호 입력 (탈퇴 확인)", type="password", key="del_pw")
            confirm = st.checkbox("위 내용을 확인했으며 탈퇴에 동의합니다.")
            with st.container():
                st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
                submitted = st.form_submit_button("회원 탈퇴", width='stretch')
                st.markdown('</div>', unsafe_allow_html=True)

            if submitted:
                if not del_pw:
                    st.error("비밀번호를 입력하세요.")
                elif not confirm:
                    st.error("동의 체크박스를 선택하세요.")
                else:
                    _, err = call_api("/auth/me", {"current_password": del_pw}, method="DELETE")
                    if err:
                        st.error(err)
                    else:
                        st.success("탈퇴 완료. 이용해주셔서 감사합니다.")
                        for k in list(st.session_state.keys()):
                            del st.session_state[k]
                        st.rerun()


# ============================================================
# 메인 앱
# ============================================================
def show_main_app():
    # 사이드바 - 사용자 정보 + 관리
    with st.sidebar:
        st.markdown(f"""
        <div class="user-badge">
            👤 &nbsp;<b>{st.session_state.user_name}</b>님<br>
            📧 &nbsp;{st.session_state.user_email}
        </div>
        """, unsafe_allow_html=True)

        if st.button("⚙️ 회원정보 관리"):
            st.session_state.page = 'account'
            st.rerun()

        if st.session_state.get('_confirm_logout'):
            st.warning("정말 로그아웃 하시겠습니까?")
            _lo_c1, _lo_c2 = st.columns(2)
            with _lo_c1:
                if st.button("✅ 로그아웃", width='stretch', type="primary"):
                    try:
                        requests.post(
                            f"{API_BASE}/auth/logout",
                            headers={"Authorization": f"Bearer {st.session_state.token}"},
                            timeout=5,
                        )
                    except Exception:
                        pass
                    _clear_session_cookie()
                    for k in list(st.session_state.keys()):
                        del st.session_state[k]
                    st.session_state.session_invalidated = True
                    st.rerun()
            with _lo_c2:
                if st.button("❌ 취소", width='stretch'):
                    del st.session_state['_confirm_logout']
                    st.rerun()
        else:
            st.markdown('<div class="outline-btn">', unsafe_allow_html=True)
            if st.button("🚪 로그아웃"):
                st.session_state['_confirm_logout'] = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        st.caption("💰 은퇴설계 v0.2.0")

    # ── 모드 헤더 (국가평균 vs 내 정보) ──────────────────────────
    _is_onboarding = st.session_state.get('onboarding_done', False)

    if _is_onboarding:
        # ■ 국가평균 모드
        _bracket = st.session_state.get('_avg_bracket', 55)
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#1565c0,#42a5f5);color:white;
            border-radius:16px;padding:16px 20px;margin-bottom:12px;">
  <div style="font-size:1.1rem;font-weight:700;">🇰🇷 대한민국 {_bracket}세 평균 기준 시뮬레이션</div>
  <div style="font-size:0.85rem;opacity:0.9;margin-top:4px;">
    2026 통계청·국민연금공단 기준 <b>{_bracket}세</b> 평균 소득·연금·자산·부채로 자동 계산된 결과입니다.<br>
    아래 <b>✏️ 내 정보 직접 입력하기</b>를 눌러 실제 데이터로 재분석하세요.
  </div>
</div>
""", unsafe_allow_html=True)
        _ob_c1, _ob_c2 = st.columns([1, 1])
        with _ob_c1:
            if st.button("✏️ 내 정보 직접 입력하기", width='stretch', type="primary"):
                st.session_state.pop('onboarding_done', None)
                st.session_state.analysis_result = None
                st.session_state._goto_personal_tab = True
                st.rerun()
        with _ob_c2:
            st.caption("※ 저장 없이 탭에서 수정 후 📊분석 탭에서 재분석 가능")
    else:
        # ■ 내 정보 모드
        st.markdown("# 💰 은퇴설계")
        st.caption("연금·세금·건보료 종합 시뮬레이션")

    # ── 저장 버튼 (내 정보 모드에서만 표시) ──────────────────────
    def _build_save_payload():
        ss = st.session_state
        return {
            "title": "기본 플랜",
            "personal": {
                "name": ss.get("inp_name", ss.user_name or ""),
                "birth_year":     ss.get("inp_birth_year", 1971),
                "birth_month":    ss.get("inp_birth_month", 5),
                "birth_day":      ss.get("inp_birth_day", 15),
                "gender":         ss.get("inp_gender", "남"),
                "retirement_age": ss.get("inp_retirement_age", 60),
                "expected_lifespan": ss.get("inp_lifespan", 90),
                "dependents":     ss.get("inp_dependents", 1),
                "spouse_nps_monthly":    ss.get("inp_spouse_nps", 0) * 10000,
                "spouse_nps_start_age":  ss.get("inp_spouse_nps_age", 65),
                "spouse_other_monthly":  ss.get("inp_spouse_other", 0) * 10000,
                "spouse_other_start_age": ss.get("inp_spouse_other_age", 65),
            },
            "current_income": {
                "annual_salary":  ss.get("inp_salary", 8000) * 10000,
                "annual_bonus":   ss.get("inp_bonus", 0) * 10000,
                "is_employee":    ss.get("inp_is_employee", True),
                "parttime_monthly": ss.get("inp_parttime_monthly", 0) * 10000,
                "parttime_until_age": ss.get("inp_parttime_until", 70),
            },
            "pensions":          ss.pensions,
            "real_estates":      ss.real_estates,
            "financial_assets":  ss.financial_assets,
            "memberships":       ss.memberships,
            "vehicles":          ss.vehicles,
            "debts":             ss.debts,
            "insurances":        ss.insurances,
            "expected_expense": {
                "living_cost":      ss.get("inp_living", 250) * 10000,
                "medical_cost":     ss.get("inp_medical", 50) * 10000,
                "leisure_cost":     ss.get("inp_leisure", 80) * 10000,
                "family_support":   ss.get("inp_family", 30) * 10000,
                "insurance_premium": ss.get("inp_insurance", 30) * 10000,
                "other":            ss.get("inp_other", 20) * 10000,
            },
        }


    def _build_analyze_payload():
        ss = st.session_state
        return {
            "personal": {
                "name": ss.get("inp_name", ss.user_name or ""),
                "birth_year":  ss.get("inp_birth_year", 1970),
                "birth_month": ss.get("inp_birth_month", 1),
                "birth_day":   ss.get("inp_birth_day", 1),
                "gender":      ss.get("inp_gender", "남"),
                "retirement_age":    ss.get("inp_retirement_age", 60),
                "expected_lifespan": ss.get("inp_lifespan", 85),
                "dependents":        ss.get("inp_dependents", 1),
                "spouse_nps_monthly":    ss.get("inp_spouse_nps", 0) * 10000,
                "spouse_nps_start_age":  ss.get("inp_spouse_nps_age", 65),
                "spouse_other_monthly":  ss.get("inp_spouse_other", 0) * 10000,
                "spouse_other_start_age": ss.get("inp_spouse_other_age", 65),
            },
            "current_income": {
                "annual_salary":  ss.get("inp_salary", 5000) * 10000,
                "annual_bonus":   ss.get("inp_bonus", 0) * 10000,
                "is_employee":    ss.get("inp_is_employee", True),
                "parttime_monthly":  ss.get("inp_parttime_monthly", 0) * 10000,
                "parttime_until_age": ss.get("inp_parttime_until", 70),
            },
            "inflation_rate": ss.get("inp_inflation", 2.5) / 100,
            "pensions":         ss.pensions,
            "real_estates":     ss.real_estates,
            "financial_assets": ss.financial_assets,
            "memberships":      ss.memberships,
            "vehicles":         ss.vehicles,
            "debts":            ss.debts,
            "insurances":       ss.insurances,
            "expected_expense": {
                "living_cost":       ss.get("inp_living", 270) * 10000,
                "medical_cost":      ss.get("inp_medical", 40) * 10000,
                "leisure_cost":      ss.get("inp_leisure", 60) * 10000,
                "family_support":    ss.get("inp_family", 30) * 10000,
                "insurance_premium": ss.get("inp_insurance", 20) * 10000,
                "other":             ss.get("inp_other", 20) * 10000,
            },
        }

    def _run_analysis():
        payload = _build_analyze_payload()
        with st.spinner("분석 중..."):
            result, err = call_api("/analyze", payload)
        if err:
            st.error(err)
        else:
            st.session_state.analysis_result = result
            st.session_state.adj_payout = {}
            st.session_state.adj_start_age = {}
            st.session_state.adj_return_rate = {}
            st.session_state.adj_balance = {}
            st.session_state.adj_monthly_contrib = {}
            st.session_state.adj_nps_balance = None
            st.session_state.adj_nps_monthly = None
            st.session_state.pop('adj_nps_age', None)
            return True
        return False

    # 분석 결과가 없으면 자동 실행 (온보딩 or 저장 후 재분석 트리거)
    if st.session_state.analysis_result is None and st.session_state.get('profile_id') is not None:
        if _run_analysis():
            st.rerun()


    # 탭 네비게이션 (저장된 프로필이 있는 경우에만 표시)
    if not _is_onboarding:
        _tab_labels = ["📊 분석", "🙋 본인", "💼 연금", "🏠 자산/부채", "💳 지출", "🎯 컨설팅"]
        if st.session_state.get('is_admin'):
            _tab_labels.append("🔧 관리자")
            # 관리자 탭 강조 CSS — 마지막 탭을 붉은 계열로
            st.markdown("""
<style>
button[data-baseweb="tab"]:last-of-type {
    background: linear-gradient(135deg,#7b1fa2,#c62828) !important;
    color: #fff !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
}
button[data-baseweb="tab"]:last-of-type:hover {
    background: linear-gradient(135deg,#6a1b9a,#b71c1c) !important;
    opacity: 0.9;
}
button[data-baseweb="tab"][aria-selected="true"]:last-of-type {
    background: linear-gradient(135deg,#4a148c,#c62828) !important;
    box-shadow: 0 0 12px rgba(198,40,40,0.5) !important;
}
</style>""", unsafe_allow_html=True)
        tabs = st.tabs(_tab_labels)
        # "내 정보 직접 입력하기" 클릭 후 본인 탭(index=1)으로 자동 포커스
        if st.session_state.pop('_goto_personal_tab', False):
            st.iframe("""<script>
(function() {
  function clickTab() {
    var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
    if (tabs.length > 1) { tabs[1].click(); }
    else { setTimeout(clickTab, 100); }
  }
  setTimeout(clickTab, 150);
})();
</script>""", height=1)

        # ----------------------------------------------------------
        # 탭 1: 분석
        # ----------------------------------------------------------
        with tabs[0]:
            st.subheader("종합 분석 실행")

            inf_rate = _sl("물가상승률", 0.0, 5.0, st.session_state.get("inp_inflation", 2.5), 0.1, "inp_inflation", "%") / 100

            if st.session_state.get('onboarding_done'):
                st.info("📊 현재 대한민국 평균 기준 시뮬레이션 중입니다. 탭에서 내 정보를 입력한 뒤 아래 버튼을 누르세요.")
            if st.button("🔍 내 정보로 분석하기", type="primary", width='stretch'):
                # 사용자가 직접 분석 클릭 → 내 정보 모드로 전환
                st.session_state.pop('onboarding_done', None)
                if _run_analysis():
                    # 분석 완료 후 자동 저장
                    _ap = _build_save_payload()
                    _apid = st.session_state.profile_id
                    _ar, _ae = (call_api(f"/profiles/{_apid}", _ap, method="PUT")
                                 if _apid and _apid != 0
                                 else call_api("/profiles", _ap))
                    if _ae:
                        st.error(f"⚠️ 자동 저장 실패: {_ae}  \n분석 결과는 표시되지만 데이터가 저장되지 않았습니다. '💾 내 정보 저장' 버튼을 눌러 직접 저장해 주세요.")
                    else:
                        st.session_state.profile_id = _ar.get('id', _apid)
                        st.rerun()


        # ----------------------------------------------------------
        # 탭 2: 본인 정보
        # ----------------------------------------------------------
        with tabs[1]:
            st.subheader("기본 정보")
            col1, col2 = st.columns(2)
            with col1:
                if 'inp_name' not in st.session_state:
                    st.session_state['inp_name'] = st.session_state.user_name or ""
                name = st.text_input("이름", key="inp_name")
                gender = st.selectbox("성별", ["남", "여"], key="inp_gender")
            with col2:
                birth_year = _sl("출생년도", 1940, 2010, st.session_state.get("inp_birth_year", 1970), 1, "inp_birth_year", "년")
                retirement_age = _sl("은퇴희망 연령", 50, 75, st.session_state.get("inp_retirement_age", 60), 1, "inp_retirement_age", "세")

            col3, col4 = st.columns(2)
            with col3:
                birth_month = _sl("출생월", 1, 12, st.session_state.get("inp_birth_month", 1), 1, "inp_birth_month", "월")
            with col4:
                birth_day = _sl("출생일", 1, 31, st.session_state.get("inp_birth_day", 1), 1, "inp_birth_day", "일")

            expected_lifespan = _sl("기대수명", 75, 120, st.session_state.get("inp_lifespan", 90), 1, "inp_lifespan", "세")
            dependents = _sl("부양가족 수", 0, 10, st.session_state.get("inp_dependents", 0), 1, "inp_dependents", "명")

            st.markdown("""
    <div style="margin:1.2rem 0 0.5rem 0;">
      <span style="background:rgba(25,118,210,0.15);color:#1976d2;border:1px solid rgba(25,118,210,0.4);
                   border-radius:6px;padding:4px 12px;font-size:0.95rem;font-weight:700;letter-spacing:0.02em;">
        💼 은퇴 전 소득
      </span>
    </div>
    """, unsafe_allow_html=True)
            annual_salary = _sl("연봉", 0, 30000, st.session_state.get("inp_salary", 0), 100, "inp_salary", "won") * 10000
            annual_bonus = _sl("연간 보너스", 0, 10000, st.session_state.get("inp_bonus", 0), 100, "inp_bonus", "won") * 10000
            is_employee = st.toggle("직장가입자", key="inp_is_employee")

            st.markdown("""
    <div style="margin:1.2rem 0 0.2rem 0;">
      <span style="background:rgba(56,142,60,0.15);color:#388e3c;border:1px solid rgba(56,142,60,0.4);
                   border-radius:6px;padding:4px 12px;font-size:0.95rem;font-weight:700;letter-spacing:0.02em;">
        🌿 은퇴 후 소득
      </span>
    </div>
    """, unsafe_allow_html=True)
            st.caption("파트타임·프리랜서 등 은퇴 후 예상 근로소득")
            col_pt1, col_pt2 = st.columns(2)
            with col_pt1:
                parttime_monthly = _sl("월 근로소득", 0, 2000, st.session_state.get("inp_parttime_monthly", 0), 10, "inp_parttime_monthly", "won") * 10000
            with col_pt2:
                parttime_until = _sl("종료 연령", 60, 80, st.session_state.get("inp_parttime_until", 65), 1, "inp_parttime_until", "세")

            st.markdown("""
    <div style="margin:1.2rem 0 0.2rem 0;">
      <span style="background:rgba(123,31,162,0.12);color:#7b1fa2;border:1px solid rgba(123,31,162,0.35);
                   border-radius:6px;padding:4px 12px;font-size:0.95rem;font-weight:700;letter-spacing:0.02em;">
        👫 배우자 연금
      </span>
    </div>
    """, unsafe_allow_html=True)
            st.caption("배우자의 국민연금·기타연금 예상 수령액")
            col_sp1, col_sp2 = st.columns(2)
            with col_sp1:
                spouse_nps = _sl("배우자 국민연금 월수령액", 0, 500, st.session_state.get("inp_spouse_nps", 0), 5, "inp_spouse_nps", "won") * 10000
                spouse_nps_age = _sl("배우자 국민연금 개시연령", 60, 70, st.session_state.get("inp_spouse_nps_age", 65), 1, "inp_spouse_nps_age", "세")
            with col_sp2:
                spouse_other = _sl("배우자 기타연금 월수령액", 0, 500, st.session_state.get("inp_spouse_other", 0), 5, "inp_spouse_other", "won") * 10000
                spouse_other_age = _sl("배우자 기타연금 개시연령", 50, 85, st.session_state.get("inp_spouse_other_age", 65), 1, "inp_spouse_other_age", "세")

            if st.button("📌 내 국민연금 정상 수급연령 확인", key="check_age"):
                result, err = call_api(f"/pension/start-age/{birth_year}", method="GET")
                if err:
                    st.error(err)
                else:
                    st.success(f"✅ {birth_year}년생 정상 수급연령: **{result['normal_start_age']}세**")

        # ----------------------------------------------------------
        # 탭 2: 연금
        # ----------------------------------------------------------

        # ----------------------------------------------------------
        # 탭 3: 연금
        # ----------------------------------------------------------
        with tabs[2]:
            PENSION_TYPES = ["국민연금", "퇴직연금DB", "퇴직연금DC", "IRP", "연금저축", "개인연금"]
            registered = {p['pension_type']: i for i, p in enumerate(st.session_state.pensions)}
            edit_idx = st.session_state.editing_pension_idx

            # ── 수정 모드 ──────────────────────────────────────────
            if edit_idx is not None and edit_idx < len(st.session_state.pensions):
                p = st.session_state.pensions[edit_idx]

                col_back, col_title = st.columns([1, 4])
                with col_back:
                    if st.button("뒤로", key="pension_back"):
                        st.session_state.editing_pension_idx = None
                        st.rerun()
                with col_title:
                    st.subheader(f"✏️ {p['pension_type']} 수정")

                _sal_won_e = st.session_state.get("inp_salary", 0) * 10000
                _pn_monthly_default_e = max(0, int(p['monthly_contribution'] // 10000))
                if p['pension_type'] == "국민연금":
                    _std = max(430_000, min(int(_sal_won_e / 12), 6_370_000))
                    _is_emp = st.session_state.get("inp_is_employee", True)
                    _rate = 0.045 if _is_emp else 0.09
                    _type_lbl = "직장가입자 4.5%" if _is_emp else "지역가입자 9%"
                    _pn_monthly_default_e = round(_std * _rate / 10000)
                    st.info(
                        f"💡 **현재 소득 기준 예상 납입액**: 월 **{int(_std * _rate):,}원**  \n"
                        f"기준소득월액 {_std:,}원 × {_type_lbl}  \n"
                        f"*(기준소득월액 상한 6,370,000원 / 하한 430,000원 적용)*"
                    )
                elif p['pension_type'] in ("퇴직연금DB", "퇴직연금DC"):
                    _dc_annual_e = int(_sal_won_e / 12)          # 법정 연간 퇴직급여
                    _dc_monthly_e = round(_dc_annual_e / 12)     # 월 적립 본인부담금
                    _pn_monthly_default_e = round(_dc_monthly_e / 10000)
                    st.info(
                        f"💡 **현재 소득 기준 예상 납입액**: 월 **{_dc_monthly_e:,}원**  \n"
                        f"연봉 {int(_sal_won_e):,}원 ÷ 12 (연간 퇴직급여) ÷ 12개월 = 본인부담 월 적립금  \n"
                        f"*(실제 납입액은 회사 규정에 따라 다를 수 있습니다)*"
                    )
                elif p['pension_type'] == "IRP":
                    _irp_monthly_e = 750_000                     # 세액공제 한도 연 900만원 → 월 75만원
                    _pn_monthly_default_e = round(_irp_monthly_e / 10000)
                    st.info(
                        f"💡 **IRP 세액공제 최대 한도 기준**: 월 **{_irp_monthly_e:,}원**  \n"
                        f"연간 세액공제 한도 9,000,000원 ÷ 12개월  \n"
                        f"*(실제 납입액은 개인 선택에 따라 다를 수 있습니다)*"
                    )

                with st.form("edit_pension_form"):
                    pn_name = st.text_input("상품명/기관명", value=p['name'])
                    c1, c2 = st.columns(2)
                    with c1:
                        pn_balance = _sl("현재 적립금", 0, 50000,
                            min(50000, max(0, int(p['current_balance'] // 10000))), 500, fmt="won")
                        pn_end_age = _sl("납입 종료 연령", 30, 80,
                            min(max(p['contribution_end_age'], 30), 80), 1, fmt="세")
                    with c2:
                        pn_monthly = _sl("월 납입금", 0, 200, _pn_monthly_default_e, 10, fmt="won")
                        pn_start_age = _sl("수령 개시 연령", 50, 85,
                            min(max(p['expected_start_age'], 50), 85), 1, fmt="세")
                    c3, c4 = st.columns(2)
                    with c3:
                        pn_payout = _sl("예상 월 수령액", 0, 500,
                            min(500, max(0, int(p['expected_monthly_payout'] // 10000))), 10, fmt="won")
                    with c4:
                        pn_return = _sl("예상 연수익률", 0.0, 20.0,
                            round(round(p['annual_return_rate'] * 100 / 0.2) * 0.2, 1), 0.2, fmt="%") / 100
                    pn_period = _sl("수령기간(년, 0=종신)", 0, 40,
                        min(p['payout_period_years'], 40), 1, fmt="년")

                    if st.form_submit_button("💾 저장", width='stretch'):
                        st.session_state.pensions[edit_idx] = {
                            **p,
                            "name": pn_name,
                            "current_balance": pn_balance * 10000,
                            "monthly_contribution": pn_monthly * 10000,
                            "contribution_end_age": pn_end_age,
                            "expected_start_age": pn_start_age,
                            "expected_monthly_payout": pn_payout * 10000,
                            "annual_return_rate": pn_return,
                            "payout_period_years": pn_period,
                        }
                        st.session_state.editing_pension_idx = None
                        st.rerun()

            # ── 추가 + 목록 모드 ────────────────────────────────────
            else:
                st.subheader("연금 상품 등록")
                st.caption("국민연금, 퇴직연금, IRP, 연금저축 등")

                with st.expander("📋 국민연금(노령연금) 수급 조건", expanded=False):
                    # 출생연도별 수급개시 연령 (user의 birth_year 강조)
                    _NPS_AGE_TABLE = [
                        ("1953 ~ 1956년생", (1953, 1956), 61),
                        ("1957 ~ 1960년생", (1957, 1960), 62),
                        ("1961 ~ 1964년생", (1961, 1964), 63),
                        ("1965 ~ 1968년생", (1965, 1968), 64),
                        ("1969년생 이후",   (1969, 9999), 65),
                    ]
                    _user_nps_age = next((age for label, (s, e), age in _NPS_AGE_TABLE
                                          if s <= birth_year <= e), 65)

                    st.markdown("#### 🔑 기본 수급 요건")
                    st.markdown("""
    | 요건 | 내용 |
    |------|------|
    | **가입기간** | **최소 10년(120개월) 이상** 납부해야 노령연금 수급권 발생 |
    | **연령** | 출생연도에 따라 만 61~65세부터 수령 가능 |
    | **10년 미만** | 노령연금 불가 /**반환일시금** (납부액 + 이자) 일시 지급 |
    """)

                    st.markdown("#### 📅 출생연도별 수급개시 연령")
                    _age_rows = []
                    for label, (s, e), age in _NPS_AGE_TABLE:
                        marker = " ✅ 나의 해당" if s <= birth_year <= e else ""
                        _age_rows.append(f"| {label} | **{age}세** |{marker}")
                    st.markdown("| 출생연도 | 정상 수급개시 |\n|----------|------------|  \n" +
                                "\n".join(_age_rows))
                    st.info(f"✅ **{birth_year}년생**의 정상 수급개시 연령: **{_user_nps_age}세**")

                    st.markdown("#### ⏩ 조기노령연금 (감액 수령)")
                    st.markdown(f"""
    - 정상 수급연령 **최대 5년 전**부터 신청 가능 /**{_user_nps_age - 5}세**부터 가능
    - 1년 앞당길 때마다 **연 6% 감액** (월 0.5%)
    - 단, 신청 당시 **소득이 없어야** 함 (근로·사업소득 有 시 신청 불가)

    | 수령 시작 | 감액률 | 예시 (월 100만원 기준) |
    |-----------|--------|----------------------|
    | {_user_nps_age - 5}세 (5년 조기) | **-30%** | 월 **70만원** |
    | {_user_nps_age - 4}세 (4년 조기) | -24% | 월 80만 4천원 |
    | {_user_nps_age - 3}세 (3년 조기) | -18% | 월 85만원 |
    | {_user_nps_age - 2}세 (2년 조기) | -12% | 월 88만원 |
    | {_user_nps_age - 1}세 (1년 조기) | -6% | 월 94만원 |
    | **{_user_nps_age}세** (정상) | **0%** | 월 **100만원** ⭐ |
    """)

                    st.markdown("#### ⏪ 연기연금 (가산 수령)")
                    st.markdown(f"""
    - 정상 수급연령 이후 **최대 5년 연기** 신청 가능 /**{_user_nps_age + 5}세**까지
    - 1년 늦출 때마다 **연 7.2% 가산** (월 0.6%)
    - 연기 기간 중에도 국민연금 가입 불필요

    | 수령 시작 | 가산률 | 예시 (월 100만원 기준) |
    |-----------|--------|----------------------|
    | **{_user_nps_age}세** (정상) | **0%** | 월 **100만원** ⭐ |
    | {_user_nps_age + 1}세 (1년 연기) | +7.2% | 월 107만 2천원 |
    | {_user_nps_age + 2}세 (2년 연기) | +14.4% | 월 114만 4천원 |
    | {_user_nps_age + 3}세 (3년 연기) | +21.6% | 월 121만 6천원 |
    | {_user_nps_age + 4}세 (4년 연기) | +28.8% | 월 128만 8천원 |
    | {_user_nps_age + 5}세 (5년 연기) | **+36%** | 월 **136만원** |
    """)

                    st.markdown("#### ⚠️ 소득이 있을 때 감액 (재직자 노령연금)")
                    st.markdown("""
    - 수급연령 도달 후에도 **소득월액이 A값(약 309만원)을 초과**하면 연금 일부 감액
    - 초과 소득 구간별로 최대 **50% 감액** (5년 후 자동 해제)

    | 초과 소득 구간 | 감액 비율 |
    |--------------|---------|
    | 100만원 미만 초과 | 초과액의 5% |
    | 100~200만원 | 5만원 + 100만원 초과분의 10% |
    | 200~300만원 | 15만원 + 200만원 초과분의 15% |
    | 300~400만원 | 30만원 + 300만원 초과분의 20% |
    | 400만원 이상 | 50만원 + 400만원 초과분의 25% (최대 50%) |

    > 💡 은퇴 직후에도 프리랜서·임대·이자소득이 있으면 A값 초과 여부를 확인하세요.
    """)

                    st.markdown("#### 💡 핵심 체크리스트")
                    st.markdown(f"""
    - [ ] 가입기간 **10년(120개월) 이상** 확인 /국민연금공단 앱에서 조회
    - [ ] 정상 수급연령: **{_user_nps_age}세** ({birth_year}년생 기준)
    - [ ] 조기 수령 시 소득 없음 조건 충족 여부 확인
    - [ ] 퇴직 후 소득 있으면 **재직자 감액** 해당 여부 체크
    - [ ] 배우자 노령연금과의 **연계·분할연금** 제도 활용 검토
    """)
                    st.markdown("#### 🔗 공식 사이트")
                    st.markdown(
                        "| 용도 | 링크 |\n|------|------|\n"
                        "| 예상연금 모의계산 (로그인 불필요) | [국민연금공단 모의계산기](https://csa.nps.or.kr/ib2010/mvc/pension/pensionCalculation.do) |\n"
                        "| 내 가입내역·예상수령액 조회 | [내 연금 알아보기](https://www.nps.or.kr/jsppage/business/moca/moca_04.jsp) |\n"
                        "| 수급개시연령 · 감액기준 공식 안내 | [국민연금공단 노령연금](https://www.nps.or.kr/jsppage/pension/hd/hd_01_01.jsp) |\n"
                        "| 보험료율 · 기준소득월액 현황 | [국민연금 보험료 안내](https://www.nps.or.kr/jsppage/business/info/info_04_01.jsp) |",
                        unsafe_allow_html=False,
                    )

                with st.expander("ℹ️ 사적연금 종류 안내", expanded=False):
                    st.markdown("""
    | 종류 | 세액공제 | 수령가능 | 특징 |
    |------|---------|---------|------|
    | **IRP** | 연 900만원 한도 (16.5%) | 만 55세~ | 퇴직금 이전 가능, 가장 폭넓은 상품 |
    | **연금저축펀드** | IRP 포함 900만원 한도 | 만 55세~ | 직접 펀드 운용, 중도인출 가능 |
    | **퇴직연금 DC** | 회사 납입분 세액공제 | 퇴직 후 | 본인이 직접 운용, 수익률 본인 책임 |
    | **퇴직연금 DB** | 회사 납입 | 퇴직 후 | 확정급여형, 회사가 운용 |
    | **개인연금(보험)** | 없음 | 계약 조건 | 비과세 혜택, 종신수령 가능 |

    > 💡 **세액공제 절세 팁**: IRP + 연금저축 합산 연 900만원까지 납입 시 최대 148.5만원 환급
    > 💡 **연 1,500만원 초과 수령** 시 종합과세 또는 16.5% 분리과세 선택 필요
    """)
                    st.markdown("**🔗 공식 사이트**")
                    st.markdown(
                        "| 용도 | 링크 |\n|------|------|\n"
                        "| 연금저축·IRP 세액공제 한도 안내 | [국세청 연금계좌](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=6655&cntntsId=7751) |\n"
                        "| 퇴직연금 제도 안내 (고용노동부) | [퇴직연금 포털](https://www.moel.go.kr/retirementBenefit/main.do) |\n"
                        "| 연금상품 비교공시 | [금융감독원 통합연금포털](https://100lifeplan.fss.or.kr) |\n"
                        "| 사적연금 과세 기준 | [국세청 연금소득 안내](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=6527&cntntsId=7667) |"
                    )

                with st.expander("➕ 새 연금 추가", expanded=False):
                    pn_type_sel = st.selectbox("연금 종류", PENSION_TYPES, key="new_pn_type")

                    if pn_type_sel in registered:
                        st.warning(f"⚠️ **{pn_type_sel}** 은(는) 이미 등록되어 있습니다.")
                        if st.button("✏️ 수정하기", key="edit_existing_pn", width='stretch'):
                            st.session_state.editing_pension_idx = registered[pn_type_sel]
                            st.rerun()
                    else:
                        # 연금 종류별 월 납입액 자동계산
                        _sal_won = st.session_state.get("inp_salary", 0) * 10000
                        _pn_monthly_default = 0
                        if pn_type_sel == "국민연금":
                            _std = max(430_000, min(int(_sal_won / 12), 6_370_000))
                            _is_emp = st.session_state.get("inp_is_employee", True)
                            _rate = 0.045 if _is_emp else 0.09
                            _pn_monthly_default = round(_std * _rate / 10000)
                            _type_lbl = "직장가입자 4.5%" if _is_emp else "지역가입자 9%"
                            st.info(
                                f"💡 **현재 소득 기준 예상 납입액**: 월 **{int(_std * _rate):,}원**  \n"
                                f"기준소득월액 {_std:,}원 × {_type_lbl}  \n"
                                f"*(기준소득월액 상한 6,370,000원 / 하한 430,000원 적용)*"
                            )
                        elif pn_type_sel in ("퇴직연금DB", "퇴직연금DC"):
                            _dc_annual = int(_sal_won / 12)          # 법정 연간 퇴직급여
                            _dc_monthly = round(_dc_annual / 12)     # 월 적립 본인부담금
                            _pn_monthly_default = round(_dc_monthly / 10000)
                            st.info(
                                f"💡 **현재 소득 기준 예상 납입액**: 월 **{_dc_monthly:,}원**  \n"
                                f"연봉 {int(_sal_won):,}원 ÷ 12 (연간 퇴직급여) ÷ 12개월 = 본인부담 월 적립금  \n"
                                f"*(실제 납입액은 회사 규정에 따라 다를 수 있습니다)*"
                            )
                        elif pn_type_sel == "IRP":
                            _irp_monthly = 750_000                   # 세액공제 한도 연 900만원 → 월 75만원
                            _pn_monthly_default = round(_irp_monthly / 10000)
                            st.info(
                                f"💡 **IRP 세액공제 최대 한도 기준**: 월 **{_irp_monthly:,}원**  \n"
                                f"연간 세액공제 한도 9,000,000원 ÷ 12개월  \n"
                                f"*(실제 납입액은 개인 선택에 따라 다를 수 있습니다)*"
                            )

                        with st.form("add_pension", clear_on_submit=True):
                            pn_name = st.text_input("상품명/기관명", value=pn_type_sel)
                            c1, c2 = st.columns(2)
                            with c1:
                                pn_balance = _sl("현재 적립금", 0, 50000, 0, 500, fmt="won") * 10000
                                pn_end_age = _sl("납입 종료 연령", 30, 80, 60, 1, fmt="세")
                            with c2:
                                pn_monthly = _sl("월 납입금", 0, 200, _pn_monthly_default, 10, fmt="won") * 10000
                                pn_start_age = _sl("수령 개시 연령", 50, 85, 65, 1, fmt="세")
                            c3, c4 = st.columns(2)
                            with c3:
                                pn_payout_monthly = _sl("예상 월 수령액", 0, 500, 0, 10, fmt="won") * 10000
                            with c4:
                                pn_return = _sl("예상 연수익률", 0.0, 20.0, 4.0, 0.2, fmt="%") / 100
                            pn_period = _sl("수령기간(년, 0=종신)", 0, 40, 20, 1, fmt="년")
                            if st.form_submit_button("추가", width='stretch'):
                                st.session_state.pensions.append({
                                    "pension_type": pn_type_sel, "name": pn_name,
                                    "current_balance": pn_balance, "monthly_contribution": pn_monthly,
                                    "contribution_end_age": pn_end_age, "expected_start_age": pn_start_age,
                                    "expected_monthly_payout": pn_payout_monthly,
                                    "annual_return_rate": pn_return, "payout_period_years": pn_period,
                                    "contribution_years": 0,
                                })
                                st.rerun()

                if st.session_state.pensions:
                    st.markdown("### 등록된 연금")
                    for i, p in enumerate(st.session_state.pensions):
                        c1, c2, c3 = st.columns([5, 1, 1])
                        with c1:
                            st.markdown(f"**{p['name']}** ({p['pension_type']})")
                            _rate = p.get('annual_return_rate', 0)
                            st.caption(
                                f"적립 {fmt_won(p['current_balance'])} · "
                                f"월납 {fmt_won(p['monthly_contribution'])} · "
                                f"{p['expected_start_age']}세부터 수령 · "
                                f"수익률 {_rate*100:.1f}%"
                            )
                        with c2:
                            if st.button("✏️", key=f"edit_pn_{i}", help="수정"):
                                st.session_state.editing_pension_idx = i
                                st.rerun()
                        with c3:
                            if st.button("🗑", key=f"del_pn_{i}", help="삭제"):
                                st.session_state.pensions.pop(i)
                                st.rerun()
                else:
                    st.info("등록된 연금이 없습니다.")

        # ----------------------------------------------------------
        # 탭 3: 자산
        # ----------------------------------------------------------

        # ----------------------------------------------------------
        # 탭 4: 자산
        # ----------------------------------------------------------
        with tabs[3]:
            asset_subtab = st.radio(
                "자산 유형",
                ["🏠 부동산", "💳 금융", "⛳ 회원권", "🚗 차량", "🛡 보험", "📉 대출"],
                horizontal=True, label_visibility="collapsed",
            )

            if asset_subtab == "🏠 부동산":
                re_edit_idx = st.session_state.editing_re_idx

                if re_edit_idx is not None and re_edit_idx < len(st.session_state.real_estates):
                    r = st.session_state.real_estates[re_edit_idx]
                    col_back, col_title = st.columns([1, 4])
                    with col_back:
                        if st.button("뒤로", key="re_back"):
                            st.session_state.editing_re_idx = None; st.rerun()
                    with col_title:
                        st.subheader(f"✏️ {r['name']} 수정")
                    with st.form("edit_re"):
                        re_name = st.text_input("이름", r['name'])
                        re_type = st.selectbox("종류", ["자가", "전세", "월세"],
                                               index=["자가", "전세", "월세"].index(r['house_type']))
                        re_market = _sl("시세", 0, 200000,
                                        min(200000, int(r['market_value'] // 10000)), 1000, fmt="won") * 10000
                        re_official = _sl("공시가격 (비우면 시세*70%)", 0, 200000,
                                          min(200000, int((r['official_price'] or 0) // 10000)), 1000, fmt="won") * 10000
                        re_debt = _sl("담보대출", 0, 100000,
                                      min(100000, int(r['debt'] // 10000)), 1000, fmt="won") * 10000
                        re_rent = _sl("월세 수입", 0, 500,
                                      min(500, int(r['monthly_rent_income'] // 10000)), 10, fmt="won") * 10000
                        re_primary = st.toggle("주거용 (1세대 1주택)", value=r['is_primary_residence'])
                        if st.form_submit_button("저장", width='stretch'):
                            st.session_state.real_estates[re_edit_idx] = {
                                "name": re_name, "house_type": re_type,
                                "market_value": re_market, "official_price": re_official,
                                "debt": re_debt, "monthly_rent_income": re_rent,
                                "is_primary_residence": re_primary,
                            }
                            st.session_state.editing_re_idx = None; st.rerun()
                else:
                    with st.expander("➕ 부동산 추가", expanded=False):
                        with st.form("add_re", clear_on_submit=True):
                            re_name = st.text_input("이름", "본가")
                            re_type = st.selectbox("종류", ["자가", "전세", "월세"])
                            re_market = _sl("시세", 0, 200000, 0, 1000, fmt="won") * 10000
                            re_official = _sl("공시가격 (비우면 시세*70%)", 0, 200000, 0, 1000, fmt="won") * 10000
                            re_debt = _sl("담보대출", 0, 100000, 0, 1000, fmt="won") * 10000
                            re_rent = _sl("월세 수입", 0, 500, 0, 10, fmt="won") * 10000
                            re_primary = st.toggle("주거용 (1세대 1주택)", value=True)
                            if st.form_submit_button("추가", width='stretch'):
                                st.session_state.real_estates.append({
                                    "name": re_name, "house_type": re_type,
                                    "market_value": re_market, "official_price": re_official,
                                    "debt": re_debt, "monthly_rent_income": re_rent,
                                    "is_primary_residence": re_primary,
                                })
                                st.rerun()
                    for i, r in enumerate(st.session_state.real_estates):
                        c1, c2, c3 = st.columns([5, 1, 1])
                        with c1:
                            st.markdown(f"**{r['name']}** ({r['house_type']})")
                            st.caption(f"시세 {fmt_won(r['market_value'])} · 대출 {fmt_won(r['debt'])}"
                                       + (f" · 월세 {fmt_won(r['monthly_rent_income'])}" if r['monthly_rent_income'] else ""))
                        with c2:
                            if st.button("✏️", key=f"edit_re_{i}", help="수정"):
                                st.session_state.editing_re_idx = i; st.rerun()
                        with c3:
                            if st.button("🗑", key=f"del_re_{i}"):
                                st.session_state.real_estates.pop(i); st.rerun()

            elif asset_subtab == "💳 금융":
                FA_TYPES = ["예금", "적금", "주식", "채권", "펀드", "ETF", "ISA"]
                fa_edit_idx = st.session_state.editing_fa_idx

                if fa_edit_idx is not None and fa_edit_idx < len(st.session_state.financial_assets):
                    f = st.session_state.financial_assets[fa_edit_idx]
                    col_back, col_title = st.columns([1, 4])
                    with col_back:
                        if st.button("뒤로", key="fa_back"):
                            st.session_state.editing_fa_idx = None; st.rerun()
                    with col_title:
                        st.subheader(f"✏️ {f['name']} 수정")
                    with st.form("edit_fa"):
                        fa_name = st.text_input("이름", f['name'])
                        fa_type = st.selectbox("종류", FA_TYPES,
                                               index=FA_TYPES.index(f['asset_type']) if f['asset_type'] in FA_TYPES else 0)
                        fa_amount = _sl("금액", 0, 100000,
                                        min(100000, int(f['amount'] // 10000)), 500, fmt="won") * 10000
                        fa_return = _sl("예상 연수익률", 0.0, 50.0,
                            min(round(f['annual_return_rate'] * 100, 1), 50.0), 0.5, fmt="%") / 100
                        fa_taxable = st.toggle("과세대상", value=f['is_taxable'])
                        if st.form_submit_button("저장", width='stretch'):
                            st.session_state.financial_assets[fa_edit_idx] = {
                                "name": fa_name, "asset_type": fa_type,
                                "amount": fa_amount, "annual_return_rate": fa_return,
                                "is_taxable": fa_taxable,
                            }
                            st.session_state.editing_fa_idx = None; st.rerun()
                else:
                    with st.expander("➕ 금융자산 추가", expanded=False):
                        with st.form("add_fa", clear_on_submit=True):
                            fa_name = st.text_input("이름", "주거래은행 예금")
                            fa_type = st.selectbox("종류", FA_TYPES)
                            fa_amount = _sl("금액", 0, 100000, 0, 500, fmt="won") * 10000
                            fa_return = _sl("예상 연수익률", 0.0, 50.0, 3.0, 0.5, fmt="%") / 100
                            fa_taxable = st.toggle("과세대상", value=(fa_type != "ISA"))
                            if st.form_submit_button("추가", width='stretch'):
                                st.session_state.financial_assets.append({
                                    "name": fa_name, "asset_type": fa_type,
                                    "amount": fa_amount, "annual_return_rate": fa_return,
                                    "is_taxable": fa_taxable,
                                })
                                st.rerun()
                    for i, f in enumerate(st.session_state.financial_assets):
                        c1, c2, c3 = st.columns([5, 1, 1])
                        with c1:
                            st.markdown(f"**{f['name']}** ({f['asset_type']})")
                            st.caption(f"{fmt_won(f['amount'])} · 연 {f['annual_return_rate']*100:.1f}%")
                        with c2:
                            if st.button("✏️", key=f"edit_fa_{i}", help="수정"):
                                st.session_state.editing_fa_idx = i; st.rerun()
                        with c3:
                            if st.button("🗑", key=f"del_fa_{i}"):
                                st.session_state.financial_assets.pop(i); st.rerun()

            elif asset_subtab == "⛳ 회원권":
                MS_TYPES = ["golf", "condo"]
                ms_fmt = lambda x: "골프" if x == "golf" else "콘도"
                ms_edit_idx = st.session_state.editing_ms_idx

                if ms_edit_idx is not None and ms_edit_idx < len(st.session_state.memberships):
                    m = st.session_state.memberships[ms_edit_idx]
                    col_back, col_title = st.columns([1, 4])
                    with col_back:
                        if st.button("뒤로", key="ms_back"):
                            st.session_state.editing_ms_idx = None; st.rerun()
                    with col_title:
                        st.subheader(f"✏️ {m['name']} 수정")
                    with st.form("edit_ms"):
                        ms_name = st.text_input("이름", m['name'])
                        ms_type = st.selectbox("종류", MS_TYPES,
                                               index=MS_TYPES.index(m['membership_type']) if m['membership_type'] in MS_TYPES else 0,
                                               format_func=ms_fmt)
                        ms_value = _sl("시세", 0, 50000,
                                       min(50000, int(m['market_value'] // 10000)), 500, fmt="won") * 10000
                        ms_dues = _sl("연회비", 0, 1000,
                                      min(1000, int(m['annual_dues'] // 10000)), 10, fmt="won") * 10000
                        if st.form_submit_button("저장", width='stretch'):
                            st.session_state.memberships[ms_edit_idx] = {
                                "name": ms_name, "membership_type": ms_type,
                                "market_value": ms_value, "annual_dues": ms_dues,
                            }
                            st.session_state.editing_ms_idx = None; st.rerun()
                else:
                    with st.expander("➕ 회원권 추가", expanded=False):
                        with st.form("add_ms", clear_on_submit=True):
                            ms_name = st.text_input("이름", "○○ 골프회원권")
                            ms_type = st.selectbox("종류", MS_TYPES, format_func=ms_fmt)
                            ms_value = _sl("시세", 0, 50000, 0, 500, fmt="won") * 10000
                            ms_dues = _sl("연회비", 0, 1000, 0, 10, fmt="won") * 10000
                            if st.form_submit_button("추가", width='stretch'):
                                st.session_state.memberships.append({
                                    "name": ms_name, "membership_type": ms_type,
                                    "market_value": ms_value, "annual_dues": ms_dues,
                                })
                                st.rerun()
                    for i, m in enumerate(st.session_state.memberships):
                        c1, c2, c3 = st.columns([5, 1, 1])
                        with c1:
                            st.markdown(f"**{m['name']}** ({ms_fmt(m['membership_type'])})")
                            st.caption(f"시세 {fmt_won(m['market_value'])} · 연회비 {fmt_won(m['annual_dues'])}")
                        with c2:
                            if st.button("✏️", key=f"edit_ms_{i}", help="수정"):
                                st.session_state.editing_ms_idx = i; st.rerun()
                        with c3:
                            if st.button("🗑", key=f"del_ms_{i}"):
                                st.session_state.memberships.pop(i); st.rerun()

            elif asset_subtab == "🚗 차량":
                v_edit_idx = st.session_state.editing_v_idx

                if v_edit_idx is not None and v_edit_idx < len(st.session_state.vehicles):
                    v = st.session_state.vehicles[v_edit_idx]
                    col_back, col_title = st.columns([1, 4])
                    with col_back:
                        if st.button("뒤로", key="v_back"):
                            st.session_state.editing_v_idx = None; st.rerun()
                    with col_title:
                        st.subheader(f"✏️ {v['name']} 수정")
                    with st.form("edit_v"):
                        v_name = st.text_input("이름", v['name'])
                        v_value = _sl("시세", 0, 20000,
                                      min(20000, int(v['market_value'] // 10000)), 100, fmt="won") * 10000
                        v_cost = _sl("연 유지비 (보험+세금+유류)", 0, 500,
                                     min(500, int(v['annual_cost'] // 10000)), 10, fmt="won") * 10000
                        if st.form_submit_button("저장", width='stretch'):
                            st.session_state.vehicles[v_edit_idx] = {
                                "name": v_name, "market_value": v_value, "annual_cost": v_cost,
                            }
                            st.session_state.editing_v_idx = None; st.rerun()
                else:
                    with st.expander("➕ 차량 추가", expanded=False):
                        with st.form("add_v", clear_on_submit=True):
                            v_name = st.text_input("이름", "○○ 차량")
                            v_value = _sl("시세", 0, 20000, 4000, 100, fmt="won") * 10000
                            v_cost = _sl("연 유지비 (보험+세금+유류)", 0, 500, 400, 10, fmt="won") * 10000
                            if st.form_submit_button("추가", width='stretch'):
                                st.session_state.vehicles.append({
                                    "name": v_name, "market_value": v_value, "annual_cost": v_cost,
                                })
                                st.rerun()
                    for i, v in enumerate(st.session_state.vehicles):
                        c1, c2, c3 = st.columns([5, 1, 1])
                        with c1:
                            st.markdown(f"**{v['name']}**")
                            st.caption(f"시세 {fmt_won(v['market_value'])} · 연유지비 {fmt_won(v['annual_cost'])}")
                        with c2:
                            if st.button("✏️", key=f"edit_v_{i}", help="수정"):
                                st.session_state.editing_v_idx = i; st.rerun()
                        with c3:
                            if st.button("🗑", key=f"del_v_{i}"):
                                st.session_state.vehicles.pop(i); st.rerun()

            elif asset_subtab == "🛡 보험":
                INS_TYPES = ["연금보험", "종신보험", "저축보험", "건강보험"]
                ins_edit_idx = st.session_state.editing_ins_idx

                if ins_edit_idx is not None and ins_edit_idx < len(st.session_state.insurances):
                    ins = st.session_state.insurances[ins_edit_idx]
                    col_back, col_title = st.columns([1, 4])
                    with col_back:
                        if st.button("뒤로", key="ins_back"):
                            st.session_state.editing_ins_idx = None; st.rerun()
                    with col_title:
                        st.subheader(f"✏️ {ins['name']} 수정")
                    with st.form("edit_ins"):
                        ins_type = st.selectbox("보험 종류", INS_TYPES,
                                                index=INS_TYPES.index(ins['insurance_type']) if ins['insurance_type'] in INS_TYPES else 0)
                        ins_name = st.text_input("상품명", ins['name'])
                        ins_premium = _sl("월 납입 보험료", 0, 100,
                                          min(100, int(ins['monthly_premium'] // 10000)), 1, fmt="won") * 10000
                        ins_end_age = _sl("납입 종료 연령", 30, 80, ins['premium_end_age'], 1, fmt="세")
                        ins_surrender = _sl("해약환급금", 0, 50000,
                                            min(50000, int(ins['surrender_value'] // 10000)), 500, fmt="won") * 10000
                        ins_maturity = _sl("만기/수령 예상금액", 0, 50000,
                                           min(50000, int(ins['maturity_value'] // 10000)), 500, fmt="won") * 10000
                        if ins_type == "연금보험":
                            ins_payout = _sl("월 수령액 (연금형)", 0, 500,
                                             min(500, int(ins['monthly_payout'] // 10000)), 10, fmt="won") * 10000
                            ins_payout_start = _sl("수령 개시 연령", 50, 85, ins['payout_start_age'], 1, fmt="세")
                            ins_payout_period = _sl("수령기간(년, 0=종신)", 0, 40, ins['payout_period_years'], 1, fmt="년")
                        else:
                            ins_payout = 0
                            ins_payout_start = ins['payout_start_age']
                            ins_payout_period = ins['payout_period_years']
                        if st.form_submit_button("저장", width='stretch'):
                            st.session_state.insurances[ins_edit_idx] = {
                                "name": ins_name, "insurance_type": ins_type,
                                "monthly_premium": ins_premium, "premium_end_age": ins_end_age,
                                "surrender_value": ins_surrender, "maturity_value": ins_maturity,
                                "monthly_payout": ins_payout, "payout_start_age": ins_payout_start,
                                "payout_period_years": ins_payout_period,
                            }
                            st.session_state.editing_ins_idx = None; st.rerun()
                else:
                    with st.expander("➕ 보험 추가", expanded=False):
                        with st.form("add_ins", clear_on_submit=True):
                            ins_type = st.selectbox("보험 종류", INS_TYPES)
                            ins_name = st.text_input("상품명", "○○ 연금보험")
                            ins_premium = _sl("월 납입 보험료", 0, 100, 0, 1, fmt="won") * 10000
                            ins_end_age = _sl("납입 종료 연령", 30, 80, 65, 1, fmt="세")
                            ins_surrender = _sl("해약환급금", 0, 50000, 0, 500, fmt="won") * 10000
                            ins_maturity = _sl("만기/수령 예상금액", 0, 50000, 0, 500, fmt="won") * 10000
                            if ins_type == "연금보험":
                                ins_payout = _sl("월 수령액 (연금형)", 0, 500, 0, 10, fmt="won") * 10000
                                ins_payout_start = _sl("수령 개시 연령", 50, 85, 65, 1, fmt="세")
                                ins_payout_period = _sl("수령기간(년, 0=종신)", 0, 40, 0, 1, fmt="년")
                            else:
                                ins_payout = 0
                                ins_payout_start = 65
                                ins_payout_period = 0
                            if st.form_submit_button("추가", width='stretch'):
                                st.session_state.insurances.append({
                                    "name": ins_name, "insurance_type": ins_type,
                                    "monthly_premium": ins_premium, "premium_end_age": ins_end_age,
                                    "surrender_value": ins_surrender, "maturity_value": ins_maturity,
                                    "monthly_payout": ins_payout, "payout_start_age": ins_payout_start,
                                    "payout_period_years": ins_payout_period,
                                })
                                st.rerun()
                    for i, ins in enumerate(st.session_state.insurances):
                        c1, c2, c3 = st.columns([5, 1, 1])
                        with c1:
                            st.markdown(f"**{ins['name']}** ({ins['insurance_type']})")
                            caption_parts = [f"월납입 {fmt_won(ins['monthly_premium'])}",
                                             f"해약환급금 {fmt_won(ins['surrender_value'])}"]
                            if ins['insurance_type'] == "연금보험" and ins['monthly_payout'] > 0:
                                caption_parts.append(f"월수령 {fmt_won(ins['monthly_payout'])}")
                            st.caption(" · ".join(caption_parts))
                        with c2:
                            if st.button("✏️", key=f"edit_ins_{i}", help="수정"):
                                st.session_state.editing_ins_idx = i; st.rerun()
                        with c3:
                            if st.button("🗑", key=f"del_ins_{i}"):
                                st.session_state.insurances.pop(i); st.rerun()

            elif asset_subtab == "📉 대출":
                D_TYPES = ["주담대", "신용대출", "전세대출", "기타"]
                d_edit_idx = st.session_state.editing_d_idx

                if d_edit_idx is not None and d_edit_idx < len(st.session_state.debts):
                    d = st.session_state.debts[d_edit_idx]
                    col_back, col_title = st.columns([1, 4])
                    with col_back:
                        if st.button("뒤로", key="d_back"):
                            st.session_state.editing_d_idx = None; st.rerun()
                    with col_title:
                        st.subheader(f"✏️ {d['name']} 수정")
                    with st.form("edit_d"):
                        d_name = st.text_input("이름", d['name'])
                        d_type = st.selectbox("종류", D_TYPES,
                                              index=D_TYPES.index(d['debt_type']) if d['debt_type'] in D_TYPES else 0)
                        d_balance = _sl("잔액", 0, 100000,
                                        min(100000, int(d['balance'] // 10000)), 500, fmt="won") * 10000
                        d_rate = _sl("이율", 0.0, 15.0,
                            round(d['interest_rate'] * 100, 1), 0.5, fmt="%") / 100
                        d_payment = _sl("월 상환액", 0, 500,
                                        min(500, int(d['monthly_payment'] // 10000)), 10, fmt="won") * 10000
                        if st.form_submit_button("저장", width='stretch'):
                            st.session_state.debts[d_edit_idx] = {
                                "name": d_name, "debt_type": d_type, "balance": d_balance,
                                "interest_rate": d_rate, "monthly_payment": d_payment,
                            }
                            st.session_state.editing_d_idx = None; st.rerun()
                else:
                    with st.expander("➕ 대출 추가", expanded=False):
                        with st.form("add_d", clear_on_submit=True):
                            d_name = st.text_input("이름", "주택담보대출")
                            d_type = st.selectbox("종류", D_TYPES)
                            d_balance = _sl("잔액", 0, 100000, 0, 500, fmt="won") * 10000
                            d_rate = _sl("이율", 0.0, 15.0, 4.5, 0.5, fmt="%") / 100
                            d_payment = _sl("월 상환액", 0, 500, 0, 10, fmt="won") * 10000
                            if st.form_submit_button("추가", width='stretch'):
                                st.session_state.debts.append({
                                    "name": d_name, "debt_type": d_type, "balance": d_balance,
                                    "interest_rate": d_rate, "monthly_payment": d_payment,
                                })
                                st.rerun()
                    for i, d in enumerate(st.session_state.debts):
                        c1, c2, c3 = st.columns([5, 1, 1])
                        with c1:
                            st.markdown(f"**{d['name']}** ({d['debt_type']})")
                            st.caption(f"잔액 {fmt_won(d['balance'])} · 이율 {d['interest_rate']*100:.2f}%")
                        with c2:
                            if st.button("✏️", key=f"edit_d_{i}", help="수정"):
                                st.session_state.editing_d_idx = i; st.rerun()
                        with c3:
                            if st.button("🗑", key=f"del_d_{i}"):
                                st.session_state.debts.pop(i); st.rerun()

        # ----------------------------------------------------------
        # 탭 4: 예상 지출
        # ----------------------------------------------------------

        # ----------------------------------------------------------
        # 탭 5: 예상 지출
        # ----------------------------------------------------------
        with tabs[4]:
            st.subheader("은퇴 후 월 예상 지출")
            living    = _sl("기본 생활비", 0, 2000, st.session_state.get("inp_living", 0), 10, "inp_living", "won") * 10000
            medical   = _sl("의료비", 0, 1000, st.session_state.get("inp_medical", 0), 10, "inp_medical", "won") * 10000
            leisure   = _sl("여가/취미", 0, 1000, st.session_state.get("inp_leisure", 0), 10, "inp_leisure", "won") * 10000
            family    = _sl("자녀/부모 지원", 0, 1000, st.session_state.get("inp_family", 0), 10, "inp_family", "won") * 10000
            insurance = _sl("보험료", 0, 1000, st.session_state.get("inp_insurance", 0), 10, "inp_insurance", "won") * 10000
            other     = st.number_input("기타 (만원)", min_value=0, max_value=1000, step=10, key="inp_other") * 10000
            total_monthly = living + medical + leisure + family + insurance + other
            st.metric("월 지출 합계", fmt_won(total_monthly))

        # ----------------------------------------------------------
        # 탭 5: 컨설팅
        # ----------------------------------------------------------
        with tabs[5]:
            st.subheader("🎯 은퇴 재원마련 컨설팅")

            # 탭 진입 시 관리자 상태 1회 갱신
            if st.session_state.token and not st.session_state.get('_admin_checked'):
                _am_resp, _am_err = call_api("/auth/me", method="GET")
                if not _am_err and _am_resp:
                    _new_is_admin = bool(_am_resp.get('is_admin', False))
                    if _new_is_admin != st.session_state.get('is_admin', False):
                        st.session_state.is_admin = _new_is_admin
                        st.session_state['_admin_checked'] = True
                        st.rerun()
                st.session_state['_admin_checked'] = True

            # 관리자 상태 표시 (진단용 — 확인 후 제거 가능)
            if st.session_state.get('is_admin'):
                st.success("🔑 관리자 모드 — 분석 실행 후 저장 버튼이 나타납니다.")
            _cons_result = st.session_state.get('analysis_result')
            if not _cons_result:
                st.info("💡 내 정보를 입력하고 저장하면 맞춤 컨설팅을 확인할 수 있습니다.")
            else:
                result = _cons_result
                cf     = result.get('현금흐름', {})
                assets = result.get('자산현황', {})
                # ── 시나리오 비교 (GOOD / BEST 저장 & 비교표) ───────────
                _retire_age_cur = result.get('사용자정보', {}).get('희망은퇴연령', 0)
                def _asset_num(v):
                    if isinstance(v, dict):
                        return int(v.get('합계', v.get('시세_합계', 0)))
                    if isinstance(v, str):
                        try:
                            return int(float(v))
                        except (ValueError, TypeError):
                            return 0
                    return int(v or 0)

                _pension_analysis = result.get('연금분석', {})
                _nps_monthly = int(next(
                    (info.get('월수령액_조정', info.get('세후월수령액', 0))
                     for name, info in _pension_analysis.items() if '국민연금' in name),
                    0
                ))
                _private_monthly = int(sum(
                    info.get('월수령액_조정', info.get('세후월수령액', 0))
                    for name, info in _pension_analysis.items() if '국민연금' not in name
                ))
                _pension_total = _nps_monthly + _private_monthly

                # 연금 적립금 / 수익률 / 그룹별 상세 계산
                _pensions_ss = st.session_state.get('pensions', [])

                # ── 나이·기간 계산 (비교표 전체 공용) ───────────────────────
                import datetime as _dt_ages
                _cur_age_u    = (_dt_ages.date.today().year
                                 - st.session_state.get('inp_birth_year',
                                   _dt_ages.date.today().year - 50))
                _yrs_to_ret_u = max(0, _retire_age_cur - _cur_age_u)
                _yrs_to_nps_u = max(0, 65 - _cur_age_u)   # 국민연금 65세 개시

                def _pv_for_user(pmt, rate_pct, yrs, payout_yr=20):
                    """월수령액 → 수령 시점 PV → 사용자 현재 나이 기준 PV"""
                    if pmt <= 0 or yrs < 0:
                        return 0
                    r_a = max(rate_pct / 100, 0.001)
                    r   = r_a / 12
                    n   = int(payout_yr * 12)
                    pv_s = pmt * (1 - (1 + r) ** (-n)) / r
                    return int(pv_s / (1 + r_a) ** yrs)

                def _pen_pv_total(pen_dict, yrs_to_ret):
                    """연금 그룹 딕셔너리 → 현재가치 적립금 합산 (시나리오별 은퇴연령 반영)"""
                    return sum(
                        _pv_for_user(
                            pen_dict.get(_sg, {}).get('월수령액', 0),
                            pen_dict.get(_sg, {}).get('수익률', 4.0),
                            _yrs_to_nps_u if _sg == '국민연금' else yrs_to_ret,
                        )
                        for _sg in ['국민연금', '퇴직연금', 'IRP', '개인연금', '기타']
                    )

                def _pen_adj(pen_dict, yrs_to_ret):
                    """저장된 연금 딕셔너리의 적립금을 현재가치로 교체 (시나리오별 은퇴연령 반영)"""
                    out = {}
                    for _sg in ['국민연금', '퇴직연금', 'IRP', '개인연금', '기타']:
                        _gd  = pen_dict.get(_sg, {})
                        _yrs = _yrs_to_nps_u if _sg == '국민연금' else yrs_to_ret
                        out[_sg] = {**_gd,
                                    '적립금': _pv_for_user(_gd.get('월수령액', 0),
                                                           _gd.get('수익률', 4.0), _yrs)}
                    return out

                def _pension_group(pt):
                    if pt == '국민연금':                      return '국민연금'
                    if pt in ('퇴직연금DB', '퇴직연금DC'):    return '퇴직연금'
                    if pt == 'IRP':                           return 'IRP'
                    if pt in ('연금저축', '개인연금'):         return '개인연금'
                    return '기타'

                _GRP_ORDER = ['국민연금', '퇴직연금', 'IRP', '개인연금', '기타']
                _grp_bal  = {g: 0  for g in _GRP_ORDER}
                _grp_wt   = {g: [] for g in _GRP_ORDER}
                _grp_mon  = {g: 0  for g in _GRP_ORDER}

                for _pp in _pensions_ss:
                    _g = _pension_group(_pp.get('pension_type', ''))
                    _grp_bal[_g] += int(_pp.get('current_balance', 0))
                    _rt = _pp.get('annual_return_rate', 0)
                    if _rt > 0:
                        _grp_wt[_g].append((_pp.get('current_balance', 0), _rt))

                for _pname, _pinfo in _pension_analysis.items():
                    _mon = int(_pinfo.get('월수령액_조정', _pinfo.get('세후월수령액', 0)))
                    _pp_m = next((p for p in _pensions_ss if p.get('name') == _pname), None)
                    _pt_m = _pp_m.get('pension_type', '') if _pp_m else _pname
                    _grp_mon[_pension_group(_pt_m)] += _mon

                _pension_by_group = {}
                for _g in _GRP_ORDER:
                    _b      = _grp_bal[_g]
                    _wl     = _grp_wt[_g]
                    _tot_wb = sum(wb for wb, _ in _wl)
                    _avg_r  = round(sum(wb * wr for wb, wr in _wl) / _tot_wb * 100, 1) if _tot_wb > 0 else 0.0
                    # 은퇴시점 잔액으로 저장 (현재잔액 × 복리 성장)
                    _r_dec  = max(_avg_r / 100, 0.001)
                    _yrs_g  = _yrs_to_nps_u if _g == '국민연금' else _yrs_to_ret_u
                    _ret_b  = int(_b * (1 + _r_dec) ** _yrs_g)
                    _pension_by_group[_g] = {'적립금': _ret_b, '월수령액': _grp_mon[_g], '수익률': _avg_r}

                # 비교표 표시: 월수령액 기준 현재가치 역산 (STANDARD 방식과 동일)
                _pension_bal_total = _pen_pv_total(_pension_by_group, _yrs_to_ret_u)
                _bal_for_rate = [(p.get('current_balance', 0), p.get('annual_return_rate', 0))
                                 for p in _pensions_ss if p.get('current_balance', 0) > 0]
                if _bal_for_rate:
                    _tot_b = sum(b for b, _ in _bal_for_rate)
                    _pension_avg_return = round(sum(b * r for b, r in _bal_for_rate) / _tot_b * 100, 1)
                else:
                    _rates_only = [p.get('annual_return_rate', 0) for p in _pensions_ss if p.get('annual_return_rate', 0) > 0]
                    _pension_avg_return = round(sum(_rates_only) / len(_rates_only) * 100, 1) if _rates_only else 0.0

                _snap_payload = {
                    'label': '',
                    'retire_age':      int(_retire_age_cur),
                    'monthly_income':  int(cf.get('월수입', 0)),
                    'monthly_expense': int(cf.get('월지출_합계', 0)),
                    'monthly_surplus': int(cf.get('월잉여(부족)', 0)),
                    'total_assets':    int(assets.get('순자산', 0)),
                    'detail': {
                        '총자산':        int(assets.get('총자산', 0)),
                        '총부채':        int(assets.get('총부채', 0)),
                        '금융자산':      _asset_num(assets.get('금융자산', 0)),
                        '부동산':        _asset_num(assets.get('부동산', 0)),
                        '국민연금':      _nps_monthly,
                        '사적연금':      _private_monthly,
                        '연금합계':      _pension_total,
                        '연금_총적립금': _pension_bal_total,
                        '연금_평균수익률': _pension_avg_return,
                        '연금상세': _pension_by_group,
                    },
                }
                if st.session_state.get('is_admin'):
                    _sc_b1, _sc_b2, _sc_b3 = st.columns(3)
                    with _sc_b1:
                        if st.button("📌 GOOD CASE 저장", key='btn_save_good', help="현재 분석 결과를 GOOD CASE로 저장", width='stretch'):
                            _p = {**_snap_payload, 'label': 'GOOD'}
                            _sr, _se = call_api("/scenarios", _p)
                            if _se:
                                st.error(f"저장 실패: {_se}")
                            else:
                                st.session_state._sc_dirty = True
                                st.toast("✅ GOOD CASE 저장 완료!")
                                st.rerun()
                    with _sc_b2:
                        if st.button("🏆 BEST CASE 저장", key='btn_save_best', help="현재 분석 결과를 BEST CASE로 저장", width='stretch'):
                            _p = {**_snap_payload, 'label': 'BEST'}
                            _sr, _se = call_api("/scenarios", _p)
                            if _se:
                                st.error(f"저장 실패: {_se}")
                            else:
                                st.session_state._sc_dirty = True
                                st.toast("✅ BEST CASE 저장 완료!")
                                st.rerun()
                    with _sc_b3:
                        if st.button("🇰🇷 우리나라 평균 저장", key='btn_save_std', help="현재 분석 결과를 우리나라 평균(STANDARD)으로 저장", width='stretch'):
                            _p = {**_snap_payload, 'label': 'STANDARD'}
                            _sr, _se = call_api("/scenarios", _p)
                            if _se:
                                st.error(f"저장 실패: {_se}")
                            else:
                                st.session_state._sc_dirty = True
                                st.toast("✅ 우리나라 평균(STANDARD) 저장 완료!")
                                st.rerun()

                # 저장된 시나리오 불러와 비교표 — session_state 캐시로 매 rerun마다 HTTP 요청 방지
                if '_sc_cache' not in st.session_state or st.session_state.pop('_sc_dirty', False):
                    _snaps, _snaps_err = call_api("/scenarios", method="GET")
                    st.session_state._sc_cache = (_snaps, _snaps_err)
                _snaps, _snaps_err = st.session_state._sc_cache
                _snap_map = {s['label']: s for s in (_snaps or [])} if not _snaps_err else {}
                st.divider()
                st.markdown("#### 📊 시나리오 비교")

                # STANDARD: DB에서 로드, 없으면 기본값 사용
                _std = _snap_map.get('STANDARD')
                def _std_val(key, default):
                    if _std:
                        d = _std.get('detail', {})
                        v = d.get(key)
                        return v if v is not None else default
                    return default

                # ── 우리나라 평균 연금: 사용자 맞춤 현재가치 역산 ──────────
                # (_pv_for_user, _yrs_to_ret_u, _yrs_to_nps_u 는 위에서 정의됨)
                # STANDARD DB의 연금상세(월수령액·수익률)를 기준으로 사용자 맞춤 적립금 계산
                _std_pen_raw = (_std or {}).get('detail', {}).get('연금상세') or {}
                _std_pen_fb = {   # DB 없을 때 기본값
                    '국민연금': {'월수령액': 660_000, '수익률': 4.0},
                    '퇴직연금': {'월수령액': 448_000, '수익률': 4.0},
                    'IRP':      {'월수령액': 135_000, '수익률': 4.0},
                    '개인연금': {'월수령액': 191_000, '수익률': 3.5},
                    '기타':     {'월수령액':       0, '수익률': 0.0},
                }
                _std_pen = {}
                _yrs_to_ret_std = max(0, ((_std or {}).get('retire_age') or _retire_age_cur) - _cur_age_u)
                for _sg in ['국민연금', '퇴직연금', 'IRP', '개인연금', '기타']:
                    _rg  = _std_pen_raw.get(_sg) or _std_pen_fb.get(_sg, {})
                    _pmt = _rg.get('월수령액', 0)
                    _rte = _rg.get('수익률', 4.0)
                    _yrs = _yrs_to_nps_u if _sg == '국민연금' else _yrs_to_ret_std
                    _std_pen[_sg] = {
                        '적립금':   _pv_for_user(_pmt, _rte, _yrs),
                        '월수령액': _pmt,
                        '수익률':   _rte,
                    }
                _std_total_bal = sum(_std_pen[g]['적립금'] for g in _std_pen)

                _KR_AVG = {
                    '은퇴연령':         f"{_std['retire_age']}세" if _std else '62세',
                    '월 수입':          fmt_won(_std['monthly_income'] if _std else 1_200_000),
                    '월 지출':          fmt_won(_std['monthly_expense'] if _std else 2_700_000),
                    '월 잉여':          fmt_won(_std['monthly_surplus'] if _std else -1_500_000),
                    '순자산':           fmt_won(_std['total_assets'] if _std else 370_000_000),
                    '금융자산':         fmt_won(_std_val('금융자산', 150_000_000)),
                    '부동산':           fmt_won(_std_val('부동산', 220_000_000)),
                    '국민연금(월)':     fmt_won(_std_val('국민연금', 650_000)),
                    '사적연금(월)':     fmt_won(_std_val('사적연금', 300_000)),
                    '연금합계(월)':     fmt_won(_std_val('연금합계', 950_000)),
                    '연금 적립금':      fmt_won(_std_total_bal),        # 사용자 맞춤 계산
                    '연금 평균수익률':  f"{_std_val('연금_평균수익률', 4.0)}%",
                }

                _cols_hdr = ['항목', '현재 상황', '🇰🇷 우리나라 평균']
                _cols_data = {
                    '은퇴연령':        [f"{_retire_age_cur}세",                          _KR_AVG['은퇴연령']],
                    '월 수입':         [fmt_won(cf.get('월수입', 0)),                    _KR_AVG['월 수입']],
                    '월 지출':         [fmt_won(cf.get('월지출_합계', 0)),               _KR_AVG['월 지출']],
                    '월 잉여':         [fmt_won(cf.get('월잉여(부족)', 0)),              _KR_AVG['월 잉여']],
                    '순자산':          [fmt_won(assets.get('순자산', 0)),                _KR_AVG['순자산']],
                    '금융자산':        [fmt_won(_asset_num(assets.get('금융자산', 0))),  _KR_AVG['금융자산']],
                    '부동산':          [fmt_won(_asset_num(assets.get('부동산', 0))),    _KR_AVG['부동산']],
                    '국민연금(월)':    [fmt_won(_nps_monthly),                          _KR_AVG['국민연금(월)']],
                    '사적연금(월)':    [fmt_won(_private_monthly),                      _KR_AVG['사적연금(월)']],
                    '연금합계(월)':    [fmt_won(_pension_total),                        _KR_AVG['연금합계(월)']],
                    '연금 적립금':     [fmt_won(_pension_bal_total),                    _KR_AVG['연금 적립금']],
                    '연금 평균수익률': [f"{_pension_avg_return}%",                      _KR_AVG['연금 평균수익률']],
                }
                for _lbl in ['GOOD', 'BEST']:
                    _emoji = '📌 GOOD CASE' if _lbl == 'GOOD' else '🏆 BEST CASE'
                    if _lbl in _snap_map:
                        _s = _snap_map[_lbl]
                        _cols_hdr.append(_emoji)
                        _cols_data['은퇴연령'].append(f"{_s['retire_age']}세")
                        _cols_data['월 수입'].append(fmt_won(_s['monthly_income']))
                        _cols_data['월 지출'].append(fmt_won(_s['monthly_expense']))
                        _cols_data['월 잉여'].append(fmt_won(_s['monthly_surplus']))
                        _cols_data['순자산'].append(fmt_won(_s['total_assets']))
                        _cols_data['금융자산'].append(fmt_won(_asset_num(_s['detail'].get('금융자산', 0))))
                        _cols_data['부동산'].append(fmt_won(_asset_num(_s['detail'].get('부동산', 0))))
                        _cols_data['국민연금(월)'].append(fmt_won(_s['detail'].get('국민연금', 0)))
                        _cols_data['사적연금(월)'].append(fmt_won(_s['detail'].get('사적연금', 0)))
                        _cols_data['연금합계(월)'].append(fmt_won(_s['detail'].get('연금합계', 0)))
                        _s_yrs_ret = max(0, _s.get('retire_age', _retire_age_cur) - _cur_age_u)
                        _s_pv = _pen_pv_total(_s.get('detail', {}).get('연금상세', {}), _s_yrs_ret)
                        _cols_data['연금 적립금'].append(fmt_won(_s_pv))
                        _cols_data['연금 평균수익률'].append(f"{_s['detail'].get('연금_평균수익률', 0)}%")

                _df_cmp = pd.DataFrame(
                    [[k] + v for k, v in _cols_data.items()],
                    columns=_cols_hdr,
                )
                st.dataframe(_df_cmp, hide_index=True, width='stretch')

                # ── 시나리오 비교 그래프 ────────────────────────────────
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots

                _lifespan_g = int(_cons_result.get('사용자정보', {}).get('기대수명', 90))

                # 공통 팔레트 — 현재/STANDARD/GOOD/BEST
                _SC_COLORS = {
                    '현재 (나)':      '#1565c0',
                    '🇰🇷 우리나라 평균': '#78909c',
                    '📌 GOOD':        '#66bb6a',
                    '🏆 BEST':        '#ffa726',
                }

                # ── 나이별 순자산 시뮬레이션 ──────────────────────────
                def _asset_sim(start, m_inc, m_exp, r_age, lifespan, ret=0.04, inf=0.025):
                    ages, vals = [], []
                    a = start
                    for i, age in enumerate(range(r_age, lifespan + 1)):
                        ages.append(age)
                        vals.append(round(a / 1e8, 2))   # 억원
                        net = (m_inc - m_exp * (1 + inf) ** i) * 12
                        a = a * (1 + ret) + net
                    return ages, vals

                _chart_series = {}
                # 현재 상황
                _chart_series['현재 (나)'] = _asset_sim(
                    assets.get('순자산', 0),
                    cf.get('월수입', 0),
                    cf.get('월지출_합계', 0),
                    _retire_age_cur,
                    _lifespan_g,
                )
                # 저장된 시나리오
                for _lbl, _emoji in [('STANDARD', '🇰🇷 우리나라 평균'), ('GOOD', '📌 GOOD'), ('BEST', '🏆 BEST')]:
                    if _lbl in _snap_map:
                        _sv = _snap_map[_lbl]
                        _chart_series[_emoji] = _asset_sim(
                            _sv['total_assets'],
                            _sv['monthly_income'],
                            _sv['monthly_expense'],
                            _sv['retire_age'],
                            _lifespan_g,
                        )

                with st.expander("📈 시나리오 비교 그래프", expanded=True):
                    _gtab1, _gtab2, _gtab3, _gtab4 = st.tabs([
                        "💰 자산 구성", "📊 수입/지출 구성", "📈 나이별 수입/지출", "🎯 종합 레이더"
                    ])

                    # ── 그래프 1: 자산 구성 비교 ──────────────────────
                    with _gtab1:
                        _bar_labels, _bar_re, _bar_fin, _bar_pen = [], [], [], []
                        _bar_labels.append('현재 (나)')
                        _bar_re.append(round(_asset_num(assets.get('부동산', 0)) / 1e8, 1))
                        _bar_fin.append(round(_asset_num(assets.get('금융자산', 0)) / 1e8, 1))
                        _bar_pen.append(round(_pension_bal_total / 1e8, 1))
                        for _lbl, _emoji in [('STANDARD','🇰🇷 평균'), ('GOOD','📌 GOOD'), ('BEST','🏆 BEST')]:
                            if _lbl in _snap_map:
                                _sv = _snap_map[_lbl]
                                _bar_labels.append(_emoji)
                                _bar_re.append(round(_asset_num(_sv['detail'].get('부동산', 0)) / 1e8, 1))
                                _bar_fin.append(round(_asset_num(_sv['detail'].get('금융자산', 0)) / 1e8, 1))
                                _s_pr = _pen_pv_total(_sv.get('detail', {}).get('연금상세', {}),
                                                      max(0, _sv.get('retire_age', _retire_age_cur) - _cur_age_u))
                                _bar_pen.append(round(_s_pr / 1e8, 1))

                        _fig1 = go.Figure()
                        _fig1.add_trace(go.Bar(name='부동산', x=_bar_labels, y=_bar_re,
                                               marker=dict(color='rgba(239,83,80,0.2)',
                                                           line=dict(color='rgba(239,83,80,0.85)', width=1.5)),
                                               hovertemplate='%{x}<br>부동산: <b>%{y:.1f}억</b><extra></extra>'))
                        _fig1.add_trace(go.Bar(name='금융자산', x=_bar_labels, y=_bar_fin,
                                               marker=dict(color='rgba(66,165,245,0.2)',
                                                           line=dict(color='rgba(66,165,245,0.85)', width=1.5)),
                                               hovertemplate='%{x}<br>금융자산: <b>%{y:.1f}억</b><extra></extra>'))
                        _fig1.add_trace(go.Bar(name='연금 적립금(PV)', x=_bar_labels, y=_bar_pen,
                                               marker=dict(color='rgba(102,187,106,0.2)',
                                                           line=dict(color='rgba(102,187,106,0.85)', width=1.5)),
                                               hovertemplate='%{x}<br>연금PV: <b>%{y:.1f}억</b><extra></extra>'))
                        _fig1.update_layout(
                            barmode='stack',
                            title=dict(text="시나리오별 자산 구성 비교 (억원)", font=dict(size=16, color='#fff')),
                            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', color='#ccc'),
                            yaxis=dict(title="금액 (억원)", gridcolor='rgba(255,255,255,0.1)', color='#ccc'),
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#ddd'),
                            legend=dict(orientation='h', yanchor='bottom', y=1.02, bgcolor='rgba(0,0,0,0)'),
                            margin=dict(l=10, r=10, t=60, b=40),
                        )
                        st.plotly_chart(_fig1, use_container_width=True)

                    # ── 그래프 2: 수입/지출 구성 (스냅샷 막대) ──────────
                    with _gtab2:
                        _cf_labels, _cf_inc, _cf_exp, _cf_sur = [], [], [], []
                        def _add_cf(label, inc, exp):
                            _cf_labels.append(label)
                            _cf_inc.append(round(inc / 10000))
                            _cf_exp.append(round(exp / 10000))
                            _cf_sur.append(round((inc - exp) / 10000))
                        _add_cf('현재 (나)', cf.get('월수입', 0), cf.get('월지출_합계', 0))
                        for _lbl, _emoji in [('STANDARD','🇰🇷 평균'), ('GOOD','📌 GOOD'), ('BEST','🏆 BEST')]:
                            if _lbl in _snap_map:
                                _sv = _snap_map[_lbl]
                                _add_cf(_emoji, _sv['monthly_income'], _sv['monthly_expense'])

                        _fig2 = go.Figure()
                        _fig2.add_trace(go.Bar(
                            name='월 수입', x=_cf_labels, y=_cf_inc,
                            marker=dict(color='rgba(66,165,245,0.2)',
                                        line=dict(color='rgba(66,165,245,0.9)', width=1.5)),
                            hovertemplate='%{x}<br>월수입: <b>%{y:,}만원</b><extra></extra>',
                        ))
                        _fig2.add_trace(go.Bar(
                            name='월 지출', x=_cf_labels, y=_cf_exp,
                            marker=dict(color='rgba(239,83,80,0.2)',
                                        line=dict(color='rgba(239,83,80,0.9)', width=1.5)),
                            hovertemplate='%{x}<br>월지출: <b>%{y:,}만원</b><extra></extra>',
                        ))
                        _fig2.add_trace(go.Scatter(
                            name='월 잉여(+)/부족(-)', x=_cf_labels, y=_cf_sur,
                            mode='lines+markers+text',
                            text=[f"{v:+,}만" for v in _cf_sur],
                            textposition='top center',
                            textfont=dict(size=12, color='#ffd54f'),
                            line=dict(color='#ffd54f', width=2, dash='dot'),
                            marker=dict(size=8, color='#ffd54f', line=dict(color='#fff', width=1)),
                            hovertemplate='%{x}<br>잉여: <b>%{y:+,}만원</b><extra></extra>',
                        ))
                        _fig2.add_hline(y=0, line_dash='dash', line_color='rgba(255,255,255,0.3)')
                        _fig2.update_layout(
                            barmode='group',
                            title=dict(text="시나리오별 월 수입 / 지출 비교 (만원)", font=dict(size=16, color='#fff')),
                            xaxis=dict(gridcolor='rgba(255,255,255,0.08)', color='#ccc'),
                            yaxis=dict(title="금액 (만원)", gridcolor='rgba(255,255,255,0.1)', color='#ccc'),
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#ddd'),
                            legend=dict(orientation='h', yanchor='bottom', y=1.02, bgcolor='rgba(0,0,0,0)'),
                            margin=dict(l=10, r=10, t=60, b=40),
                            hovermode='x unified',
                        )
                        st.plotly_chart(_fig2, use_container_width=True)

                    # ── 그래프 3: 나이별 월수입·월지출 라인 ───────────
                    with _gtab3:
                        _inf_rate = st.session_state.get('inp_inflation', 2.5) / 100

                        # 시나리오별 나이→(수입,지출) 데이터 생성
                        def _cf_by_age(m_inc, m_exp, r_age, lifespan, inf=_inf_rate):
                            ages, incs, exps = [], [], []
                            for i, age in enumerate(range(r_age, lifespan + 1)):
                                ages.append(age)
                                incs.append(round(m_inc / 10000))          # 만원, 수입은 고정
                                exps.append(round(m_exp * (1 + inf) ** i / 10000))  # 물가상승 반영
                            return ages, incs, exps

                        # 현재(나): 실제 나이별수입 데이터 사용
                        _cage_rows_g = _cons_result.get('나이별수입', [])
                        _g_ages  = [r['나이'] for r in _cage_rows_g if r['나이'] >= _retire_age_cur]
                        _g_incs  = [round(max(0, r.get('월수입', 0) - r.get('월세금', 0)) / 10000)
                                    for r in _cage_rows_g if r['나이'] >= _retire_age_cur]
                        _g_base_exp = cf.get('월지출_합계', 0)
                        _g_exps  = [round(_g_base_exp * (1 + _inf_rate) ** i / 10000)
                                    for i, _ in enumerate(_g_ages)]

                        _fig1 = go.Figure()

                        # ── 현재(나) ──
                        if _g_ages:
                            _fig1.add_trace(go.Scatter(
                                x=_g_ages, y=_g_incs, name='수입 — 현재(나)',
                                mode='lines',
                                line=dict(color='#1565c0', width=2.5),
                                hovertemplate='%{x}세 수입: <b>%{y:,}만원</b><extra>현재(나)</extra>',
                            ))
                            _fig1.add_trace(go.Scatter(
                                x=_g_ages, y=_g_exps, name='지출 — 현재(나)',
                                mode='lines',
                                line=dict(color='#1565c0', width=2.5, dash='dot'),
                                hovertemplate='%{x}세 지출: <b>%{y:,}만원</b><extra>현재(나)</extra>',
                            ))
                            # 잉여/부족 영역
                            _g_sur = [inc - exp for inc, exp in zip(_g_incs, _g_exps)]
                            _fig1.add_trace(go.Scatter(
                                x=_g_ages + _g_ages[::-1],
                                y=[max(0, s) for s in _g_sur] + [0] * len(_g_ages),
                                fill='toself', mode='none', showlegend=False,
                                fillcolor='rgba(21,101,192,0.08)',
                                hoverinfo='skip',
                            ))

                        # ── 저장된 시나리오 ──
                        _sc_styles = {
                            'STANDARD': ('🇰🇷 평균',  '#78909c'),
                            'GOOD':     ('📌 GOOD',   '#66bb6a'),
                            'BEST':     ('🏆 BEST',   '#ffa726'),
                        }
                        for _lbl, (_emoji, _scol) in _sc_styles.items():
                            if _lbl not in _snap_map:
                                continue
                            _sv = _snap_map[_lbl]
                            _sa, _si, _se = _cf_by_age(
                                _sv['monthly_income'], _sv['monthly_expense'],
                                _sv['retire_age'], _lifespan_g,
                            )
                            _fig1.add_trace(go.Scatter(
                                x=_sa, y=_si, name=f'수입 — {_emoji}',
                                mode='lines',
                                line=dict(color=_scol, width=2),
                                hovertemplate='%{x}세 수입: <b>%{y:,}만원</b><extra>' + _emoji + '</extra>',
                            ))
                            _fig1.add_trace(go.Scatter(
                                x=_sa, y=_se, name=f'지출 — {_emoji}',
                                mode='lines',
                                line=dict(color=_scol, width=2, dash='dot'),
                                hovertemplate='%{x}세 지출: <b>%{y:,}만원</b><extra>' + _emoji + '</extra>',
                            ))

                        _fig1.add_hline(y=0, line_dash='dash',
                                        line_color='rgba(255,255,255,0.2)')
                        _fig1.update_layout(
                            title=dict(text="나이별 월 수입(실선) / 지출(점선) — 만원", font=dict(size=16, color='#fff')),
                            xaxis=dict(title="나이", tickmode='linear', dtick=5,
                                       gridcolor='rgba(255,255,255,0.08)', color='#ccc'),
                            yaxis=dict(title="금액 (만원)", gridcolor='rgba(255,255,255,0.1)', color='#ccc'),
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#ddd'),
                            legend=dict(orientation='h', yanchor='bottom', y=1.02,
                                        bgcolor='rgba(0,0,0,0)', font=dict(size=11)),
                            margin=dict(l=10, r=10, t=60, b=40),
                            hovermode='x unified',
                        )
                        st.plotly_chart(_fig1, use_container_width=True)

                    # ── 그래프 4: 종합 레이더 차트 ────────────────────
                    with _gtab4:
                        _r_cats = ['순자산<br>(억)', '월수입<br>(백만)', '월지출<br>(백만)', '연금합계<br>(월·만원)', '금융자산<br>(억)']
                        def _radar_vals(net, m_inc, m_exp, pen, fin):
                            return [round(net/1e8,1), round(m_inc/1e6,1), round(m_exp/1e6,1),
                                    round(pen/10000,1), round(fin/1e8,1)]

                        _r_data = {}
                        # 현재
                        _r_data['현재 (나)'] = _radar_vals(
                            assets.get('순자산', 0), cf.get('월수입',0), cf.get('월지출_합계',0),
                            _pension_total, _asset_num(assets.get('금융자산',0)),
                        )
                        for _lbl, _emoji in [('STANDARD','🇰🇷 평균'), ('GOOD','📌 GOOD'), ('BEST','🏆 BEST')]:
                            if _lbl in _snap_map:
                                _sv = _snap_map[_lbl]
                                _r_data[_emoji] = _radar_vals(
                                    _sv['total_assets'], _sv['monthly_income'], _sv['monthly_expense'],
                                    _sv['detail'].get('연금합계', 0), _asset_num(_sv['detail'].get('금융자산',0)),
                                )

                        # 정규화 (최대값 기준)
                        _r_maxes = [max((v[i] for v in _r_data.values()), default=1) or 1 for i in range(5)]

                        _fig3 = go.Figure()
                        for _sname, _rvals in _r_data.items():
                            _norm = [round(v / _r_maxes[i] * 100, 1) for i, v in enumerate(_rvals)]
                            _norm_closed = _norm + [_norm[0]]
                            _cats_closed = _r_cats + [_r_cats[0]]
                            _col = _SC_COLORS.get(_sname, '#aaaaaa')
                            _hover = '<br>'.join(
                                f"{_r_cats[i].replace('<br>', ' ')}: {_rvals[i]}" for i in range(5)
                            )
                            _h = _col.lstrip('#')
                            _fc = f'rgba({int(_h[0:2],16)},{int(_h[2:4],16)},{int(_h[4:6],16)},0.18)'
                            _fig3.add_trace(go.Scatterpolar(
                                r=_norm_closed, theta=_cats_closed,
                                fill='toself',
                                fillcolor=_fc,
                                name=_sname,
                                line=dict(color=_col, width=2),
                                hovertemplate=f"<b>{_sname}</b><br>{_hover}<extra></extra>",
                            ))
                        _fig3.update_layout(
                            polar=dict(
                                bgcolor='rgba(0,0,0,0)',
                                radialaxis=dict(visible=True, range=[0, 100],
                                                gridcolor='rgba(255,255,255,0.15)', color='#aaa',
                                                ticksuffix='%'),
                                angularaxis=dict(gridcolor='rgba(255,255,255,0.15)', color='#ccc'),
                            ),
                            title=dict(text="종합 지표 비교 (최대값 = 100%)", font=dict(size=16, color='#fff')),
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#ddd'),
                            legend=dict(orientation='h', yanchor='bottom', y=-0.15,
                                        bgcolor='rgba(0,0,0,0)'),
                            margin=dict(l=30, r=30, t=60, b=60),
                        )
                        st.plotly_chart(_fig3, use_container_width=True)

                # 연금 상세보기 (_std_pen 은 위에서 사용자 맞춤 계산 완료)
                with st.expander("📋 연금 상세보기", expanded=False):
                    _det_grps = ['국민연금', '퇴직연금', 'IRP', '개인연금', '기타']

                    # GOOD/BEST: 저장된 월수령액·수익률 기반으로 현재가치 역산 (시나리오별 은퇴연령 반영)
                    _good_det_raw  = _snap_map.get('GOOD', {}).get('detail', {}).get('연금상세', {})
                    _best_det_raw  = _snap_map.get('BEST', {}).get('detail', {}).get('연금상세', {})
                    _yrs_ret_good  = max(0, _snap_map.get('GOOD', {}).get('retire_age', _retire_age_cur) - _cur_age_u)
                    _yrs_ret_best  = max(0, _snap_map.get('BEST', {}).get('retire_age', _retire_age_cur) - _cur_age_u)
                    _user_pen_adj  = _pen_adj(_pension_by_group, _yrs_to_ret_u)
                    _good_det      = _pen_adj(_good_det_raw, _yrs_ret_good) if _good_det_raw else {}
                    _best_det      = _pen_adj(_best_det_raw, _yrs_ret_best) if _best_det_raw else {}

                    def _grp_val(d, grp, key, default=0):
                        return d.get(grp, {}).get(key, default)

                    def _fw(d, grp, key):
                        return fmt_won(_grp_val(d, grp, key)) if d else '-'

                    def _fr(d, grp):
                        if not d: return '-'
                        v = _grp_val(d, grp, '수익률')
                        return f"{v}%" if v else '-'

                    # 열 헤더: 현재 + 우리나라 평균 고정, GOOD/BEST는 저장된 경우에만
                    _det_hdr = ['연금 종류', '나 (현재)', '🇰🇷 우리나라 평균']
                    if 'GOOD' in _snap_map: _det_hdr.append('📌 GOOD')
                    if 'BEST' in _snap_map: _det_hdr.append('🏆 BEST')

                    def _det_row(grp, key, fmt_fn):
                        row = [grp,
                               fmt_fn(_user_pen_adj, grp, key),   # 현재 (PV)
                               fmt_fn(_std_pen, grp, key)]         # 우리나라 평균 (PV)
                        if 'GOOD' in _snap_map: row.append(fmt_fn(_good_det, grp, key))
                        if 'BEST' in _snap_map: row.append(fmt_fn(_best_det, grp, key))
                        return row

                    st.markdown("**적립금 현황** (현가평가연금액)")
                    st.dataframe(
                        pd.DataFrame(
                            [_det_row(_g, '적립금', _fw) for _g in _det_grps],
                            columns=_det_hdr,
                        ),
                        hide_index=True, width='stretch',
                    )

                    st.markdown("**예상 월수령액** (은퇴 후 수령액)")
                    st.dataframe(
                        pd.DataFrame(
                            [_det_row(_g, '월수령액', _fw) for _g in _det_grps],
                            columns=_det_hdr,
                        ),
                        hide_index=True, width='stretch',
                    )

                    st.markdown("**연 수익률**")
                    _det_hdr_rt = ['연금 종류', '나 (현재)', '🇰🇷 우리나라 평균']
                    if 'GOOD' in _snap_map: _det_hdr_rt.append('📌 GOOD')
                    if 'BEST' in _snap_map: _det_hdr_rt.append('🏆 BEST')
                    _rows_rt = []
                    for _g in _det_grps:
                        _v = _grp_val(_pension_by_group, _g, '수익률')
                        _row_rt = [_g, f"{_v}%" if _v else '-', _fr(_std_pen, _g)]
                        if 'GOOD' in _snap_map: _row_rt.append(_fr(_good_det_raw, _g))
                        if 'BEST' in _snap_map: _row_rt.append(_fr(_best_det_raw, _g))
                        _rows_rt.append(_row_rt)
                    st.dataframe(pd.DataFrame(_rows_rt, columns=_det_hdr_rt),
                                 hide_index=True, width='stretch')

                if st.session_state.get('is_admin'):
                    with st.expander("🗑️ 시나리오 삭제", expanded=False):
                        _del_c1, _del_c2, _del_c3 = st.columns(3)
                        with _del_c1:
                            if 'GOOD' in _snap_map and st.button("GOOD 삭제", key='del_good'):
                                call_api("/scenarios/GOOD", method="DELETE")
                                st.session_state._sc_dirty = True
                                st.rerun()
                        with _del_c2:
                            if 'BEST' in _snap_map and st.button("BEST 삭제", key='del_best'):
                                call_api("/scenarios/BEST", method="DELETE")
                                st.session_state._sc_dirty = True
                                st.rerun()
                        with _del_c3:
                            if 'STANDARD' in _snap_map and st.button("STANDARD 삭제", key='del_std'):
                                call_api("/scenarios/STANDARD", method="DELETE")
                                st.session_state._sc_dirty = True
                                st.rerun()


                import datetime as _dt_mod

                _ss = st.session_state
                _ccf  = _cons_result.get('현금흐름', {})
                _cage_rows = _cons_result.get('나이별수입', [])
                _cage_map  = {r['나이']: r for r in _cage_rows}

                _cur_year  = _dt_mod.date.today().year
                _birth_yr  = _ss.get('inp_birth_year', 1971)
                _cur_age   = _cur_year - _birth_yr
                _user_info = _cons_result.get('사용자정보', {})
                _ret_age   = _user_info.get('희망은퇴연령', _ss.get('inp_retirement_age', 60))
                _lifespan  = _user_info.get('기대수명', _ss.get('inp_lifespan', 90))
                _cinf      = _ss.get('inp_inflation', 2.5) / 100
                _yrs_to_ret = max(0, _ret_age - _cur_age)
                _ret_yrs   = max(1, _lifespan - _ret_age)
                _base_exp  = _ccf.get('월지출_합계', 0)

                # 은퇴 후 연령별 월 부족액 합산 (명목 총액)
                _total_shortage = 0
                for _ca in range(_ret_age, _lifespan + 1):
                    _crow = _cage_map.get(_ca, {})
                    _cincome = max(0, _crow.get('월수입', 0) - _crow.get('월세금', 0))
                    _cexp    = _base_exp * ((1 + _cinf) ** (_ca - _ret_age))
                    _total_shortage += max(0, _cexp - _cincome) * 12

                # 현재 투자 가능 자산
                _fa_list   = _ss.get('financial_assets', [])
                _total_fa  = sum(a.get('amount', 0) for a in _fa_list)
                _re_list   = _ss.get('real_estates', [])
                _non_prim_equity = sum(
                    max(0, re.get('market_value', 0) - re.get('debt', 0))
                    for re in _re_list if not re.get('is_primary_residence', True)
                )
                _debt_list = _ss.get('debts', [])
                _high_int_debt = sum(
                    d.get('balance', 0) for d in _debt_list
                    if d.get('interest_rate', 0) > 0.05
                )

                # 헬퍼 함수
                def _fv_lump(pv, r, yrs):
                    return pv * ((1 + r) ** yrs) if yrs > 0 else pv

                def _fv_save(monthly, r, yrs):
                    if yrs <= 0 or monthly <= 0: return 0
                    if r <= 0: return monthly * 12 * yrs
                    mr = r / 12; n = int(yrs * 12)
                    return monthly * ((1 + mr) ** n - 1) / mr

                def _monthly_for_fv(target, r, yrs):
                    if target <= 0 or yrs <= 0: return 0
                    if r <= 0: return target / (12 * yrs)
                    mr = r / 12; n = int(yrs * 12)
                    factor = ((1 + mr) ** n - 1) / mr
                    return target / factor if factor > 0 else 0

                # ── 1. 재원 진단 ────────────────────────────────
                st.markdown("#### 📋 은퇴 재원 진단")
                _d1, _d2, _d3 = st.columns(3)
                with _d1:
                    st.metric("은퇴까지 남은 기간", f"{_yrs_to_ret}년")
                with _d2:
                    st.metric("은퇴 후 생활 기간", f"{_ret_yrs}년")
                with _d3:
                    st.metric("현재 금융자산", fmt_won(_total_fa))

                _ret_row0  = _cage_map.get(_ret_age, {})
                _ret_inc0  = max(0, _ret_row0.get('월수입', 0) - _ret_row0.get('월세금', 0))
                _gap0      = max(0, _base_exp - _ret_inc0)

                if _total_shortage > 0:
                    st.error(
                        f"⚠️ **은퇴 후 총 예상 부족액 약 {fmt_won(int(_total_shortage))}** "
                        f"(은퇴 첫 해 월 {fmt_won(int(_gap0))} 부족 → 이후 매년 물가반영 증가)"
                    )
                else:
                    st.success("✅ 현재 수입원으로 은퇴 후 생활비를 충당할 수 있습니다. 더 적극적인 자산 성장 전략을 검토해보세요.")

                if _high_int_debt > 0:
                    st.warning(f"💳 고금리 부채(5% 초과) **{fmt_won(int(_high_int_debt))}** 가 있습니다. 투자 전 상환 우선 검토를 권장합니다.")

                st.divider()

                # ── 2. 투자 시나리오 시뮬레이션 ─────────────────
                st.markdown("#### 📊 투자 시나리오 시뮬레이션")
                st.caption("매월 일정 금액을 은퇴 전까지 투자했을 때 은퇴 시점 예상 적립금을 비교합니다.")

                _sim_monthly = _sl("월 추가 투자액", 10, 500,
                    st.session_state.get("cons_monthly_invest", 50), 10, "cons_monthly_invest", "won") * 10000

                _scenarios = [
                    {"name": "안정형",  "r": 0.03, "icon": "🏦", "color": "#1565c0",
                     "desc": "예적금·국채·MMF", "risk": "낮음"},
                    {"name": "균형형",  "r": 0.05, "icon": "⚖️", "color": "#2e7d32",
                     "desc": "ETF + 채권 혼합", "risk": "중간"},
                    {"name": "성장형",  "r": 0.07, "icon": "📈", "color": "#e65100",
                     "desc": "주식ETF·리츠 중심", "risk": "높음"},
                    {"name": "공격형",  "r": 0.10, "icon": "🚀", "color": "#b71c1c",
                     "desc": "성장주·대체투자 포함", "risk": "매우 높음"},
                ]

                _sc_cols = st.columns(4)
                for _sci, _sc in enumerate(_scenarios):
                    _fa_grown   = _fv_lump(_total_fa, _sc['r'], _yrs_to_ret)
                    _sv_grown   = _fv_save(_sim_monthly, _sc['r'], _yrs_to_ret)
                    _total_pot  = _fa_grown + _sv_grown
                    _remaining  = _total_shortage - _total_pot
                    _covers     = _remaining <= 0
                    _need_mo    = _monthly_for_fv(max(0, _total_shortage - _fv_lump(_total_fa, _sc['r'], _yrs_to_ret)), _sc['r'], _yrs_to_ret)
                    with _sc_cols[_sci]:
                        _bg = "#e8f5e9" if _covers else "#fff8e1"
                        st.markdown(f"""
<div style="border:1px solid {_sc['color']};border-radius:10px;padding:12px;background:{_bg};text-align:center;">
<div style="font-size:20px;">{_sc['icon']}</div>
<div style="font-weight:bold;color:{_sc['color']};font-size:15px;">{_sc['name']}</div>
<div style="font-size:11px;color:#555;margin:4px 0;">{_sc['desc']}<br>기대수익률 {_sc['r']*100:.0f}%</div>
<hr style="border:none;border-top:1px solid #ddd;margin:8px 0;">
<div style="font-size:12px;color:#555;">은퇴 시 적립금</div>
<div style="font-weight:bold;font-size:14px;">{fmt_won(int(_total_pot))}</div>
<div style="font-size:12px;color:#555;margin-top:6px;">{"✅ 부족액 커버 가능" if _covers else f"⚠️ 여전히 {fmt_won(int(_remaining))} 부족"}</div>
<div style="font-size:11px;color:#777;margin-top:4px;">{"" if _covers else f"필요 월 투자: {fmt_won(int(_need_mo))}"}</div>
<div style="font-size:11px;color:#888;margin-top:4px;">위험도: {_sc['risk']}</div>
</div>""", unsafe_allow_html=True)

                st.divider()

                # ── 3. 투자 유형별 가이드 ──────────────────────
                st.markdown("#### 💡 투자 유형별 가이드")

                with st.expander("📈 주식투자 — 장기 분산투자 (ETF 중심)", expanded=False):
                    st.markdown(f"""
**핵심 원칙:** 개별 종목보다 ETF로 분산, 장기 보유

| 상품 | 기대수익률 | 특징 |
|------|-----------|------|
| S&P500 ETF (VOO·IVV·TIGER 미국S&P500) | 연 7~10% | 미국 대형주 500개 분산, 50년 평균 연 10% |
| KOSPI200 ETF | 연 5~8% | 국내 대형주 분산 |
| 배당 ETF (SCHD·KODEX고배당) | 연 4~6% + 배당 | 배당 재투자로 복리 효과 |
| 글로벌 리츠 ETF | 연 5~7% | 부동산 간접투자, 배당 안정적 |

**은퇴까지 {_yrs_to_ret}년 → 장기투자에 유리한 시점**
적립식(DCA) 투자로 시장 타이밍 리스크 분산을 권장합니다.
ISA 계좌 + 연금저축 활용 시 세금 혜택(비과세·과세이연) 가능합니다.
""")

                with st.expander("🏠 부동산 투자 — 보유 자산 활용 전략", expanded=False):
                    _has_primary = any(re.get('is_primary_residence') for re in _re_list)
                    _has_rental  = any(re.get('monthly_rent_income', 0) > 0 for re in _re_list)
                    _primary_val = next((re.get('market_value', 0) for re in _re_list if re.get('is_primary_residence')), 0)
                    st.markdown(f"""
**현재 보유 부동산 현황:**
{'- 자가 보유 (' + fmt_won(_primary_val) + ') → **주택연금** 검토 가능' if _has_primary else '- 자가 없음 → 전세·월세 거주 중'}
{'- 임대수익 발생 중 → 꾸준한 현금흐름 확보' if _has_rental else '- 임대수익 없음'}

**부동산 투자 전략:**

| 전략 | 내용 | 적합 시기 |
|------|------|-----------|
| **주택연금** | 집을 담보로 사망 시까지 월 수령 | 은퇴 후 (55세↑) |
| **소형 아파트·오피스텔** | 임대수익 월 50~100만원 | 은퇴 전 적립기 |
| **리츠(REITs)** | 부동산 간접투자, 소액 가능 | 지금 당장 가능 |
| **상업용 부동산** | 높은 수익률, 공실 리스크 | 자금 충분 시 |

{'**💡 주택연금 예시:** 70세 기준 시가 5억 주택 → 월 약 120만원 수령 (종신)' if _has_primary and _primary_val >= 300_000_000 else ''}
""")

                with st.expander("🪙 코인·대체투자 — 고위험 고수익", expanded=False):
                    st.markdown(f"""
**코인(암호화폐) 투자 원칙:**

- ⚠️ **포트폴리오의 5~10% 이내** 배분 권장 (은퇴 자금 핵심 부분으로 부적합)
- 비트코인·이더리움 등 시가총액 상위 코인 중심으로 분산
- 장기 보유(HODL) 전략이 단기 트레이딩보다 위험 대비 유리
- 손실 가능성: -70~80%까지 하락 경험 있음 (2022년 코인 시장 기준)

**기타 대체투자:**

| 유형 | 기대수익 | 위험도 | 비고 |
|------|---------|--------|------|
| 비트코인 | 연 20~50% (변동폭 큼) | ★★★★★ | 소액·분산 |
| 금·원자재 ETF | 연 3~5% | ★★☆☆☆ | 인플레이션 헤지 |
| 사모펀드·VC | 연 10~15% | ★★★★☆ | 고액·장기 락업 |
| 스타트업 엔젤 | 수십 배 또는 전손 | ★★★★★ | 전문가 영역 |

**은퇴 자금의 핵심은 안정성입니다.** 코인은 여유 자금 일부로만 활용하세요.
""")

                with st.expander("🏦 안정형 투자 — 채권·예금·절세 계좌", expanded=False):
                    st.markdown(f"""
**절세 계좌 우선 활용 (세금 혜택이 가장 확실한 수익):**

| 계좌 | 연 납입한도 | 혜택 |
|------|-----------|------|
| **IRP** | 900만원 | 납입액의 13.2~16.5% 세액공제 |
| **연금저축** | 600만원 (IRP 합산 900만원) | 동일 세액공제, 투자 자유도 높음 |
| **ISA** | 2,000만원 | 수익 200~400만원 비과세 + 저율과세 |

**예시: 연 900만원 IRP/연금저축 납입 → 세액공제 약 {fmt_won(int(9_000_000 * 0.148))} 환급**

**채권 투자:**
- 국고채 (10년): 연 3~3.5%, 원금 보장에 준함
- 회사채 (AA등급): 연 4~5%, 신용 리스크 소량 존재
- 채권형 ETF: KOSEF국고채3년, TIGER 미국채10년

은퇴가 {_yrs_to_ret}년 남은 시점에서는 **주식 비중을 높이고** 은퇴 접근 시 점차 채권·예금 비중 확대를 권장합니다.
""")

                st.divider()

                # ── 4. 맞춤 포트폴리오 제안 ────────────────────
                st.markdown("#### 🗂️ 입력 자산 기반 맞춤 조언")

                _advice_items = []

                if _total_fa > 0:
                    _avg_fa_return = (
                        sum(a.get('amount', 0) * a.get('annual_return_rate', 0.03) for a in _fa_list)
                        / _total_fa if _total_fa > 0 else 0.03
                    )
                    if _avg_fa_return < 0.04:
                        _advice_items.append(
                            f"💰 **금융자산 {fmt_won(_total_fa)}의 평균 수익률이 "
                            f"{_avg_fa_return*100:.1f}%로 낮습니다.** "
                            "예금·적금 비중을 줄이고 ETF(연 5~7%) 리밸런싱을 검토하세요."
                        )
                    else:
                        _advice_items.append(
                            f"✅ 금융자산 {fmt_won(_total_fa)}, 평균 수익률 "
                            f"{_avg_fa_return*100:.1f}% — 양호한 수준입니다."
                        )

                if _non_prim_equity > 0:
                    _advice_items.append(
                        f"🏠 **비거주 부동산 순자산 {fmt_won(int(_non_prim_equity))}** 보유 중. "
                        "임대수익을 극대화하거나, 수익률이 낮으면 금융자산으로 전환도 검토하세요."
                    )

                if _has_primary and _primary_val >= 300_000_000 and _cur_age >= 50:
                    _advice_items.append(
                        f"🏡 자가 주택 ({fmt_won(_primary_val)}) 보유 — "
                        "은퇴 후 **주택연금**으로 안정적인 월 수입을 확보할 수 있습니다. "
                        "(55세 이상, 공시가격 12억 이하 가입 가능)"
                    )

                if _high_int_debt > 0:
                    _advice_items.append(
                        f"⚡ **고금리 부채 {fmt_won(int(_high_int_debt))}** 상환이 최우선입니다. "
                        "5% 이상 이자는 5% 투자수익을 내는 것과 동일 효과입니다."
                    )

                if _yrs_to_ret >= 10:
                    _advice_items.append(
                        f"⏳ 은퇴까지 **{_yrs_to_ret}년 이상** 남아 있어 "
                        "복리 효과를 최대한 활용할 수 있습니다. "
                        "성장형~균형형 포트폴리오가 적합합니다."
                    )
                elif _yrs_to_ret >= 5:
                    _advice_items.append(
                        f"⏰ 은퇴까지 **{_yrs_to_ret}년**, 포트폴리오를 서서히 "
                        "안정형으로 이동(주식→채권·예금 비중 확대)을 시작할 시점입니다."
                    )
                else:
                    _advice_items.append(
                        "🔔 은퇴가 5년 이내입니다. 지금부터는 원금 보호 중심으로 "
                        "포트폴리오 보수화를 권장합니다."
                    )

                if not _advice_items:
                    _advice_items.append("자산 정보를 입력하면 맞춤 조언을 제공합니다.")

                for _adv in _advice_items:
                    st.markdown(f"- {_adv}")

                st.caption("※ 본 컨설팅은 참고용 정보이며, 실제 투자 결정은 공인 재무설계사(CFP)와 상담하시기 바랍니다.")

        # ----------------------------------------------------------
        # 탭 6: 관리자 (is_admin=True 일 때만 탭 존재)
        # ----------------------------------------------------------
        if st.session_state.get('is_admin'):
            with tabs[6]:
                st.subheader("🔧 관리자 패널")

                _adm_tab1, _adm_tab2 = st.tabs(["👥 사용자 관리", "📊 시나리오 관리"])

                # ── 사용자 관리 ──────────────────────────────────────
                with _adm_tab1:
                    st.markdown("#### 전체 회원 목록")
                    if '_adm_users_cache' not in st.session_state or st.session_state.pop('_adm_users_dirty', False):
                        _users_resp, _users_err = call_api("/admin/users", method="GET")
                        st.session_state._adm_users_cache = (_users_resp, _users_err)
                    _users_resp, _users_err = st.session_state._adm_users_cache
                    if _users_err:
                        st.error(f"사용자 목록 조회 실패: {_users_err}")
                    elif _users_resp:
                        # 확인 대기 중인 user_id (session_state로 관리)
                        _pending_key = 'adm_pending_toggle_uid'
                        for _u in _users_resp:
                            _uid      = _u['id']
                            _is_adm   = _u.get('is_admin', False)
                            _ucol1, _ucol2, _ucol3, _ucol4, _ucol5 = st.columns([1, 4, 2, 2, 1])
                            with _ucol1:
                                st.write(f"**#{_uid}**")
                            with _ucol2:
                                st.write(_u['email'])
                            with _ucol3:
                                st.write(_u.get('name', ''))
                            with _ucol4:
                                if _is_adm:
                                    st.markdown(
                                        '<span style="display:inline-block;'
                                        'background:linear-gradient(135deg,#7b1fa2,#c62828);'
                                        'color:#fff;padding:3px 12px;border-radius:12px;'
                                        'font-size:13px;font-weight:700;">🔑 관리자</span>',
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(
                                        '<span style="display:inline-block;'
                                        'background:#455a64;color:#cfd8dc;'
                                        'padding:3px 12px;border-radius:12px;'
                                        'font-size:13px;">일반 사용자</span>',
                                        unsafe_allow_html=True,
                                    )
                            with _ucol5:
                                if st.button("변경", key=f"adm_toggle_{_uid}",
                                             help="관리자 권한 변경"):
                                    st.session_state[_pending_key] = _uid

                            # 이 사용자가 확인 대기 중이면 예/아니오 표시
                            if st.session_state.get(_pending_key) == _uid:
                                _new_role = "일반 사용자" if _is_adm else "관리자"
                                st.warning(
                                    f"**{_u['email']}** 님을 **{_new_role}**로 변경하시겠습니까?",
                                    icon="⚠️",
                                )
                                _yes_col, _no_col, _ = st.columns([1, 1, 5])
                                with _yes_col:
                                    if st.button("예", key=f"adm_yes_{_uid}", type="primary"):
                                        _tr, _te = call_api(
                                            f"/admin/users/{_uid}/toggle-admin",
                                            method="PUT",
                                        )
                                        del st.session_state[_pending_key]
                                        if _te:
                                            st.error(f"변경 실패: {_te}")
                                        else:
                                            _new_state = "관리자" if _tr.get('is_admin') else "일반 사용자"
                                            st.toast(f"✅ {_tr.get('email')} → {_new_state}")
                                            st.session_state._adm_users_dirty = True
                                        st.rerun()
                                with _no_col:
                                    if st.button("아니오", key=f"adm_no_{_uid}"):
                                        del st.session_state[_pending_key]
                                        st.rerun()

                # ── 시나리오 관리 ────────────────────────────────────
                with _adm_tab2:
                    st.markdown("#### STANDARD / GOOD / BEST 기준값 저장")
                    st.caption("분석 실행 없이 직접 수치를 입력하여 기준 시나리오를 저장할 수 있습니다.")

                    # 현재 DB 값 로드 — 컨설팅 탭과 동일한 캐시 사용
                    if '_sc_cache' not in st.session_state or st.session_state.pop('_sc_dirty', False):
                        _sc_list, _sc_err = call_api("/scenarios", method="GET")
                        st.session_state._sc_cache = (_sc_list, _sc_err)
                    _sc_list, _sc_err = st.session_state._sc_cache
                    _sc_db = {s['label']: s for s in (_sc_list or [])} if not _sc_err else {}

                    _sc_label_sel = st.selectbox(
                        "저장할 시나리오 선택",
                        ["STANDARD", "GOOD", "BEST"],
                        key="adm_sc_label",
                    )
                    _sc_cur = _sc_db.get(_sc_label_sel, {})
                    _sc_det = _sc_cur.get('detail', {})

                    with st.form("admin_scenario_form"):
                        _fc1, _fc2 = st.columns(2)
                        with _fc1:
                            _f_retire  = st.number_input("은퇴 연령",         value=int(_sc_cur.get('retire_age', 60)),            min_value=50, max_value=80, step=1)
                            _f_income  = st.number_input("월 수입 (원)",       value=int(_sc_cur.get('monthly_income', 0)),         min_value=0,  step=100_000)
                            _f_expense = st.number_input("월 지출 (원)",       value=int(_sc_cur.get('monthly_expense', 0)),        min_value=0,  step=100_000)
                            _f_surplus = st.number_input("월 잉여/부족 (원)",  value=int(_sc_cur.get('monthly_surplus', 0)),        step=100_000)
                            _f_net     = st.number_input("순자산 (원)",        value=int(_sc_cur.get('total_assets', 0)),           min_value=0,  step=1_000_000)
                        with _fc2:
                            _f_total   = st.number_input("총자산 (원)",        value=int(_sc_det.get('총자산', 0)),                 min_value=0,  step=1_000_000)
                            _f_debt    = st.number_input("총부채 (원)",        value=int(_sc_det.get('총부채', 0)),                 min_value=0,  step=1_000_000)
                            _f_fin     = st.number_input("금융자산 (원)",      value=int(_sc_det.get('금융자산', 0)),               min_value=0,  step=1_000_000)
                            _f_re      = st.number_input("부동산 (원)",        value=int(_sc_det.get('부동산', 0)),                 min_value=0,  step=1_000_000)
                            _f_nps     = st.number_input("국민연금 월수령액",  value=int(_sc_det.get('국민연금', 0)),               min_value=0,  step=10_000)
                            _f_priv    = st.number_input("사적연금 월수령액",  value=int(_sc_det.get('사적연금', 0)),               min_value=0,  step=10_000)

                        if st.form_submit_button(f"💾 {_sc_label_sel} 저장", type="primary"):
                            _sc_payload = {
                                "label":           _sc_label_sel,
                                "retire_age":      _f_retire,
                                "monthly_income":  _f_income,
                                "monthly_expense": _f_expense,
                                "monthly_surplus": _f_surplus,
                                "total_assets":    _f_net,
                                "detail": {
                                    "총자산":    _f_total,
                                    "총부채":    _f_debt,
                                    "금융자산":  _f_fin,
                                    "부동산":    _f_re,
                                    "국민연금":  _f_nps,
                                    "사적연금":  _f_priv,
                                    "연금합계":  _f_nps + _f_priv,
                                },
                            }
                            _sr2, _se2 = call_api("/scenarios", _sc_payload)
                            if _se2:
                                st.error(f"저장 실패: {_se2}")
                            else:
                                st.session_state._sc_dirty = True
                                st.success(f"✅ {_sc_label_sel} 저장 완료!")
                                st.rerun()

                    # 현재 DB 저장 현황 요약
                    if _sc_db:
                        st.divider()
                        st.markdown("**현재 저장된 기준 시나리오**")
                        _sc_rows = []
                        for _lbl in ["STANDARD", "GOOD", "BEST"]:
                            _s = _sc_db.get(_lbl)
                            if _s:
                                _sc_rows.append({
                                    "라벨":        _lbl,
                                    "은퇴연령":    f"{_s['retire_age']}세",
                                    "월수입":      fmt_won(_s['monthly_income']),
                                    "월지출":      fmt_won(_s['monthly_expense']),
                                    "순자산":      fmt_won(_s['total_assets']),
                                })
                        if _sc_rows:
                            st.dataframe(pd.DataFrame(_sc_rows), hide_index=True, width='stretch')

                        # 삭제 버튼
                        with st.expander("🗑️ 시나리오 삭제", expanded=False):
                            _dc1, _dc2, _dc3 = st.columns(3)
                            with _dc1:
                                if "GOOD" in _sc_db and st.button("GOOD 삭제", key="adm_del_good"):
                                    call_api("/scenarios/GOOD", method="DELETE")
                                    st.session_state._sc_dirty = True
                                    st.rerun()
                            with _dc2:
                                if "BEST" in _sc_db and st.button("BEST 삭제", key="adm_del_best"):
                                    call_api("/scenarios/BEST", method="DELETE")
                                    st.session_state._sc_dirty = True
                                    st.rerun()
                            with _dc3:
                                if "STANDARD" in _sc_db and st.button("STANDARD 삭제", key="adm_del_std"):
                                    call_api("/scenarios/STANDARD", method="DELETE")
                                    st.session_state._sc_dirty = True
                                    st.rerun()


    if not _is_onboarding:
        _save_col, _status_col = st.columns([2, 5])
        with _save_col:
            if st.button("💾 내 정보 저장", width='stretch'):
                _payload = _build_save_payload()
                _pid = st.session_state.profile_id
                if _pid and _pid != 0:
                    _r, _e = call_api(f"/profiles/{_pid}", _payload, method="PUT")
                else:
                    _r, _e = call_api("/profiles", _payload)
                if _e:
                    st.error(f"저장 실패: {_e}")
                else:
                    st.session_state.profile_id = _r.get('id', _pid)
                    with _status_col:
                        st.success("✅ 저장 완료! 분석 중...")
                    _run_analysis()
                    st.rerun()

    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        st.divider()

        # ── 온보딩: 평균 기준 데이터 요약 안내 ──────────────
        if st.session_state.get('onboarding_done'):
            with st.expander("ℹ️ 적용된 우리나라 평균 데이터 (클릭하여 확인)", expanded=False):
                st.markdown("""
| 항목 | 적용 평균값 | 비고 |
|---|---|---|
| 연봉 | **5,000만원** | 50대 직장인 평균 (통계청 2024) |
| 국민연금 | **65세부터 90만원/월** | 평균 수령액 기준 |
| 퇴직연금(DC) | **적립금 8,000만원** | 50대 중간값 기준 |
| IRP | **적립금 2,000만원** | 직장인 평균 |
| 금융자산 | **1억 5,000만원** | 예적금·펀드 기준 |
| 주택담보대출 | **잔액 1억 5천만원 / 월 70만원** | 50대 평균 부채 |
| 신용대출 | **잔액 2천만원 / 월 30만원** | 50대 평균 부채 |
| 월 생활비 | **270만원** | 은퇴부부 기준 (통계청) |
| 물가상승률 | **2.0%** | 한국 현행 CPI 기준 |
| 기대수명 | **85세** | 국민 평균 |
""")
                st.info("왼쪽 탭(기본정보·소득·연금·자산/부채·지출)에서 내 실제 값을 입력하고 **재분석**하세요.")

        # ── 핵심 지표 ──────────────────────────────────────
        st.markdown("### 📈 핵심 지표")
        cf = result.get('현금흐름', {})
        c1, c2 = st.columns(2)
        with c1:
            st.metric("월 수입", fmt_won(cf.get('월수입', 0)))
        with c2:
            st.metric("월 지출", fmt_won(cf.get('월지출_합계', 0)))
        surplus = cf.get('월잉여(부족)', 0)
        st.metric(
            "월 잉여/부족", fmt_won(surplus),
            delta=fmt_won(surplus * 12) + " (연환산)" if surplus else None,
            delta_color="normal" if surplus >= 0 else "inverse",
        )
        assets = result.get('자산현황', {})
        st.metric("순자산", fmt_won(assets.get('순자산', 0)))

        # ── 기초연금 ─────────────────────────────────────────
        _bp = result.get('기초연금', {})
        if _bp:
            _bp_eligible = _bp.get('수급가능', False)
            _bp_amount   = _bp.get('월수급액', 0)
            _bp_note     = _bp.get('비고', '')
            _bp_income   = _bp.get('소득인정액', 0)
            _bp_threshold= _bp.get('선정기준액', 0)
            if _bp_eligible:
                st.success(
                    f"🏛️ **기초연금 수급 가능** — 월 **{fmt_won(_bp_amount)}** "
                    f"({_bp_note}) | 소득인정액 {fmt_won(_bp_income)} ≤ 선정기준 {fmt_won(_bp_threshold)}"
                )
            else:
                st.info(
                    f"🏛️ 기초연금: **수급 불가** — {_bp_note} "
                    f"(소득인정액 {fmt_won(_bp_income)} / 기준 {fmt_won(_bp_threshold)})"
                )

        # ── 나이별 수령액 시나리오 그래프 ──────────────────────
        _age_rows = result.get('나이별수입', [])
        if _age_rows:
            st.divider()
            with st.expander("📅 나이별 월수입 시나리오", expanded=True):
                st.caption("연금 개시 연령에 따라 수입이 늘어나는 구간을 보여줍니다.")

                _max_age = _age_rows[-1]['나이'] if _age_rows else 90
                _min_age = _age_rows[0]['나이'] if _age_rows else 55
                _age_map = {r['나이']: r for r in _age_rows}
                _retire_age = result.get('사용자정보', {}).get('희망은퇴연령', 60)

                # ── 나이별 지출 체감률 설정 ──────────────────────
                with st.expander("💸 나이별 지출 체감률 설정", expanded=False):
                    st.caption("은퇴 시점 지출을 100%로 볼 때 나이별 지출 비율 | 물가 반영은 별도 슬라이더로")
                    _sr_cols = st.columns(5)
                    _sr_cfg = [
                        ('은퇴~69세', 'sr_under70',  100),
                        ('70~74세',   'sr_70_74',    90),
                        ('75~79세',   'sr_75_79',    80),
                        ('80~84세',   'sr_80_84',    70),
                        ('85세+',     'sr_85plus',   60),
                    ]
                    _spending_rates = {}
                    for _col, (_lbl, _key, _def) in zip(_sr_cols, _sr_cfg):
                        with _col:
                            if _key not in st.session_state:
                                st.session_state[_key] = _def
                            _spending_rates[_lbl] = st.number_input(
                                _lbl, min_value=10, max_value=150,
                                step=5, key=_key, help=f"기본값 {_def}%",
                            ) / 100.0

                def _exp_mult(age):
                    if age < 70:   return _spending_rates.get('은퇴~69세', 1.0)
                    elif age < 75: return _spending_rates.get('70~74세', 0.9)
                    elif age < 80: return _spending_rates.get('75~79세', 0.8)
                    elif age < 85: return _spending_rates.get('80~84세', 0.7)
                    else:          return _spending_rates.get('85세+', 0.6)

                # ── 시각화 차트 ──────────────────────────────────
                # 현재 나이부터 5세 간격 눈금
                _tick_start = _min_age - (_min_age % 5) if _min_age % 5 != 0 else _min_age
                _tick_ages = list(range(_tick_start, _max_age + 1, 5))
                if _min_age not in _tick_ages:
                    _tick_ages = [_min_age] + _tick_ages
                if _max_age not in _tick_ages:
                    _tick_ages.append(_max_age)

                # ── 납입 기여금: 현재나이 → 납입종료연령 ────────────
                # DB/DC/국민연금: 은퇴까지(contribution_end_age 기본값=은퇴연령)
                # IRP/연금저축: 사용자가 설정한 contribution_end_age까지
                _CONTRIB_TYPES = {'국민연금', '퇴직연금DC', '퇴직연금DB', 'IRP', '연금저축'}
                _contrib_items = []
                for _pp in st.session_state.get('pensions', []):
                    _pt = _pp.get('pension_type', '')
                    if _pt not in _CONTRIB_TYPES:
                        continue
                    _pname = _pp.get('name', _pt)
                    # 퇴직연금DC/DB = 재직 납입이므로 은퇴연령까지 (Vega-Lite 파라미터로 동적 처리)
                    # 국민연금/IRP/연금저축 = 설정값 우선
                    if _pt in {'퇴직연금DC', '퇴직연금DB'}:
                        _until = _retire_age
                        _is_emp = True
                    else:
                        _until = _pp.get('contribution_end_age', _retire_age)
                        _is_emp = False
                    # 조정값 우선, 없으면 저장값
                    if _pt == '국민연금':
                        _mc_man = st.session_state.get('adj_nps_monthly') or round(_pp.get('monthly_contribution', 0) / 10000)
                    else:
                        _mc_man = (st.session_state.adj_monthly_contrib.get(_pname)
                                   or round(_pp.get('monthly_contribution', 0) / 10000))
                    if _mc_man <= 0:
                        continue
                    _contrib_items.append({
                        'label': f"{_pname}(납입)",
                        'amount_man': -_mc_man,
                        'until_age': _until,
                        'is_employment': _is_emp,
                    })

                # 수입 데이터: 모든 연령, 모든 항목 명시 (없으면 0 → 끊김 방지)
                _all_sources = set()
                for _r in _age_map.values():
                    _all_sources.update(_r['항목별'].keys())

                _records = []
                for _age in sorted(_age_map.keys()):
                    _row = _age_map[_age]
                    for _src in _all_sources:
                        _amt = _row['항목별'].get(_src, 0) or 0
                        _safe_amt = _amt if isinstance(_amt, (int, float)) and math.isfinite(_amt) else 0
                        _records.append({'나이': _age, '항목': _src, '색상키': _src, '월수입(만원)': round(_safe_amt / 10000, 1)})

                # 음수 데이터: 납입금 + 소득세 + 건보료 (모든 연령, 연속 area)
                _contrib_records = []
                for _age_val in sorted(_age_map.keys()):
                    _row = _age_map[_age_val]
                    # 연금 납입금 (until_age에서 0행 추가 → 면적 부드럽게 종료)
                    for _ci in _contrib_items:
                        if _age_val < _ci['until_age']:
                            _contrib_records.append({
                                '나이': _age_val, '항목': _ci['label'],
                                '색상키': _ci['label'].replace('(납입)', ''),
                                '월수입(만원)': float(_ci['amount_man']),
                                'is_dc_db': _ci.get('is_employment', False),
                            })
                        elif _age_val == _ci['until_age']:
                            _contrib_records.append({
                                '나이': _age_val, '항목': _ci['label'],
                                '색상키': _ci['label'].replace('(납입)', ''),
                                '월수입(만원)': 0.0,
                                'is_dc_db': _ci.get('is_employment', False),
                            })
                    _tax_v = round(_row.get('월소득세', 0) / 10000, 1)
                    if _tax_v > 0:
                        _contrib_records.append({'나이': _age_val, '항목': '소득세', '색상키': '소득세', '월수입(만원)': -_tax_v, 'is_dc_db': False})
                    _hi_v = round(_row.get('월건보료', 0) / 10000, 1)
                    if _hi_v > 0:
                        _contrib_records.append({'나이': _age_val, '항목': '건보료', '색상키': '건보료', '월수입(만원)': -_hi_v, 'is_dc_db': False})

                _df = pd.DataFrame(_records)
                _df_contrib = pd.DataFrame(_contrib_records) if _contrib_records else pd.DataFrame(columns=['나이','항목','색상키','월수입(만원)','is_dc_db'])
                _x_axis = alt.Axis(values=_tick_ages, format='d', labelExpr="datum.value + '세'")
                _x_scale = alt.Scale(domain=[_min_age, _max_age])

                if not _df.empty:
                    # ── 항목 정렬 순서: 근로소득→금융→국민연금→퇴직→IRP→연금저축→기타 ──
                    _PENSION_TYPE_RANK = {'국민연금': 30, '퇴직연금DC': 40, '퇴직연금DB': 41, 'IRP': 50, '연금저축': 60}
                    _FIXED_SOURCE_RANK = {'근로소득': 10, '임대수입': 20, '금융자산수익': 25}
                    _LATE_SOURCE_RANK = {'배우자 국민연금': 80, '배우자 기타연금': 81, '기초연금': 90}
                    # 연금 이름 → 타입 rank 매핑
                    _pname_rank = {}
                    for _pp in st.session_state.get('pensions', []):
                        _pname_rank[_pp.get('name', '')] = _PENSION_TYPE_RANK.get(_pp.get('pension_type', ''), 70)

                    def _src_rank(k):
                        if k in _FIXED_SOURCE_RANK: return _FIXED_SOURCE_RANK[k]
                        if k in _pname_rank: return _pname_rank[k]
                        if k in _LATE_SOURCE_RANK: return _LATE_SOURCE_RANK[k]
                        return 75

                    # ── 공유 색상 스케일 (수입·납입·세금 동일 팔레트) ──
                    _PALETTE = ['#aecde8','#fcc58a','#f5b3b2','#b8e3e1','#a8d5a2',
                                '#faebb8','#ddb9d4','#ffd6db','#d4bfb4','#e3dedd']
                    _FIXED_CLR = {'소득세': '#cda0d8', '건보료': '#86d0d8'}
                    # 순서 지정 정렬
                    _income_keys = sorted(set(_df['색상키'].unique()) - set(_FIXED_CLR), key=_src_rank)
                    _all_keys = _income_keys + list(_FIXED_CLR.keys())
                    _clr_range = [_PALETTE[i % len(_PALETTE)] for i in range(len(_income_keys))] + list(_FIXED_CLR.values())
                    _clr_scale = alt.Scale(domain=_all_keys, range=_clr_range)

                    # ── rank 컬럼 ───────────────────────────────────
                    _rank_map = {k: i for i, k in enumerate(_all_keys)}
                    _df['_rank'] = _df['색상키'].map(lambda k: _rank_map.get(k, 99))
                    _df_contrib['_rank'] = _df_contrib['색상키'].map(lambda k: _rank_map.get(k, 99))

                    # ── 차트 조정 컨트롤 ─────────────────────────────
                    _chart_retire_age = int(st.session_state.get('_chart_retire_age', _retire_age))

                    # ── Altair 파라미터 ──────────────────────────────
                    _p_retire = alt.param(name='retire_age', value=float(_chart_retire_age))
                    _inf_fixed = float(st.session_state.get('inp_inflation', 2.5))
                    _p_inf = alt.param(name='inf_rate', value=_inf_fixed)
                    # 클릭 셀렉션 (나이 필드 캡처)
                    _sel_click = alt.selection_point(
                        name='age_click', fields=['나이'],
                        on='click', nearest=True, clear=False,
                    )

                    _adj_expr = "datum['항목'] == '근로소득' && datum['나이'] >= retire_age ? 0 : datum['월수입(만원)']"
                    _adj_cont_expr = "datum.is_dc_db && datum['나이'] >= retire_age ? 0 : datum['월수입(만원)']"

                    # 수입 영역
                    _area = alt.Chart(_df).transform_calculate(
                        adj_income=_adj_expr
                    ).mark_area(interpolate='monotone').add_params(
                        _p_retire, _p_inf, _sel_click
                    ).encode(
                        x=alt.X('나이:Q', title='나이', scale=_x_scale, axis=_x_axis),
                        y=alt.Y('adj_income:Q', stack='zero',
                                axis=alt.Axis(tickMinStep=10, labelExpr="datum.value + '만'", title='월수입')),
                        color=alt.Color('색상키:N', scale=_clr_scale, sort=_all_keys,
                                        legend=alt.Legend(title='수입원', orient='bottom', columns=3)),
                        order=alt.Order('_rank:Q', sort='ascending'),
                        opacity=alt.value(0.65),
                        tooltip=[alt.Tooltip('나이:Q', title='나이'), alt.Tooltip('항목:N', title='항목'),
                                 alt.Tooltip('adj_income:Q', title='금액(만원)', format='.0f')],
                    )

                    # 납입·세금 (DC/DB 동적 컷오프)
                    _contrib_layer = alt.Chart(_df_contrib).transform_calculate(
                        adj_contrib=_adj_cont_expr
                    ).mark_area(interpolate='monotone').encode(
                        x=alt.X('나이:Q', scale=_x_scale, axis=_x_axis),
                        y=alt.Y('adj_contrib:Q', stack='zero'),
                        color=alt.Color('색상키:N', scale=_clr_scale, sort=_all_keys, legend=None),
                        order=alt.Order('_rank:Q', sort='ascending'),
                        opacity=alt.value(0.55),
                        tooltip=[alt.Tooltip('나이:Q', title='나이'), alt.Tooltip('항목:N', title='항목'),
                                 alt.Tooltip('adj_contrib:Q', title='금액(만원)', format='.0f')],
                    )

                    # 0 기준선
                    _zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
                        color='#888', strokeWidth=1.5
                    ).encode(y=alt.Y('y:Q'))

                    # 수입 합계선
                    _line = alt.Chart(_df).transform_calculate(
                        adj_income=_adj_expr
                    ).transform_aggregate(
                        total='sum(adj_income)',
                        groupby=['나이']
                    ).mark_line(color='#1565c0', strokeWidth=2.5, point=True).encode(
                        x=alt.X('나이:Q', scale=_x_scale, axis=_x_axis),
                        y=alt.Y('total:Q'),
                        tooltip=[alt.Tooltip('나이:Q', title='나이'),
                                 alt.Tooltip('total:Q', title='월수입 합계(만원)', format='.0f')],
                    )

                    # 지출선 (나이별 체감률 × 물가)
                    _base_expense = cf.get('월지출_합계', 0) / 10000
                    _df_exp_raw = pd.DataFrame([
                        {'나이': float(a), '기본지출': float(_base_expense * _exp_mult(a))}
                        for a in sorted(_age_map.keys())
                    ])
                    _exp_line = alt.Chart(_df_exp_raw).transform_calculate(
                        월지출="datum.기본지출 * pow(1 + inf_rate / 100, max(0, datum['나이'] - retire_age))"
                    ).mark_line(color='#e53935', strokeWidth=2, strokeDash=[6, 3]).encode(
                        x=alt.X('나이:Q', scale=_x_scale, axis=_x_axis),
                        y=alt.Y('월지출:Q'),
                        tooltip=[alt.Tooltip('나이:Q', title='나이'),
                                 alt.Tooltip('월지출:Q', title='지출(만원)', format='.0f')],
                    )

                    # 은퇴 기준선
                    _r_base = pd.DataFrame([{'_d': 0.0}])
                    _r_rule = alt.Chart(_r_base).transform_calculate(
                        x='retire_age'
                    ).mark_rule(color='#ff6f00', strokeWidth=2.5, strokeDash=[6, 3]).encode(
                        x=alt.X('x:Q', scale=_x_scale)
                    )
                    _r_txt = alt.Chart(_r_base).transform_calculate(
                        x='retire_age',
                        lbl="'은퇴 ' + toString(round(retire_age)) + '세'",
                    ).mark_text(
                        color='#ff6f00', fontSize=10, fontWeight='bold', align='left', dx=5,
                    ).encode(
                        x=alt.X('x:Q', scale=_x_scale),
                        y=alt.value(20),
                        text=alt.Text('lbl:N'),
                    )

                    _income_chart = (
                        _area + _contrib_layer + _zero_line + _line + _exp_line + _r_rule + _r_txt
                    ).resolve_scale(color='independent').properties(height=340)

                    _chart_event = st.altair_chart(
                        _income_chart,
                        on_select='rerun',
                        key='income_scenario_chart',
                        width='stretch',
                    )
                    st.caption("🟠 은퇴선 / 🔴 지출선 / 🔵 수입합계 / 0선 아래: 납입·세금")

                    # 클릭 이벤트 → 은퇴연령 갱신
                    if _chart_event and _chart_event.selection:
                        _click_data = _chart_event.selection.get('age_click', [])
                        if _click_data and isinstance(_click_data, list) and len(_click_data) > 0:
                            _first = _click_data[0]
                            _clicked_age = _first.get('나이') if isinstance(_first, dict) else None
                            if _clicked_age is not None:
                                _new_retire = max(55, int(round(float(_clicked_age))))
                                if _new_retire != st.session_state.get('_chart_retire_age'):
                                    st.session_state['_chart_retire_age'] = _new_retire
                                    st.rerun()

                    # ── 상세 인터랙티브 차트 열기 버튼 ─────────────────
                    if st.button("🔍 상세 인터랙티브 차트 열기", key='btn_detail_chart',
                                 help="D3.js 기반 별도 창으로 열립니다 — 드래그·슬라이더 완전 조작 가능"):
                        try:
                            import sys, os
                            sys.path.insert(0, os.path.dirname(__file__))
                            from detail_chart import generate_detail_html

                            # 데이터 직렬화
                            _detail_data = {
                                'ages': [int(a) for a in sorted(_age_map.keys())],
                                'income': {
                                    int(age): {
                                        src: round(val / 10000, 2)
                                        for src, val in _age_map[age]['항목별'].items()
                                    }
                                    for age in sorted(_age_map.keys())
                                },
                                'contrib_items': _contrib_items,
                                'retire_age': _chart_retire_age,
                                'inflation': float(st.session_state.get('inp_inflation', 2.5)),
                                'base_expense_man': round(cf.get('월지출_합계', 0) / 10000, 2),
                                'spending_rates': {
                                    'under65': float(st.session_state.get('sr_under65', 100)) / 100,
                                    '65_69':   float(st.session_state.get('sr_65_69',   90))  / 100,
                                    '70_74':   float(st.session_state.get('sr_70_74',   80))  / 100,
                                    '75_79':   float(st.session_state.get('sr_75_79',   70))  / 100,
                                    '80plus':  float(st.session_state.get('sr_80plus',  60))  / 100,
                                },
                                'tax': {
                                    int(age): round(_age_map[age].get('월소득세', 0) / 10000, 2)
                                    for age in sorted(_age_map.keys())
                                },
                                'health_ins': {
                                    int(age): round(_age_map[age].get('월건보료', 0) / 10000, 2)
                                    for age in sorted(_age_map.keys())
                                },
                                'colors': dict(zip(_all_keys, _clr_range)),
                                'income_sources': _income_keys,
                            }

                            _html_content = generate_detail_html(_detail_data)
                            _b64 = base64.b64encode(_html_content.encode('utf-8')).decode('ascii')
                            _open_script = f"""
<script>
(function() {{
  const b64 = "{_b64}";
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  const blob = new Blob([bytes], {{type: 'text/html;charset=utf-8'}});
  const url  = URL.createObjectURL(blob);
  window.open(url, '_blank');
}})();
</script>"""
                            st.iframe(_open_script, height=1)
                        except Exception as _e:
                            st.error(f"차트 생성 오류: {_e}")

            with st.expander("📋 구간별 수입/지출 세부 내역", expanded=False):
                _inf_rate = st.session_state.get('inp_inflation', 2.5) / 100
                _cf_living  = cf.get('월지출_생활', 0)
                _nps_info = {
                    name: info
                    for name, info in result.get('연금분석', {}).items()
                    if info.get('종류') == '국민연금'
                }
                _cf_member  = cf.get('월지출_회원권', 0)
                _cf_vehicle = cf.get('월지출_차량', 0)

                _prev_total = 0
                for _row in _age_rows:
                    _items = _row['항목별']
                    _prev_items = _age_rows[max(0, _age_rows.index(_row) - 1)]['항목별']
                    if _items != _prev_items or _row == _age_rows[0]:
                        _new_srcs = [k for k in _items if k not in _prev_items]
                        _total = _row['월수입']
                        _itax  = _row.get('월소득세', 0)
                        _hi    = _row.get('월건보료', 0)
                        _tax_total = _row.get('월세금', 0)
                        _delta = _total - _prev_total

                        _yrs = max(0, _row['나이'] - _retire_age)
                        _inf_mult  = (1 + _inf_rate) ** _yrs
                        _age_mult  = _exp_mult(_row['나이'])
                        _exp_living  = round(_cf_living  * _inf_mult * _age_mult)
                        _exp_member  = round(_cf_member  * _inf_mult * _age_mult)
                        _exp_vehicle = round(_cf_vehicle * _inf_mult * _age_mult)
                        _exp_total   = _exp_living + _exp_member + _exp_vehicle + _tax_total
                        _surplus     = _total - _exp_total

                        _sur_sign = "+" if _surplus >= 0 else ""
                        _hdr = (
                            f"{_row['나이']}세~  —  수입 {fmt_won(_total)}"
                            f"  |  지출 {fmt_won(_exp_total)}"
                            f"  |  잉여 {_sur_sign}{fmt_won(_surplus)}"
                        )
                        if _delta > 0:
                            _hdr += f"  (수입 +{fmt_won(_delta)})"

                        with st.expander(_hdr, expanded=False):
                            col_inc, col_exp = st.columns(2)
                            with col_inc:
                                st.metric("수입 합계", fmt_won(_total))
                            with col_exp:
                                st.metric("지출 합계", fmt_won(_exp_total))

                            _sur_color = "🟢" if _surplus >= 0 else "🔴"
                            st.markdown(
                                f"**월 잉여/부족:** {_sur_color} **{_sur_sign}{fmt_won(_surplus)}**"
                            )
                            st.divider()

                            col_inc2, col_exp2 = st.columns(2)
                            with col_inc2:
                                st.markdown("**수입 세부 내역**")
                                for _src, _amt in _items.items():
                                    _badge = " 🆕" if _src in _new_srcs else ""
                                    _pct = (_amt / _total * 100) if _total else 0
                                    st.markdown(f"- {_src}{_badge}: **{fmt_won(_amt)}** ({_pct:.0f}%)")
                                    if _src in _nps_info:
                                        _ni = _nps_info[_src]
                                        _orig = _ni.get('월수령액_원래', 0)
                                        _tdiff = _ni.get('조정_차이', 0)
                                        _treason = _ni.get('조정_사유', '')
                                        _ided = _ni.get('재직자_감액', 0)
                                        _ireason = _ni.get('재직자_감액_사유', '')
                                        _note_parts = []
                                        if _tdiff != 0:
                                            _sign = "+" if _tdiff > 0 else ""
                                            _note_parts.append(f"예상수령금액 {fmt_won(_orig)} → {_sign}{fmt_won(_tdiff)} ({_treason})")
                                        if _ided > 0:
                                            _note_parts.append(f"재직자 감액 -{fmt_won(_ided)} ({_ireason})")
                                        if _note_parts:
                                            st.caption("  &nbsp;&nbsp;&nbsp;" + "  /  ".join(_note_parts))

                            with col_exp2:
                                st.markdown("**지출 세부 내역**")
                                _inf_label = f" (물가 {_yrs}년" if _yrs > 0 else ""
                                _age_pct = round(_age_mult * 100)
                                _age_label = f" · 체감 {_age_pct}%)" if _inf_label else f" (체감 {_age_pct}%)"
                                st.markdown(f"- 생활비{_inf_label}{_age_label}: **{fmt_won(_exp_living)}**")
                                if _exp_member:
                                    st.markdown(f"- 회원권 연회비: **{fmt_won(_exp_member)}**")
                                if _exp_vehicle:
                                    st.markdown(f"- 차량 유지비: **{fmt_won(_exp_vehicle)}**")
                                if _tax_total:
                                    st.markdown(f"- 세금·건보료: **{fmt_won(_tax_total)}**")

                            _td = _row.get('세금계산기준', {})
                            if _td and (_itax > 0 or _hi > 0):
                                with st.expander("└ 세금·건보료 계산 기준", expanded=False):
                                    if _row['나이'] < _retire_age:
                                        st.markdown(
                                            f"**소득 구분:** 근로소득  \n"
                                            f"**연 총소득:** {_td.get('연소득', 0):,}만원  \n"
                                            f"**근로소득공제:** -{_td.get('근로소득공제', 0):,}만원  \n"
                                            f"**기본공제:** -150만원  \n"
                                            f"**과세표준:** {_td.get('과세표준', 0):,}만원  \n"
                                            f"**연 소득세:** {_td.get('연소득세', 0):,}만원 "
                                            f"(실효세율 {_td.get('실효세율', 0):.1f}%, 지방소득세 포함)  \n"
                                            f"**건보료:** {_td.get('건보료_월', 0):.1f}만원/월 "
                                            f"({_td.get('건보료구분', '')})"
                                        )
                                    else:
                                        _pvt = _td.get('사적연금_분리과세', '')
                                        _pvt_line = f"  \n**사적연금 과세 방식:** {_pvt}" if _pvt else ""
                                        _hi_inc = _td.get('건보료_소득반영', 0)
                                        st.markdown(
                                            f"**소득 구분:** 연금소득 (종합과세)  \n"
                                            f"**연 연금소득:** {_td.get('연연금소득', 0):,}만원  \n"
                                            f"**연금소득공제:** -{_td.get('연금소득공제', 0):,}만원  \n"
                                            f"**기본공제:** -150만원  \n"
                                            f"**과세표준:** {_td.get('과세표준', 0):,}만원  \n"
                                            f"**연 소득세:** {_td.get('연소득세', 0):,}만원 "
                                            f"(실효세율 {_td.get('실효세율', 0):.1f}%, 지방소득세 포함)"
                                            + _pvt_line +
                                            f"  \n**건보료:** {_td.get('건보료_월', 0):.1f}만원/월 "
                                            f"({_td.get('건보료구분', '')} — 연금소득 {_hi_inc:,}만원 반영, "
                                            f"공적연금은 50%만 산정)"
                                        )

                        _prev_total = _total

        # ── 현금흐름 부족 시 보완 수단 ───────────────────────
        supplement = result.get('현금흐름_보완', {})
        if supplement.get('부족여부'):
            shortfall = supplement.get('월부족액', 0)
            st.divider()
            st.markdown(f"### ⚠️ 현금흐름 부족 — 월 **{fmt_won(shortfall)}** 부족")
            remedies = supplement.get('보완수단', [])
            if remedies:
                st.markdown("#### 💡 보완 가능 수단")
                for r in remedies:
                    충당 = r.get('충당률', 0)
                    bar = "🟩" * (충당 // 20) + "⬜" * (5 - 충당 // 20)
                    st.info(
                        f"**{r['방법']}**  \n"
                        f"월 추가 수입 **{fmt_won(r['월추가수입'])}** "
                        f"(부족분의 {충당}%)  \n"
                        f"{bar}  \n"
                        f"{r['설명']}"
                    )

        recs = result.get('제언', [])
        if recs:
            st.markdown("### 💡 핵심 제언")
            for r in recs:
                priority_color = {'높음': '🔴', '중': '🟡', '검토': '🔵'}.get(r['우선순위'], '⚪')
                st.info(f"{priority_color} **[{r['우선순위']}] {r['항목']}**\n\n{r['내용']}")

        with st.expander("💼 연금별 수령액", expanded=False):
            _TAX_ICON = {
                '비과세': '🟢', '저율분리과세': '🟡', '분리과세': '🟠', '종합': '🔴',
            }
            _cur_year = _date.today().year
            _cur_age  = _cur_year - st.session_state.get('inp_birth_year', 1971)
            for pension_name, info in result.get('연금분석', {}).items():
                start_age  = info.get('수령시작_연령', info.get('실제수급연령'))
                start_year = info.get('개시년도')
                if not start_year and isinstance(start_age, int):
                    start_year = _cur_year + max(0, start_age - _cur_age)
                tax_method = info.get('과세방식', '')
                tax_icon = next((v for k, v in _TAX_ICON.items() if k in tax_method), '⚪')
                st.markdown(f"**{pension_name}** — {info.get('종류', '')}　{tax_icon} {tax_method}")
                c1, c2, c3 = st.columns(3)
                with c1:
                    if '월수령액_조정' in info:
                        st.metric("월 수령액", fmt_won(info['월수령액_조정']))
                    else:
                        st.metric("세후 월수령액", fmt_won(info.get('세후월수령액', 0)))
                with c2:
                    st.metric("수령 개시 연령", f"{start_age}세" if start_age else "-")
                with c3:
                    st.metric("개시 년도", f"{start_year}년" if start_year else "-")

                # 국민연금: 조정 사항이 있는 경우에만 상세 표시
                if info.get('종류') == '국민연금':
                    _orig = info.get('월수령액_원래', 0)
                    _timing_diff = info.get('조정_차이', 0)
                    _timing_reason = info.get('조정_사유', '')
                    _inc_ded = info.get('재직자_감액', 0)
                    _inc_reason = info.get('재직자_감액_사유', '')
                    _has_adjustment = (_timing_diff != 0 or _inc_ded > 0)

                    if _has_adjustment:
                        _rows = [("예상수령금액", fmt_won(_orig), "정상수령 기준금액")]
                        if _timing_diff != 0:
                            _sign = "+" if _timing_diff > 0 else ""
                            _rows.append((
                                "조기/연기 조정",
                                f"{_sign}{fmt_won(_timing_diff)}",
                                _timing_reason,
                            ))
                        if _inc_ded > 0:
                            _rows.append((
                                "재직자 노령연금 감액",
                                f"-{fmt_won(_inc_ded)}",
                                _inc_reason,
                            ))
                        _final = _orig + _timing_diff - _inc_ded
                        _rows.append(("최종 수령액", fmt_won(_final), ""))

                        for _label, _val, _desc in _rows:
                            _ra, _rb, _rc = st.columns([2, 1, 3])
                            _ra.markdown(f"**{_label}**")
                            _rb.markdown(f"**{_val}**")
                            if _desc:
                                _rc.caption(_desc)

                if '납입완료시_예상금액' in info:
                    end_amt = info['납입완료시_예상금액']
                    payout_amt = info.get('수령시점_적립금', end_amt)
                    st.caption(
                        f"납입완료시 예상금액 **{fmt_won(end_amt)}**"
                        + (f" /수령시점 **{fmt_won(payout_amt)}** (거치 운용 후)" if payout_amt != end_amt else "")
                    )
                if '수령기간' in info:
                    st.caption(f"수령기간 {info['수령기간']}년")
                st.divider()

        # ── 세금 & 건보료 ──────────────────────────────────────
        tax_info = result.get('세금건보료', {})
        with st.expander("🧾 세금 & 건보료", expanded=False):
            _ann_tax = tax_info.get('종합소득세', {}).get('total', 0)
            _ann_hi  = tax_info.get('건강보험료', {}).get('annual_total', 0)
            _c1, _c2 = st.columns(2)
            _c1.metric("월 종합소득세", fmt_won(round(_ann_tax / 12)),
                       delta=f"연 {fmt_won(_ann_tax)}", delta_color="off")
            _c2.metric("월 건강보험료", fmt_won(round(_ann_hi / 12)),
                       delta=f"연 {fmt_won(_ann_hi)}", delta_color="off")
            # ── 피부양자 자격 분석 ──────────────────────────────
            dep = tax_info.get('피부양자_가능여부', {})
            st.divider()
            st.markdown("**🏥 건강보험 피부양자 자격 분석**")
            st.caption("직장가입자 자녀(또는 배우자)의 건강보험에 피부양자로 등재되면 월 건보료 **0원**입니다.")

            _dep_inc    = dep.get('연간소득_피부양자기준', 0)
            _dep_prop   = dep.get('재산세과표_합계', 0)
            _dep_no_rent = dep.get('임대소득_없음', True)
            _dep_inc_ok  = dep.get('소득기준_충족', True)
            _dep_prop_ok = dep.get('재산기준_충족', True)
            _dep_mid     = dep.get('재산중간구간', False)
            _dep_mid_ok  = dep.get('재산중간구간_소득기준_충족')
            _dep_children = dep.get('자녀_있음', False)
            _dep_saving  = dep.get('절감_예상_연', 0)
            _dep_items   = dep.get('재산_항목', [])

            # 자격 3가지 조건 체크리스트
            _chk1 = "✅" if _dep_inc_ok  else "❌"
            _chk2 = "✅" if _dep_prop_ok else "❌"
            _chk3 = "✅" if _dep_no_rent else "⚠️"
            _mid_note = ""
            if _dep_mid:
                _mid_note = f" *(재산 3.6~5.4억 구간 → 소득 {'1천만원 이하 ✅' if _dep_mid_ok else '1천만원 초과 ❌'})*"

            st.markdown(f"""
| 조건 | 현황 | 기준 |
|------|------|------|
| {_chk1} **소득 기준** | 연 **{fmt_won(_dep_inc)}** | 2,000만원 이하 (국민연금+금융소득¹+임대소득) |
| {_chk2} **재산세과표 기준** | **{fmt_won(_dep_prop)}**{_mid_note} | 5.4억 이하 (주택 공시가×60%) |
| {_chk3} **임대·사업소득** | {'없음' if _dep_no_rent else '⚠️ 임대소득 있음'} | 임대사업 소득 있으면 자격 제한 가능 |

¹ 금융소득(이자+배당)이 연 1,000만원 이하이면 소득 산정 제외
""")

            if _dep_items:
                with st.expander("📋 재산세 과표 산정 내역", expanded=False):
                    for _di in _dep_items:
                        _pb = "자가" if _di.get('is_primary') else "투자"
                        _rent = " (임대중)" if _di.get('has_rental') else ""
                        st.text(
                            f"  {_di['name']} [{_pb}{_rent}]  "
                            f"공시가 {fmt_won(_di['official_price'])}  →  "
                            f"과표 {fmt_won(_di['tax_base'])} (×60%)"
                        )
                    if dep.get('재산세과표_합계', 0) > 0:
                        st.text(f"  합계 과표: {fmt_won(dep.get('재산세과표_합계', 0))}")

            if dep.get('eligible'):
                st.success(
                    f"✅ **피부양자 등재 가능** — 연 **{fmt_won(_dep_saving)}** 건보료 절감 예상"
                )
                if _dep_children:
                    st.info("👨‍👩‍👧 자녀가 직장가입자인 경우, 자녀 건보에 피부양자 등재를 검토하세요.")
            else:
                _reasons = dep.get('reasons_disqualified', [])
                st.warning(f"❌ **피부양자 자격 미충족** — {', '.join(_reasons)}")
                if _dep_children:
                    st.info(
                        "👨‍👩‍👧 자녀가 직장가입자이더라도 위 조건 미충족 시 피부양자 등재 불가. "
                        "소득·재산이 기준을 초과하면 지역가입자로 별도 납부해야 합니다."
                    )
                # 조건 개선 힌트
                if not _dep_inc_ok:
                    st.caption(f"💡 소득 기준 초과액: **{fmt_won(int(_dep_inc - 20_000_000))}** — 연금 수령 시기 조정 또는 금융자산 분산으로 소득 절감 가능")
                if not _dep_prop_ok:
                    st.caption(f"💡 재산 기준 초과액: **{fmt_won(int(_dep_prop - 540_000_000))}** — 부동산 처분 또는 대출 활용으로 과표 축소 가능")
            # ── 직장 임의계속가입 ──────────────────────────────
            vol_info = tax_info.get('임의계속가입', {})
            if vol_info:
                st.divider()
                st.markdown("**🏢 퇴직 후 건강보험 옵션 비교**")
                st.caption(
                    "퇴직 후 3가지 건보 가입 방식 중 본인 상황에 맞는 옵션을 선택할 수 있습니다. "
                    "재산이 많아 지역가입자 보험료가 높은 경우 **직장 임의계속가입**이 유리할 수 있습니다."
                )

                _vol_monthly = vol_info.get('월_보험료', 0)
                _loc_monthly = tax_info.get('건강보험료', {}).get('monthly_total', 0)
                _vol_saves   = vol_info.get('지역가입자_대비_절감_월', 0)
                _vol_better  = vol_info.get('임의계속가입_유리', False)
                _dep_eligible = dep.get('eligible', False)

                # 3가지 옵션 비교표
                _opt_rows = [
                    ("피부양자 등재",       "월 **0원**",               "✅ 가능" if _dep_eligible else "❌ 불가",
                     "자녀·배우자 직장보험에 무료 등재"),
                    ("직장 임의계속가입",   f"월 **{fmt_won(_vol_monthly)}**", "최대 36개월", "퇴직 전 급여 기준, 퇴직일로부터 2개월 내 신청"),
                    ("지역가입자 (기본)",   f"월 **{fmt_won(_loc_monthly)}**",  "은퇴 후 계속", "소득·재산 점수 합산, 재산 많을수록 보험료 높음"),
                ]
                _tbl = "| 옵션 | 월 보험료 | 기간/자격 | 비고 |\n|------|----------|----------|------|\n"
                for _r in _opt_rows:
                    _tbl += f"| {_r[0]} | {_r[1]} | {_r[2]} | {_r[3]} |\n"
                st.markdown(_tbl)

                # 추천 박스
                if _dep_eligible:
                    st.success(
                        "✅ **추천: 피부양자 등재** — 월 보험료 0원으로 가장 유리합니다. "
                        "자녀 또는 배우자의 직장보험에 피부양자로 등재하세요."
                    )
                elif _vol_better:
                    st.info(
                        f"💡 **추천: 직장 임의계속가입** — 지역가입자 대비 월 **{fmt_won(_vol_saves)}** 절감 (최대 36개월).  \n"
                        f"36개월 이후에는 지역가입자로 전환되므로, 그 전에 피부양자 자격 확보 또는 소득·재산 조정을 검토하세요."
                    )
                else:
                    st.warning(
                        f"ℹ️ 현재 설정 기준으로 지역가입자(월 {fmt_won(_loc_monthly)})가 임의계속가입(월 {fmt_won(_vol_monthly)})보다 유리합니다.  \n"
                        "급여가 높았던 경우 임의계속가입 보험료가 오히려 더 비쌀 수 있습니다."
                    )

                with st.expander("📌 직장 임의계속가입 조건 및 신청 방법", expanded=False):
                    st.markdown(f"""
**대상:** 퇴직 전 직장가입자였던 분 (1개월 이상 재직)

**보험료 산정:** 퇴직 전 보수월액 기준, 직장·회사 부담분 **모두 본인 부담**
- 적용 요율: 건강보험 7.09% (직장+사업주 합산) + 장기요양 12.95% × 건강보험료
- 기준 월급여: {fmt_won(vol_info.get('기준_월급여', 0))} → 월 보험료: **{fmt_won(_vol_monthly)}**

**적용 기간:** 최대 **36개월** (퇴직일 기준)

**신청 기한:** 퇴직일로부터 **2개월 이내** ← 이 기한을 놓치면 신청 불가

**신청 방법:**
1. 건강보험공단 지사 방문 또는 팩스·우편 신청
2. 「직장가입자 임의계속가입 신청서」 제출
3. 전 직장 사용자(회사)의 확인 없이 본인 단독 신청 가능

**주의사항:**
- 36개월 경과 후 자동으로 **지역가입자**로 전환됨
- 임의계속가입 중에도 소득·재산 변동 없으면 보험료 고정
- 재취직하면 즉시 직장가입자로 전환 (임의계속가입 종료)

🔗 [건강보험공단 임의계속가입 안내](https://www.nhis.or.kr/nhis/policy/wbhada02300m01.do)
""")

            st.divider()
            st.markdown("**🔗 현행 기준 확인**")
            st.markdown(
                "| 항목 | 공식 링크 |\n|------|----------|\n"
                "| 종합소득세 세율표 (현행) | [국세청 세율 안내](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=6527&cntntsId=7667) |\n"
                "| 연금소득 세액공제·과세 기준 | [국세청 연금소득](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=6655&cntntsId=7751) |\n"
                "| 홈택스 모의계산 (종합소득세) | [홈택스 세금계산기](https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&menuCd=ST) |\n"
                "| 지역가입자 건강보험료 계산 | [건강보험공단 보험료 계산기](https://www.nhis.or.kr/nhis/minwon/retrieveLocalInsureInfoCalc.do) |\n"
                "| 피부양자 등재 조건 확인 | [건강보험공단 피부양자 안내](https://www.nhis.or.kr/nhis/policy/wbhada01500m01.do) |"
            )

        # ── 세액공제 최적화 ──────────────────────────────────────
        tax_opt = result.get('세액공제최적화', {})
        if tax_opt:
            with st.expander("💡 IRP/연금저축 세액공제 최적화", expanded=False):
                col_t1, col_t2, col_t3 = st.columns(3)
                col_t1.metric("현재 연간 납입액", fmt_won(tax_opt.get('연간_납입액', 0)))
                col_t2.metric("현재 환급 예상액", fmt_won(tax_opt.get('현재_환급액', 0)))
                col_t3.metric("최대 추가 환급 가능", fmt_won(tax_opt.get('추가_환급가능액', 0)))
                rate_pct = round(tax_opt.get('적용세율', 0.132) * 100, 1)
                if tax_opt.get('한도도달여부'):
                    st.success(f"✅ 세액공제 한도(900만원)를 모두 활용하고 있습니다! (적용세율 {rate_pct}%)")
                else:
                    remaining = tax_opt.get('한도_잔여액', 0)
                    additional = tax_opt.get('추가_환급가능액', 0)
                    st.warning(
                        f"📌 연간 **{fmt_won(remaining)}** 추가 납입 시 **{fmt_won(additional)}** 세금 환급 가능  \n"
                        f"(적용세율 {rate_pct}% · 세액공제 한도 900만원)"
                    )
                st.caption("[세액공제 상세 기준 안내 (국세청)](https://www.nts.go.kr)")

        # ── 대출 분석 ────────────────────────────────────────
        _debts = st.session_state.get('debts', [])
        if _debts:
            _total_balance  = sum(d.get('balance', 0) for d in _debts)
            _total_monthly  = sum(d.get('monthly_payment', 0) for d in _debts)
            _total_interest = sum(
                d.get('balance', 0) * d.get('interest_rate', 0) / 12
                for d in _debts
            )
            with st.expander(
                f"📉 대출 분석 — 총 잔액 {fmt_won(_total_balance)} / 월 상환 {fmt_won(round(_total_monthly))}",
                expanded=False,
            ):
                _D_TYPE_KR = {'주담대': '주택담보대출', '신용대출': '신용대출',
                              '전세대출': '전세대출', '기타': '기타'}
                for d in _debts:
                    _bal  = d.get('balance', 0)
                    _rate = d.get('interest_rate', 0)
                    _pay  = d.get('monthly_payment', 0)
                    _int_m = round(_bal * _rate / 12)
                    _prin_m = max(0, _pay - _int_m)
                    _payoff = round(_bal / _pay) if _pay > _int_m else None
                    dc1, dc2, dc3 = st.columns(3)
                    dc1.metric(f"**{d['name']}** ({d.get('debt_type','')})",
                               fmt_won(_bal), delta=f"이율 {_rate*100:.1f}%", delta_color="off")
                    dc2.metric("월 상환액", fmt_won(_pay),
                               delta=f"이자 {fmt_won(_int_m)} / 원금 {fmt_won(_prin_m)}",
                               delta_color="off")
                    if _payoff:
                        _payoff_yr = _payoff // 12
                        _payoff_mo = _payoff % 12
                        dc3.metric("완납 예상",
                                   f"{_payoff_yr}년 {_payoff_mo}개월" if _payoff_yr else f"{_payoff_mo}개월")
                    else:
                        dc3.metric("완납 예상", "이자만 납부 중")
                    st.divider()
                _sc1, _sc2, _sc3 = st.columns(3)
                _sc1.metric("대출 총 잔액", fmt_won(_total_balance))
                _sc2.metric("월 총 상환액", fmt_won(round(_total_monthly)),
                            delta=f"월 이자 {fmt_won(round(_total_interest))}", delta_color="off")
                _dti = (_total_monthly * 12 / (cf.get('월수입', 1) * 12) * 100) if cf.get('월수입') else 0
                _sc3.metric("DTI (연소득 대비 상환비율)", f"{_dti:.1f}%",
                            delta="양호" if _dti < 40 else "주의", delta_color="normal" if _dti < 40 else "inverse")
                if _total_balance > 0:
                    st.caption(
                        f"💡 은퇴 전까지 대출 상환 시 월 지출 **{fmt_won(round(_total_monthly))}** 절감 가능 — "
                        f"은퇴 계획 수립 시 상환 완료 시점을 확인하세요."
                    )

        hp = result.get('주택연금', {})
        if hp.get('eligible'):
            with st.expander("🏠 주택연금 (비과세)", expanded=False):
                st.metric("예상 월 수령액", fmt_won(hp.get('monthly_payout', 0)))
                st.caption(f"공시가격 {fmt_won(hp.get('house_value_used', 0))} 기준, {hp.get('age_at_start')}세 가입시")
                st.markdown(
                    "🔗 [주택금융공사 — 주택연금 예상수령액 계산](https://www.hf.go.kr/hf/sub03/sub01.do)  \n"
                    "🔗 [주택연금 가입 조건·지급 방식 안내](https://www.hf.go.kr/hf/sub03/sub03.do)"
                )

        # ── 국민연금 수급시기 조정 ──────────────────────────
        scenarios = result.get('시나리오비교', {})
        nps_scenarios = scenarios.get('국민연금_수급시기', [])
        if nps_scenarios:
            st.divider()
            st.markdown("### 🎛️ 국민연금 수급시기 조정")
            st.caption("수급 개시 연령을 선택하면 조기/연기에 따른 수령액이 즉시 표시됩니다.")

            _nps_age_map = {s['start_age']: s for s in nps_scenarios}
            _nps_ages = sorted(_nps_age_map.keys())
            _normal_age = next((s['start_age'] for s in nps_scenarios
                                if s.get('diff_from_normal') == 0), _nps_ages[0])

            _cur_nps_age = next(
                (p['expected_start_age'] for p in st.session_state.pensions
                 if p.get('pension_type') == '국민연금'),
                _normal_age
            )
            _cur_nps_age = _cur_nps_age if _cur_nps_age in _nps_ages else _normal_age

            if st.session_state.get('adj_nps_age') not in _nps_ages:
                st.session_state.adj_nps_age = _cur_nps_age

            sel_nps_age = st.select_slider(
                "국민연금 수급 개시 연령",
                options=_nps_ages,
                value=st.session_state.adj_nps_age,
                key="adj_nps_age_slider",
            )
            st.session_state.adj_nps_age = sel_nps_age

            # ── 현재 납부 누적금 / 월 납입금 슬라이더 (메트릭 앞) ──
            _nps_p = next(
                (p for p in st.session_state.pensions if p.get('pension_type') == '국민연금'), {}
            )
            if st.session_state.adj_nps_balance is None:
                _raw_bal = round(_nps_p.get('current_balance', 0) / 10000)
                st.session_state.adj_nps_balance = (round(_raw_bal / 500) * 500)
            if st.session_state.adj_nps_monthly is None:
                _raw_mc = round(_nps_p.get('monthly_contribution', 0) / 10000)
                st.session_state.adj_nps_monthly = (round(_raw_mc / 5) * 5)

            cn_b1, cn_b2 = st.columns(2)
            with cn_b1:
                _bal_v = max(0, min(30000, (st.session_state.adj_nps_balance // 500) * 500))
                sel_nps_bal = _sl("현재 납부 누적금", 0, 30000, _bal_v, 500, "adj_nps_bal_sl", "won")
                st.session_state.adj_nps_balance = sel_nps_bal
            with cn_b2:
                _mc_v = max(0, min(50, (st.session_state.adj_nps_monthly // 5) * 5))
                sel_nps_mc = _sl("월 납입금", 0, 50, _mc_v, 5, "adj_nps_mc_sl", "won")
                st.session_state.adj_nps_monthly = sel_nps_mc

            # ── 적립금/납입금 변동 → 월수령액 비례 재계산 ──────
            _orig_bal_man = round(_nps_p.get('current_balance', 0) / 10000)
            _orig_mc_man  = round(_nps_p.get('monthly_contribution', 0) / 10000)
            _birth_year   = st.session_state.get('inp_birth_year', 1970)
            _birth_month  = st.session_state.get('inp_birth_month', 1)
            _now = _datetime.now()
            _cur_age = _now.year - _birth_year - (1 if _now.month < _birth_month else 0)
            _months_left = max(0, (sel_nps_age - _cur_age) * 12)

            _orig_total = _orig_bal_man + _orig_mc_man * _months_left
            _adj_total  = sel_nps_bal  + sel_nps_mc  * _months_left
            _nps_scale  = (_adj_total / _orig_total) if _orig_total > 0 else 1.0

            def _scale_nps(info):
                return {**info,
                        'monthly_amount': round(info['monthly_amount'] * _nps_scale),
                        'total_payout':   round(info['total_payout']   * _nps_scale)}

            _sel          = _scale_nps(_nps_age_map[sel_nps_age])
            _cur_nps_info = _scale_nps(_nps_age_map.get(_cur_nps_age, _nps_age_map[_normal_age]))
            _delta_nps    = _sel['monthly_amount'] - _cur_nps_info['monthly_amount']

            cn1, cn2, cn3 = st.columns(3)
            with cn1:
                _tag = "정상수급" if sel_nps_age == _normal_age else (
                    f"조기수급 ({_normal_age - sel_nps_age}년 앞당김)" if sel_nps_age < _normal_age
                    else f"연기수급 ({sel_nps_age - _normal_age}년 연기)")
                st.metric("수급 유형", _tag)
            with cn2:
                st.metric("월 수령액", fmt_won(_sel['monthly_amount']),
                          delta=fmt_won(_delta_nps) if _delta_nps else None)
            with cn3:
                st.metric("기대수명까지 총수령", fmt_won(_sel['total_payout']))

            if st.button("✅ 이 수급연령 국민연금에 적용", width='stretch'):
                for i, p in enumerate(st.session_state.pensions):
                    if p.get('pension_type') == '국민연금':
                        st.session_state.pensions[i]['expected_start_age'] = sel_nps_age
                        st.session_state.pensions[i]['expected_monthly_payout'] = _sel['monthly_amount']
                        st.session_state.pensions[i]['current_balance'] = sel_nps_bal * 10000
                        st.session_state.pensions[i]['monthly_contribution'] = sel_nps_mc * 10000
                st.success(f"✅ {sel_nps_age}세 수급으로 적용 완료! 재분석합니다...")
                st.session_state.analysis_result = None
                st.rerun()


        # ── 사적연금 수령기간 조정 ──────────────────────────
        pension_scenarios = supplement.get('사적연금_기간별', [])
        if pension_scenarios:
            st.divider()
            st.markdown("### 🎛️ 사적연금 수령기간 / 개시연령 조정")
            st.caption("슬라이더를 바꾸면 적립금과 월수령액이 즉시 재계산됩니다. 확정 후 재분석하세요.")

            # 인라인 재계산 헬퍼
            def _fv(pv, pmt, rate, years):
                if years <= 0:
                    return pv
                r = rate / 12
                n = int(years * 12)
                fv = pv * (1 + r) ** n
                fv += pmt * (((1 + r) ** n - 1) / r) if r > 0 else pmt * n
                return fv

            def _monthly_payout(balance, start_age, payout_years, rate):
                if payout_years <= 0:
                    payout_years = max(1, 90 - start_age)
                r = rate / 12
                n = payout_years * 12
                factor = (1 - (1 + r) ** -n) / r if r > 0 else n
                return round(balance / factor) if factor > 0 else 0

            def _calc_balance(ps, new_start_age, rate=None):
                _pn = ps['연금명']
                _adj_bal = st.session_state.adj_balance.get(_pn)
                _adj_mc  = st.session_state.adj_monthly_contrib.get(_pn)
                cb  = (_adj_bal * 10000) if _adj_bal is not None else ps.get('_current_balance', 0)
                pmt = (_adj_mc  * 10000) if _adj_mc  is not None else ps.get('_monthly_contribution', 0)
                ca  = ps.get('_current_age', 40)
                ea  = ps.get('_contribution_end_age', 60)
                r   = rate if rate is not None else ps.get('_annual_return', 0.04)
                bal_end = _fv(cb, pmt, r, max(0, ea - ca))
                bal_pay = _fv(bal_end, 0, r, max(0, new_start_age - ea))
                return bal_pay

            adj_total_delta = 0
            for ps in pension_scenarios:
                pname = ps['연금명']
                kind  = ps['종류']
                cur_y = ps['현재_기간']
                cur_m = ps['현재_월수령']
                orig_start_age = ps.get('수령시작_연령', 65)
                rate  = ps.get('_annual_return', 0.04)

                _period_opts = [0, 5, 10, 15, 20, 25, 30]
                if st.session_state.adj_payout.get(pname) not in _period_opts:
                    _snapped = min(_period_opts, key=lambda v: abs(v - cur_y))
                    st.session_state.adj_payout[pname] = _snapped
                if pname not in st.session_state.adj_start_age:
                    st.session_state.adj_start_age[pname] = orig_start_age
                if pname not in st.session_state.adj_return_rate:
                    _snapped_r = round(round(rate * 100 / 0.25) * 0.25, 2)
                    st.session_state.adj_return_rate[pname] = _snapped_r
                # 현재 적립금·월납입 기본값 (만원 단위)
                _orig_balance_man = round(ps.get('_current_balance', 0) / 10000)
                _orig_contrib_man = round(ps.get('_monthly_contribution', 0) / 10000)
                if pname not in st.session_state.adj_balance:
                    st.session_state.adj_balance[pname] = _orig_balance_man
                if pname not in st.session_state.adj_monthly_contrib:
                    st.session_state.adj_monthly_contrib[pname] = _orig_contrib_man

                with st.expander(f"**{pname}** ({kind})", expanded=False):
                    # ── 현재 적립금 / 월납입 슬라이더 ──
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        _bv = max(0, min(50000, (st.session_state.adj_balance[pname] // 500) * 500))
                        sel_balance = _sl("현재 적립금", 0, 50000, _bv, 500, f"adj_bal_{pname}", "won")
                        st.session_state.adj_balance[pname] = sel_balance
                    with cc2:
                        _mc_step = 5 if kind in ('IRP', '연금저축') else 10
                        _mv = max(0, min(200, (st.session_state.adj_monthly_contrib[pname] // _mc_step) * _mc_step))
                        sel_contrib = _sl("월 납입금", 0, 200, _mv, _mc_step, f"adj_mc_{pname}", "won")
                        st.session_state.adj_monthly_contrib[pname] = sel_contrib

                    ca, cb = st.columns(2)
                    with ca:
                        sel_start = _sl("수령 개시 연령", 50, 85,
                            st.session_state.adj_start_age[pname], 1, f"adj_sa_{pname}", "세")
                        st.session_state.adj_start_age[pname] = sel_start
                    with cb:
                        sel_years = st.select_slider(
                            "수령기간 (년, 0=종신)",
                            options=_period_opts,
                            value=st.session_state.adj_payout[pname],
                            key=f"adj_sl_{pname}",
                        )
                        st.session_state.adj_payout[pname] = sel_years

                    # 수익률 슬라이더
                    sel_rate_pct = _sl("예상 수익률", 0.25, 15.0,
                        float(st.session_state.adj_return_rate[pname]), 0.25, f"adj_rt_{pname}", "%")
                    st.session_state.adj_return_rate[pname] = sel_rate_pct
                    sel_rate = sel_rate_pct / 100

                    # 수익률별 적립금 bar 차트
                    _rate_scenarios = [
                        ('예금형\n(1.5%)', 0.015),
                        ('채권형\n(4.0%)', 0.040),
                        ('TDF/혼합\n(5.5%)', 0.055),
                        ('주식형\n(8.0%)', 0.080),
                    ]
                    _sel_in_std = any(abs(sel_rate - r) < 0.001 for _, r in _rate_scenarios)
                    _bar_rows = []
                    for _lbl, _r in _rate_scenarios:
                        _bal = _calc_balance(ps, sel_start, _r)
                        _is_sel = abs(_r - sel_rate) < 0.001
                        _bar_rows.append({
                            '유형': _lbl,
                            '적립금(만원)': round(_bal / 10000),
                            '구분': '선택' if _is_sel else '기타',
                        })
                    if not _sel_in_std:
                        _custom_bal = _calc_balance(ps, sel_start, sel_rate)
                        _bar_rows.append({
                            '유형': f'설정\n({sel_rate_pct:.1f}%)',
                            '적립금(만원)': round(_custom_bal / 10000),
                            '구분': '선택',
                        })
                    _df_bar = pd.DataFrame(_bar_rows)
                    _bar_chart = (
                        alt.Chart(_df_bar)
                        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                        .encode(
                            x=alt.X('유형:N', sort=None, title=None,
                                    axis=alt.Axis(labelAngle=0, labelLineHeight=14)),
                            y=alt.Y('적립금(만원):Q', title='수령시점 적립금(만원)'),
                            color=alt.Color('구분:N',
                                scale=alt.Scale(
                                    domain=['선택', '기타'],
                                    range=['#1976d2', '#b0bec5'],
                                ),
                                legend=None,
                            ),
                            tooltip=[
                                alt.Tooltip('유형:N', title='유형'),
                                alt.Tooltip('적립금(만원):Q', title='적립금(만원)', format=','),
                            ],
                        )
                        .properties(height=180)
                    )
                    st.altair_chart(_bar_chart, width='stretch')

                    adj_balance = _calc_balance(ps, sel_start, sel_rate)
                    adj_monthly = _monthly_payout(adj_balance, sel_start, sel_years, sel_rate)
                    delta_m = adj_monthly - cur_m
                    adj_total_delta += delta_m

                    end_age_str = (f"{sel_start + sel_years - 1}세"
                                   if sel_years > 0 else "종신")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("수령시점 적립금", fmt_won(round(adj_balance)))
                    with c2:
                        st.metric("조정 후 월수령", fmt_won(adj_monthly),
                                  delta=fmt_won(delta_m) if delta_m else None)
                    c3, c4 = st.columns(2)
                    with c3:
                        st.metric("수령 종료 연령", end_age_str)
                    with c4:
                        st.metric("현재 설정",
                                  f"{orig_start_age}세 / {cur_y}년 / {rate*100:.1f}%",
                                  delta=f"월 {fmt_won(cur_m)}", delta_color="off")

            # 조정 후 현금흐름 요약
            adj_surplus = surplus + adj_total_delta
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("조정 후 월 잉여/부족", fmt_won(adj_surplus),
                          delta=fmt_won(adj_total_delta) if adj_total_delta else None,
                          delta_color="normal" if adj_surplus >= 0 else "inverse")
            with c2:
                if adj_surplus >= 0:
                    st.success("✅ 기간 조정으로 부족분 해소 가능")
                elif adj_surplus > surplus:
                    st.warning(f"{fmt_won(adj_total_delta)} 개선 — 여전히 {fmt_won(abs(adj_surplus))} 부족")
                else:
                    st.error("❌ 기간 조정만으로는 부족")

            # 현재 연금에 기간/개시연령/수익률/적립금/납입액 반영 버튼
            if st.button("✅ 조정값 연금에 적용", width='stretch'):
                for ps in pension_scenarios:
                    pname = ps['연금명']
                    new_y     = st.session_state.adj_payout.get(pname, ps['현재_기간'])
                    new_a     = st.session_state.adj_start_age.get(pname, ps.get('수령시작_연령', 65))
                    new_r_pct = st.session_state.adj_return_rate.get(pname)
                    new_bal   = st.session_state.adj_balance.get(pname)
                    new_mc    = st.session_state.adj_monthly_contrib.get(pname)
                    for i, p in enumerate(st.session_state.pensions):
                        if p['name'] == pname:
                            st.session_state.pensions[i]['payout_period_years'] = new_y
                            st.session_state.pensions[i]['expected_start_age'] = new_a
                            if new_r_pct is not None:
                                st.session_state.pensions[i]['annual_return_rate'] = new_r_pct / 100
                            if new_bal is not None:
                                st.session_state.pensions[i]['current_balance'] = new_bal * 10000
                            if new_mc is not None:
                                st.session_state.pensions[i]['monthly_contribution'] = new_mc * 10000
                st.success("✅ 적용 완료! 재분석합니다...")
                st.session_state.analysis_result = None
                st.rerun()

        st.divider()
        st.download_button(
            "📥 결과 JSON 다운로드",
            data=json.dumps(result, ensure_ascii=False, indent=2, default=str),
            file_name=f"retirement_analysis_{st.session_state.get('inp_name', st.session_state.user_name or 'user')}.json",
            mime="application/json",
            width='stretch',
        )


    # 푸터
    st.divider()
    st.caption("⚠️ 본 결과는 추정치입니다. 정확한 금액은 각 공단의 공식 모의계산기 또는 전문가 상담을 권장합니다.")
    st.markdown(
        "<small>"
        "📎 공식 참고 사이트: "
        "[국민연금공단](https://www.nps.or.kr) · "
        "[국세청](https://www.nts.go.kr) · "
        "[건강보험공단](https://www.nhis.or.kr) · "
        "[주택금융공사](https://www.hf.go.kr) · "
        "[통합연금포털](https://100lifeplan.fss.or.kr) · "
        "[고용노동부 퇴직연금](https://www.moel.go.kr/retirementBenefit/main.do)"
        "</small>",
        unsafe_allow_html=True,
    )


# ============================================================
# 라우팅
# ============================================================
if not st.session_state.token:
    show_auth_screen()
elif st.session_state.page == 'account':
    show_account_page()
else:
    # 로그인 직후 최초 1회 프로필 자동 로드
    # onboarding_done=True(신규 가입 직후)이면 국가평균이 이미 세팅됐으므로 API 호출 생략
    if st.session_state.profile_id is None and not st.session_state.get('onboarding_done'):
        _prof, _err = call_api("/profiles/latest", method="GET")
        _has_saved_profile = False
        if not _err and _prof and _prof.get('id'):
            _restore_from_profile(_prof)
            # DB에 저장된 프로필이 있으면 무조건 내 정보 모드
            _has_saved_profile = True
        if not _has_saved_profile:
            # 프로필 없음 → 국가 평균으로 온보딩 (기본 55세 구간)
            _default_age = st.session_state.get('_reg_age', 55)
            _apply_national_avg(_default_age)
            st.session_state.onboarding_done = True
            st.session_state.analysis_result = None
            if not st.session_state.get('profile_id'):
                st.session_state.profile_id = 0
        st.rerun()
    show_main_app()
