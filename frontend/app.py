"""
은퇴설계 Streamlit 어플 (모바일 친화)
- 실행: streamlit run frontend/app.py
"""
import streamlit as st
import requests
import json
import pandas as pd
import altair as alt
from datetime import date as _date, datetime as _datetime, timedelta as _timedelta
from urllib.parse import unquote
import extra_streamlit_components as stx

# ============================================================
# 설정
# ============================================================
try:
    API_BASE = st.secrets.get("API_BASE", "http://localhost:8080")
except Exception:
    try:
        from dotenv import load_dotenv as _lde
        import os as _os
        _lde(dotenv_path=_os.path.join(_os.path.dirname(_os.path.dirname(__file__)), '.env'))
        API_BASE = _os.getenv("BACKEND_URL", "http://localhost:8080")
    except Exception:
        API_BASE = "http://localhost:8080"

st.set_page_config(
    page_title="은퇴설계",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown("<script>document.title='은퇴설계';</script>", unsafe_allow_html=True)

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
        'profile_id': None,      # None=아직 로드 시도 안함, 0=프로필 없음, n=프로필ID
        # 기본 정보
        'inp_birth_year': 1971,
        'inp_birth_month': 5,
        'inp_birth_day': 15,
        'inp_gender': '남',
        'inp_retirement_age': 60,
        'inp_lifespan': 90,
        'inp_dependents': 1,
        'inp_inflation': 2.5,
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

# ── 쿠키 기반 세션 유지 ──────────────────────────────────────
_cm = stx.CookieManager(key="ret_cookies")

def _save_session_to_cookie(token, user_id, user_name, user_email):
    _exp = _datetime.now() + _timedelta(days=30)
    _cm.set('ret_token', token,        expires_at=_exp, key='cks_tok')
    _cm.set('ret_uid',   str(user_id), expires_at=_exp, key='cks_uid')
    _cm.set('ret_name',  user_name,    expires_at=_exp, key='cks_name')
    _cm.set('ret_email', user_email,   expires_at=_exp, key='cks_email')

def _clear_session_cookie():
    for _ck in ('ret_token', 'ret_uid', 'ret_name', 'ret_email'):
        try:
            _cm.delete(_ck)
        except Exception:
            pass

# 새로고침 후 쿠키에서 세션 복원
# CookieManager는 첫 렌더에서 None 반환 → JS 로드 후 자동 rerun → 두 번째에 실제값
if not st.session_state.token:
    _ck_token = _cm.get('ret_token')
    if _ck_token:
        st.session_state.token      = _ck_token
        st.session_state.user_id    = int(_cm.get('ret_uid') or 0)
        st.session_state.user_name  = _cm.get('ret_name') or ''
        st.session_state.user_email = _cm.get('ret_email') or ''
        st.rerun()  # 토큰 복원 후 메인 앱으로 전환

# OAuth 콜백 처리 (소셜 로그인 완료 후 리다이렉트)
_qp = st.query_params
if "token" in _qp and not st.session_state.token:
    st.session_state.token      = _qp["token"]
    st.session_state.user_id    = int(_qp.get("user_id", 0))
    st.session_state.user_name  = unquote(_qp.get("name", ""))
    st.session_state.user_email = unquote(_qp.get("email", ""))
    _save_session_to_cookie(st.session_state.token, st.session_state.user_id,
                            st.session_state.user_name, st.session_state.user_email)
    st.query_params.clear()
    st.rerun()
elif "oauth_error" in _qp:
    _err = unquote(_qp["oauth_error"])
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
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return None, f"오류: {detail}"
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
    if abs(amount) >= 100_000_000:
        return f"{amount/100_000_000:.2f}억원"
    elif abs(amount) >= 10_000:
        return f"{amount/10_000:,.0f}만원"
    else:
        return f"{amount:,}원"


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

    tab_login, tab_register = st.tabs(["🔑 로그인", "📝 회원가입"])

    # --- 로그인 ---
    with tab_login:
        with st.form("login_form"):
            st.subheader("로그인")
            email = st.text_input("이메일", placeholder="example@email.com")
            password = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("로그인", width='stretch')

        if submitted:
            if not email or not password:
                st.error("이메일과 비밀번호를 입력하세요.")
            else:
                result, err = call_api("/auth/login", {
                    "username": email,
                    "password": password,
                }, method="POST", form=True)
                if err:
                    msg = err.replace("오류: ", "", 1)
                    st.error(msg)
                else:
                    st.session_state.token = result["access_token"]
                    st.session_state.user_id = result["user_id"]
                    st.session_state.user_name = result["name"]
                    st.session_state.user_email = email
                    _save_session_to_cookie(result["access_token"], result["user_id"],
                                            result["name"], email)
                    st.success(f"환영합니다, {result['name']}님!")
                    st.rerun()

    # --- 회원가입 ---
    with tab_register:
        with st.form("register_form"):
            st.subheader("회원가입")
            r_name = st.text_input("이름", placeholder="홍길동")
            r_email = st.text_input("이메일", placeholder="example@email.com", key="r_email")
            r_pw = st.text_input("비밀번호 (6자 이상)", type="password", key="r_pw")
            r_pw2 = st.text_input("비밀번호 확인", type="password", key="r_pw2")
            submitted = st.form_submit_button("회원가입", width='stretch')

        if submitted:
            if not all([r_name, r_email, r_pw, r_pw2]):
                st.error("모든 항목을 입력하세요.")
            elif len(r_pw) < 6:
                st.error("비밀번호는 6자 이상이어야 합니다.")
            elif r_pw != r_pw2:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                result, err = call_api("/auth/register", {
                    "email": r_email,
                    "password": r_pw,
                    "name": r_name,
                })
                if err:
                    st.error(err)
                else:
                    st.session_state.token = result["access_token"]
                    st.session_state.user_id = result["user_id"]
                    st.session_state.user_name = result["name"]
                    st.session_state.user_email = r_email
                    _save_session_to_cookie(result["access_token"], result["user_id"],
                                            result["name"], r_email)
                    st.success(f"가입 완료! 환영합니다, {result['name']}님!")
                    st.rerun()


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

        st.markdown('<div class="outline-btn">', unsafe_allow_html=True)
        if st.button("🚪 로그아웃"):
            _clear_session_cookie()
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        st.caption("💰 은퇴설계 v0.2.0")

    # 헤더
    st.markdown("# 💰 은퇴설계")
    st.caption("연금·세금·건보료 종합 시뮬레이션")

    # ── 저장 버튼 ──────────────────────────────────────
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
                    st.success("✅ 저장 완료!")

    # 탭 네비게이션
    tabs = st.tabs(["🙋 본인", "💼 연금", "🏠 자산", "💳 지출", "📊 분석"])

    # ----------------------------------------------------------
    # 탭 1: 본인 정보
    # ----------------------------------------------------------
    with tabs[0]:
        st.subheader("기본 정보")
        col1, col2 = st.columns(2)
        with col1:
            if 'inp_name' not in st.session_state:
                st.session_state['inp_name'] = st.session_state.user_name or ""
            name = st.text_input("이름", key="inp_name")
            gender = st.selectbox("성별", ["남", "여"], key="inp_gender")
        with col2:
            birth_year = st.number_input("출생년도", min_value=1940, max_value=2010, step=1, key="inp_birth_year")
            retirement_age = st.number_input("은퇴희망 연령", min_value=50, max_value=75, step=1, key="inp_retirement_age")

        col3, col4 = st.columns(2)
        with col3:
            birth_month = st.number_input("출생월", min_value=1, max_value=12, step=1, key="inp_birth_month")
        with col4:
            birth_day = st.number_input("출생일", min_value=1, max_value=31, step=1, key="inp_birth_day")

        expected_lifespan = st.slider("기대수명", min_value=75, max_value=120, key="inp_lifespan")
        dependents = st.number_input("부양가족 수", min_value=0, max_value=10, step=1, key="inp_dependents")

        st.markdown("""
<div style="margin:1.2rem 0 0.5rem 0;">
  <span style="background:rgba(25,118,210,0.15);color:#1976d2;border:1px solid rgba(25,118,210,0.4);
               border-radius:6px;padding:4px 12px;font-size:0.95rem;font-weight:700;letter-spacing:0.02em;">
    💼 은퇴 전 소득
  </span>
</div>
""", unsafe_allow_html=True)
        annual_salary = st.number_input("연봉 (만원)", min_value=0, max_value=100000, step=100, key="inp_salary") * 10000
        annual_bonus = st.number_input("연간 보너스 (만원)", min_value=0, max_value=100000, step=100, key="inp_bonus") * 10000
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
            parttime_monthly = st.number_input("월 근로소득 (만원)", min_value=0, max_value=10000,
                step=10, key="inp_parttime_monthly") * 10000
        with col_pt2:
            parttime_until = st.slider("종료 연령", min_value=60, max_value=80,
                key="inp_parttime_until")

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
            spouse_nps = st.number_input("배우자 국민연금 월수령액 (만원)", min_value=0, max_value=1000,
                step=5, key="inp_spouse_nps") * 10000
            spouse_nps_age = st.slider("배우자 국민연금 개시연령", min_value=60, max_value=70,
                key="inp_spouse_nps_age")
        with col_sp2:
            spouse_other = st.number_input("배우자 기타연금 월수령액 (만원)", min_value=0, max_value=1000,
                step=5, key="inp_spouse_other") * 10000
            spouse_other_age = st.slider("배우자 기타연금 개시연령", min_value=50, max_value=85,
                key="inp_spouse_other_age")

        if st.button("📌 내 국민연금 정상 수급연령 확인", key="check_age"):
            result, err = call_api(f"/pension/start-age/{birth_year}", method="GET")
            if err:
                st.error(err)
            else:
                st.success(f"✅ {birth_year}년생 정상 수급연령: **{result['normal_start_age']}세**")

    # ----------------------------------------------------------
    # 탭 2: 연금
    # ----------------------------------------------------------
    with tabs[1]:
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
            if p['pension_type'] == "국민연금":
                _std = max(430_000, min(int(_sal_won_e / 12), 6_370_000))
                _is_emp = st.session_state.get("inp_is_employee", True)
                _rate = 0.045 if _is_emp else 0.09
                _type_lbl = "직장가입자 4.5%" if _is_emp else "지역가입자 9%"
                st.info(
                    f"💡 **현재 소득 기준 예상 납입액**: 월 **{int(_std * _rate):,}원**  \n"
                    f"기준소득월액 {_std:,}원 × {_type_lbl}  \n"
                    f"*(기준소득월액 상한 6,370,000원 / 하한 430,000원 적용)*"
                )
            elif p['pension_type'] in ("퇴직연금DB", "퇴직연금DC", "IRP"):
                _monthly_sal_e = int(_sal_won_e / 12)
                st.info(
                    f"💡 **현재 소득 기준 예상 납입액**: 월 **{_monthly_sal_e:,}원**  \n"
                    f"연봉 {int(_sal_won_e):,}원 ÷ 12개월 (법정 퇴직급여 기준)  \n"
                    f"*(실제 납입액은 회사 규정에 따라 다를 수 있습니다)*"
                )

            with st.form("edit_pension_form"):
                pn_name = st.text_input("상품명/기관명", value=p['name'])
                c1, c2 = st.columns(2)
                with c1:
                    pn_balance = st.number_input("현재 적립금 (만원)", 0, 1_000_000,
                        max(0, int(p['current_balance'] // 10000)), step=100)
                    pn_end_age = st.slider("납입 종료 연령", 30, 80,
                        min(max(p['contribution_end_age'], 30), 80), step=1)
                with c2:
                    pn_monthly = st.number_input("월 납입금 (만원)", 0, 1000,
                        max(0, int(p['monthly_contribution'] // 10000)), step=10)
                    pn_start_age = st.slider("수령 개시 연령", 50, 85,
                        min(max(p['expected_start_age'], 50), 85), step=1)
                c3, c4 = st.columns(2)
                with c3:
                    pn_payout = st.number_input("예상 월 수령액 (만원)", 0, 1000,
                        max(0, int(p['expected_monthly_payout'] // 10000)), step=10)
                with c4:
                    pn_return = st.slider("예상 연수익률 (%)", 0, 50,
                        min(round(int(p['annual_return_rate'] * 100)), 50), step=1) / 100
                pn_period = st.slider("수령기간(년, 0=종신)", 0, 40,
                    min(p['payout_period_years'], 40), step=1)

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
                    elif pn_type_sel in ("퇴직연금DB", "퇴직연금DC", "IRP"):
                        _monthly_sal = int(_sal_won / 12)
                        _pn_monthly_default = round(_monthly_sal / 10000)
                        st.info(
                            f"💡 **현재 소득 기준 예상 납입액**: 월 **{_monthly_sal:,}원**  \n"
                            f"연봉 {int(_sal_won):,}원 ÷ 12개월 (법정 퇴직급여 기준)  \n"
                            f"*(실제 납입액은 회사 규정에 따라 다를 수 있습니다)*"
                        )

                    with st.form("add_pension", clear_on_submit=True):
                        pn_name = st.text_input("상품명/기관명", value=pn_type_sel)
                        c1, c2 = st.columns(2)
                        with c1:
                            pn_balance = st.number_input("현재 적립금 (만원)", 0, 1_000_000, 0, step=100) * 10000
                            pn_end_age = st.slider("납입 종료 연령", 30, 80, 60, step=1)
                        with c2:
                            pn_monthly = st.number_input("월 납입금 (만원)", 0, 1000, _pn_monthly_default, step=10) * 10000
                            pn_start_age = st.slider("수령 개시 연령", 50, 85, 65, step=1)
                        c3, c4 = st.columns(2)
                        with c3:
                            pn_payout_monthly = st.number_input(
                                "예상 월 수령액 (만원, 국민연금/DB형)", 0, 1000, 0, step=10) * 10000
                        with c4:
                            pn_return = st.slider("예상 연수익률 (%)", 0, 50, 4, step=1) / 100
                        pn_period = st.slider("수령기간(년, 0=종신)", 0, 40, 20, step=1)
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
    with tabs[2]:
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
                    re_market = st.number_input("시세 (만원)", 0, 100_000_000,
                                                int(r['market_value'] // 10000), step=1000) * 10000
                    re_official = st.number_input("공시가격 (만원, 비우면 시세*70%)", 0, 100_000_000,
                                                  int((r['official_price'] or 0) // 10000), step=1000) * 10000
                    re_debt = st.number_input("담보대출 (만원)", 0, 100_000_000,
                                              int(r['debt'] // 10000), step=100) * 10000
                    re_rent = st.number_input("월세 수입 (만원)", 0, 10000,
                                              int(r['monthly_rent_income'] // 10000), step=10) * 10000
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
                        re_market = st.number_input("시세 (만원)", 0, 100_000_000, 0, step=1000) * 10000
                        re_official = st.number_input("공시가격 (만원, 비우면 시세*70%)", 0, 100_000_000, 0, step=1000) * 10000
                        re_debt = st.number_input("담보대출 (만원)", 0, 100_000_000, 0, step=100) * 10000
                        re_rent = st.number_input("월세 수입 (만원)", 0, 10000, 0, step=10) * 10000
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
                    fa_amount = st.number_input("금액 (만원)", 0, 100_000_000,
                                                int(f['amount'] // 10000), step=100) * 10000
                    fa_return = st.slider("예상 연수익률 (%)", 0.0, 50.0,
                        min(round(f['annual_return_rate'] * 100, 1), 50.0), step=0.5) / 100
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
                        fa_amount = st.number_input("금액 (만원)", 0, 100_000_000, 0, step=100) * 10000
                        fa_return = st.slider("예상 연수익률 (%)", 0.0, 50.0, 3.0, step=0.5) / 100
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
                    ms_value = st.number_input("시세 (만원)", 0, 100_000,
                                               int(m['market_value'] // 10000), step=100) * 10000
                    ms_dues = st.number_input("연회비 (만원)", 0, 10000,
                                              int(m['annual_dues'] // 10000), step=10) * 10000
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
                        ms_value = st.number_input("시세 (만원)", 0, 100_000, 0, step=100) * 10000
                        ms_dues = st.number_input("연회비 (만원)", 0, 10000, 0, step=10) * 10000
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
                    v_value = st.number_input("시세 (만원)", 0, 100000,
                                              int(v['market_value'] // 10000), step=100) * 10000
                    v_cost = st.number_input("연 유지비 (만원, 보험+세금+유류)", 0, 5000,
                                             int(v['annual_cost'] // 10000), step=10) * 10000
                    if st.form_submit_button("저장", width='stretch'):
                        st.session_state.vehicles[v_edit_idx] = {
                            "name": v_name, "market_value": v_value, "annual_cost": v_cost,
                        }
                        st.session_state.editing_v_idx = None; st.rerun()
            else:
                with st.expander("➕ 차량 추가", expanded=False):
                    with st.form("add_v", clear_on_submit=True):
                        v_name = st.text_input("이름", "○○ 차량")
                        v_value = st.number_input("시세 (만원)", 0, 100000, 4000, step=100) * 10000
                        v_cost = st.number_input("연 유지비 (만원, 보험+세금+유류)", 0, 5000, 400, step=10) * 10000
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
                    ins_premium = st.number_input("월 납입 보험료 (만원)", 0, 10000,
                                                  int(ins['monthly_premium'] // 10000), step=1) * 10000
                    ins_end_age = st.slider("납입 종료 연령", 30, 80, ins['premium_end_age'])
                    ins_surrender = st.number_input("해약환급금 (만원)", 0, 100_000_000,
                                                    int(ins['surrender_value'] // 10000), step=100) * 10000
                    ins_maturity = st.number_input("만기/수령 예상금액 (만원)", 0, 100_000_000,
                                                   int(ins['maturity_value'] // 10000), step=100) * 10000
                    if ins_type == "연금보험":
                        ins_payout = st.number_input("월 수령액 (만원, 연금형)", 0, 10000,
                                                     int(ins['monthly_payout'] // 10000), step=10) * 10000
                        ins_payout_start = st.slider("수령 개시 연령", 50, 85, ins['payout_start_age'])
                        ins_payout_period = st.slider("수령기간(년, 0=종신)", 0, 40, ins['payout_period_years'])
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
                        ins_premium = st.number_input("월 납입 보험료 (만원)", 0, 10000, 0, step=1) * 10000
                        ins_end_age = st.slider("납입 종료 연령", 30, 80, 65)
                        ins_surrender = st.number_input("해약환급금 (만원)", 0, 100_000_000, 0, step=100) * 10000
                        ins_maturity = st.number_input("만기/수령 예상금액 (만원)", 0, 100_000_000, 0, step=100) * 10000
                        if ins_type == "연금보험":
                            ins_payout = st.number_input("월 수령액 (만원, 연금형)", 0, 10000, 0, step=10) * 10000
                            ins_payout_start = st.slider("수령 개시 연령", 50, 85, 65)
                            ins_payout_period = st.slider("수령기간(년, 0=종신)", 0, 40, 0)
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
                    d_balance = st.number_input("잔액 (만원)", 0, 1_000_000,
                                                int(d['balance'] // 10000), step=100) * 10000
                    d_rate = st.slider("이율 (%)", 0.0, 15.0,
                        round(d['interest_rate'] * 100, 1), step=0.5) / 100
                    d_payment = st.number_input("월 상환액 (만원)", 0, 10000,
                                                int(d['monthly_payment'] // 10000), step=10) * 10000
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
                        d_balance = st.number_input("잔액 (만원)", 0, 1_000_000, 0, step=100) * 10000
                        d_rate = st.slider("이율 (%)", 0.0, 15.0, 4.5, step=0.5) / 100
                        d_payment = st.number_input("월 상환액 (만원)", 0, 10000, 0, step=10) * 10000
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
    with tabs[3]:
        st.subheader("은퇴 후 월 예상 지출")
        living    = st.number_input("기본 생활비 (만원)", min_value=0, max_value=2000, step=10, key="inp_living") * 10000
        medical   = st.number_input("의료비 (만원)", min_value=0, max_value=1000, step=10, key="inp_medical") * 10000
        leisure   = st.number_input("여가/취미 (만원)", min_value=0, max_value=1000, step=10, key="inp_leisure") * 10000
        family    = st.number_input("자녀/부모 지원 (만원)", min_value=0, max_value=1000, step=10, key="inp_family") * 10000
        insurance = st.number_input("보험료 (만원)", min_value=0, max_value=1000, step=10, key="inp_insurance") * 10000
        other     = st.number_input("기타 (만원)", min_value=0, max_value=1000, step=10, key="inp_other") * 10000
        total_monthly = living + medical + leisure + family + insurance + other
        st.metric("월 지출 합계", fmt_won(total_monthly))

    # ----------------------------------------------------------
    # 탭 5: 분석
    # ----------------------------------------------------------
    with tabs[4]:
        st.subheader("종합 분석 실행")

        inf_rate = st.slider("물가상승률 (%)", min_value=0.0, max_value=5.0, step=0.1, key="inp_inflation") / 100

        if st.button("🔍 은퇴설계 분석하기", type="primary", width='stretch'):
            ss = st.session_state
            payload = {
                "personal": {
                    "name": name, "birth_year": birth_year,
                    "birth_month": birth_month, "birth_day": birth_day,
                    "gender": gender, "retirement_age": retirement_age,
                    "expected_lifespan": expected_lifespan, "dependents": dependents,
                    "spouse_nps_monthly":    ss.get("inp_spouse_nps", 0) * 10000,
                    "spouse_nps_start_age":  ss.get("inp_spouse_nps_age", 65),
                    "spouse_other_monthly":  ss.get("inp_spouse_other", 0) * 10000,
                    "spouse_other_start_age": ss.get("inp_spouse_other_age", 65),
                },
                "current_income": {
                    "annual_salary": annual_salary, "annual_bonus": annual_bonus,
                    "is_employee": is_employee,
                    "parttime_monthly": ss.get("inp_parttime_monthly", 0) * 10000,
                    "parttime_until_age": ss.get("inp_parttime_until", 70),
                },
                "inflation_rate": inf_rate,
                "pensions": st.session_state.pensions,
                "real_estates": st.session_state.real_estates,
                "financial_assets": st.session_state.financial_assets,
                "memberships": st.session_state.memberships,
                "vehicles": st.session_state.vehicles,
                "debts": st.session_state.debts,
                "insurances": st.session_state.insurances,
                "expected_expense": {
                    "living_cost": living, "medical_cost": medical,
                    "leisure_cost": leisure, "family_support": family,
                    "insurance_premium": insurance, "other": other,
                },
            }
            with st.spinner("분석 중..."):
                result, err = call_api("/analyze", payload)
            if err:
                st.error(err)
            else:
                st.session_state.analysis_result = result
                # 연금조정 슬라이더를 저장된 값으로 리셋
                st.session_state.adj_payout = {}
                st.session_state.adj_start_age = {}
                st.session_state.pop('adj_nps_age', None)
                st.success("✅ 분석 완료!")
                # 분석 시 자동 저장
                _ap = _build_save_payload()
                _apid = st.session_state.profile_id
                _ar, _ae = call_api(f"/profiles/{_apid}", _ap, method="PUT") if _apid and _apid != 0 else call_api("/profiles", _ap)
                if not _ae:
                    st.session_state.profile_id = _ar.get('id', _apid)

        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            st.divider()

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

            # ── 월 수입 상세 내역 ──────────────────────────────
            _income_detail = result.get('예상수입', {})
            _income_items = _income_detail.get('항목별', {})
            if _income_items:
                with st.expander("📋 월 수입 계산 내역", expanded=False):
                    _total = 0
                    for _src, _amt in _income_items.items():
                        _pct = (_amt / cf['월수입'] * 100) if cf.get('월수입') else 0
                        c_l, c_r = st.columns([3, 2])
                        with c_l:
                            st.markdown(f"**{_src}**")
                        with c_r:
                            st.markdown(f"{fmt_won(_amt)} ({_pct:.0f}%)")
                        _total += _amt
                    st.divider()
                    c_l, c_r = st.columns([3, 2])
                    with c_l:
                        st.markdown("**합계**")
                    with c_r:
                        st.markdown(f"**{fmt_won(_total)}**")

                    # 지출 항목도 함께 표시
                    st.markdown("##### 월 지출 구성")
                    _exp_items = {
                        "생활비": cf.get('월지출_생활', 0),
                        "세금·건보료": cf.get('월지출_세금건보', 0),
                        "회원권 연회비": cf.get('월지출_회원권', 0),
                        "차량 유지비": cf.get('월지출_차량', 0),
                    }
                    _exp_total = cf.get('월지출_합계', 0)
                    for _src, _amt in _exp_items.items():
                        if _amt:
                            _pct = (_amt / _exp_total * 100) if _exp_total else 0
                            c_l, c_r = st.columns([3, 2])
                            with c_l:
                                st.markdown(f"**{_src}**")
                            with c_r:
                                st.markdown(f"{fmt_won(_amt)} ({_pct:.0f}%)")
                    st.divider()
                    c_l, c_r = st.columns([3, 2])
                    with c_l:
                        st.markdown("**합계**")
                    with c_r:
                        st.markdown(f"**{fmt_won(_exp_total)}**")

            # ── 나이별 수령액 시나리오 그래프 ──────────────────────
            _age_rows = result.get('나이별수입', [])
            if _age_rows:
                st.divider()
                with st.expander("📅 나이별 월수입 시나리오", expanded=True):
                    st.caption("연금 개시 연령에 따라 수입이 늘어나는 구간을 보여줍니다.")

                    # 5년 단위 데이터만 사용 (55 ~ 기대수명)
                    _max_age = _age_rows[-1]['나이'] if _age_rows else 90
                    _tick_ages = list(range(55, _max_age + 1, 5))
                    if _max_age not in _tick_ages:
                        _tick_ages.append(_max_age)
                    _age_map = {r['나이']: r for r in _age_rows}

                    _retire_age = result.get('사용자정보', {}).get('희망은퇴연령', 60)

                    _records = []
                    _total_records = []
                    _tax_records = []
                    for _age in _tick_ages:
                        _row = _age_map.get(_age)
                        if _row is None:
                            continue
                        _total_records.append({
                            '나이': _age,
                            '월합계(만원)': round(_row['월수입'] / 10000, 1),
                        })
                        _tax_records.append({
                            '나이': _age,
                            '세금+건보(만원)': round(_row.get('월세금', 0) / 10000, 1),
                        })
                        for _src, _amt in _row['항목별'].items():
                            _records.append({
                                '나이': _age,
                                '항목': _src,
                                '월수입(만원)': round(_amt / 10000, 1),
                            })

                    _df = pd.DataFrame(_records)
                    _df_total = pd.DataFrame(_total_records)
                    _df_tax = pd.DataFrame(_tax_records)

                    _x_axis = alt.Axis(
                        values=_tick_ages, format='d', labelExpr="datum.value + '세'",
                    )
                    _x_scale = alt.Scale(domain=[55, _max_age])

                    if not _df.empty:
                        # 누적 영역 차트
                        _area = alt.Chart(_df).mark_area(
                            opacity=0.65, interpolate='monotone'
                        ).encode(
                            x=alt.X('나이:Q', title='나이', scale=_x_scale, axis=_x_axis),
                            y=alt.Y('월수입(만원):Q', stack='zero'),
                            color=alt.Color('항목:N', legend=alt.Legend(title='수입원', orient='bottom', columns=3)),
                            tooltip=[
                                alt.Tooltip('나이:Q', title='나이'),
                                alt.Tooltip('항목:N', title='항목'),
                                alt.Tooltip('월수입(만원):Q', title='금액(만원)', format='.0f'),
                            ],
                        )
                        # 합계 꺾은선
                        _line = alt.Chart(_df_total).mark_line(
                            color='#1565c0', strokeWidth=2.5, point=True
                        ).encode(
                            x=alt.X('나이:Q', scale=_x_scale, axis=_x_axis),
                            y=alt.Y('월합계(만원):Q'),
                            tooltip=[
                                alt.Tooltip('나이:Q', title='나이'),
                                alt.Tooltip('월합계(만원):Q', title='월합계(만원)', format='.0f'),
                            ],
                        )
                        _base_expense = cf.get('월지출_합계', 0) / 10000
                        _inf = st.session_state.get('inp_inflation', 2.5) / 100
                        _df_expense_rows = []
                        for _age in _tick_ages:
                            years_from_retire = max(0, _age - _retire_age)
                            _df_expense_rows.append({
                                '나이': _age,
                                '월지출(만원)': round(_base_expense * (1 + _inf) ** years_from_retire, 1)
                            })
                        _df_expense = pd.DataFrame(_df_expense_rows)
                        _exp_line = alt.Chart(_df_expense).mark_line(
                            color='#e53935', strokeWidth=2, strokeDash=[6, 3]
                        ).encode(
                            x=alt.X('나이:Q', scale=_x_scale, axis=_x_axis),
                            y=alt.Y('월지출(만원):Q'),
                            tooltip=[alt.Tooltip('나이:Q', title='나이'), alt.Tooltip('월지출(만원):Q', title='지출(만원)', format='.0f')]
                        )
                        # 세금+건보료 선
                        _tax_line = alt.Chart(_df_tax).mark_line(
                            color='#546e7a', strokeWidth=2, strokeDash=[4, 2], point=True
                        ).encode(
                            x=alt.X('나이:Q', scale=_x_scale, axis=_x_axis),
                            y=alt.Y('세금+건보(만원):Q'),
                            tooltip=[
                                alt.Tooltip('나이:Q', title='나이'),
                                alt.Tooltip('세금+건보(만원):Q', title='세금+건보(만원)', format='.1f'),
                            ],
                        )
                        # 은퇴 기준선
                        _r_df = pd.DataFrame([{'x': float(_retire_age)}])
                        _r_rule = alt.Chart(_r_df).mark_rule(
                            color='#ff6f00', strokeWidth=2.5, strokeDash=[6, 3]
                        ).encode(x=alt.X('x:Q', scale=_x_scale))
                        _r_txt = alt.Chart(_r_df).mark_text(
                            color='#ff6f00', fontSize=10, fontWeight='bold', align='left', dx=5
                        ).encode(
                            x=alt.X('x:Q', scale=_x_scale),
                            y=alt.value(12),
                            text=alt.value(f'은퇴 {_retire_age}세'),
                        )
                        st.altair_chart(
                            (_area + _line + _exp_line + _tax_line + _r_rule + _r_txt).properties(height=320),
                            width='stretch',
                        )
                        st.caption("🟠 주황 점선: 은퇴 시점 / 🔴 빨간 점선: 물가반영 월지출 / 파란선: 월수입 합계 / 🔵 회색 점선: 세금+건보")

                    # 구간별 요약 테이블 (연금 개시 시점만)
                    _prev_total = 0
                    for _row in _age_rows:
                        _items = _row['항목별']
                        _prev_items = _age_rows[max(0, _age_rows.index(_row) - 1)]['항목별']
                        if _items != _prev_items or _row == _age_rows[0]:
                            _new_srcs = [k for k in _items if k not in _prev_items]
                            _total = _row['월수입']
                            _tax = _row.get('월세금', 0)
                            _delta = _total - _prev_total
                            _delta_str = f" (+{fmt_won(_delta)})" if _delta > 0 else ""
                            _src_str = " + ".join(_new_srcs) if _new_srcs else "—"
                            _tax_str = f" &nbsp;|&nbsp; 세금+건보 **{fmt_won(_tax)}**" if _tax > 0 else ""
                            st.markdown(
                                f"**{_row['나이']}세~** &nbsp; 월 **{fmt_won(_total)}**{_delta_str}{_tax_str}"
                                + (f"  \n&nbsp;&nbsp;&nbsp;🆕 {_src_str} 수령 시작" if _new_srcs else "")
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

            with st.expander("💼 연금별 수령액", expanded=True):
                _TAX_ICON = {
                    '비과세': '🟢', '저율분리과세': '🟡', '분리과세': '🟠', '종합': '🔴',
                }
                _cur_year = _date.today().year
                _cur_age  = _cur_year - birth_year
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
                dep = tax_info.get('피부양자_가능여부', {})
                if dep.get('eligible'):
                    st.success("✅ 피부양자 등재 가능 (배우자 직장가입자 있을 시)")
                else:
                    st.warning(f"❌ 피부양자 불가: {', '.join(dep.get('reasons_disqualified', []))}")
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

            _nps_scens_pre = result.get('시나리오비교', {}).get('국민연금_수급시기', [])
            if _nps_scens_pre:
                _nps_normal_pre = next((s['start_age'] for s in _nps_scens_pre if s.get('diff_from_normal') == 0), None)
                with st.expander("📋 국민연금 시나리오 보기", expanded=False):
                    for s in _nps_scens_pre:
                        marker = " ⭐" if s['start_age'] == _nps_normal_pre else ""
                        st.text(f"{s['start_age']}세: 월 {fmt_won(s['monthly_amount'])} / 총 {fmt_won(s['total_payout'])}{marker}")
                    st.caption("⭐ = 정상 수급연령 · 총액은 기대수명까지 합산")
                    st.markdown("🔗 [국민연금공단 예상연금 모의계산](https://csa.nps.or.kr/ib2010/mvc/pension/pensionCalculation.do)")

            _private_scens_pre = result.get('현금흐름_보완', {}).get('사적연금_기간별', [])
            for ps in _private_scens_pre:
                pname = ps['연금명']
                kind = ps['종류']
                cur_y = ps['현재_기간']
                start_age_sc = ps.get('수령시작_연령', 65)
                with st.expander(f"📊 {pname} ({kind}) 수령기간별 시나리오", expanded=False):
                    for k, v in sorted(ps['기간별'].items(), key=lambda x: int(x[0])):
                        years = int(k)
                        monthly = v['monthly'] if isinstance(v, dict) else v
                        total = v['total'] if isinstance(v, dict) else monthly * 12 * years
                        end_age = start_age_sc + years - 1
                        marker = " ⭐" if years == cur_y else ""
                        st.text(f"{years}년 (~{end_age}세): 월 {fmt_won(monthly)} / 총 {fmt_won(total)}{marker}")

            hp = result.get('주택연금', {})
            if hp.get('eligible'):
                with st.expander("🏠 주택연금 (비과세)", expanded=False):
                    st.metric("예상 월 수령액", fmt_won(hp.get('monthly_payout', 0)))
                    st.caption(f"공시가격 {fmt_won(hp.get('house_value_used', 0))} 기준, {hp.get('age_at_start')}세 가입시")
                    st.markdown(
                        "🔗 [주택금융공사 — 주택연금 예상수령액 계산](https://www.hf.go.kr/hf/sub03/sub01.do)  \n"
                        "🔗 [주택연금 가입 조건·지급 방식 안내](https://www.hf.go.kr/hf/sub03/sub03.do)"
                    )

            # ── 퇴직연금 포트폴리오 시나리오 ──────────────────────
            _pf_scenarios = result.get('퇴직연금_포트폴리오', [])
            if _pf_scenarios:
                st.divider()
                st.markdown("### 📊 퇴직연금 포트폴리오 유형별 비교")
                st.caption("DC형·IRP·연금저축의 운용 방식을 바꿀 경우 예상 수령액 변화입니다.")
                for _pf in _pf_scenarios:
                    with st.expander(f"**{_pf['연금명']}** ({_pf['종류']}) — 현재 {_pf['현재_수익률']*100:.1f}%", expanded=True):
                        _scenarios = _pf['시나리오']
                        for _row_start in range(0, len(_scenarios), 2):
                            _row = _scenarios[_row_start:_row_start + 2]
                            _cols = st.columns(len(_row))
                            for _ci, _sc in enumerate(_row):
                                with _cols[_ci]:
                                    _is_cur = _sc['현재설정']
                                    _delta = _sc['월수령액_증감']
                                    if _is_cur:
                                        _delta_str = ""
                                        _delta_color = "inherit"
                                    elif _delta > 0:
                                        _delta_str = f"▲ +{fmt_won(_delta)}"
                                        _delta_color = "#66bb6a"
                                    elif _delta < 0:
                                        _delta_str = f"▼ {fmt_won(_delta)}"
                                        _delta_color = "#ef5350"
                                    else:
                                        _delta_str = "기준"
                                        _delta_color = "inherit"
                                    _badge = "✅ " if _is_cur else ""
                                    _bg = "rgba(76,175,80,0.15)" if _is_cur else "rgba(128,128,128,0.07)"
                                    _border = "rgba(76,175,80,0.5)" if _is_cur else "rgba(128,128,128,0.25)"
                                    st.markdown(f"""
<div style="text-align:center;padding:14px 8px;background:{_bg};
     border-radius:12px;border:1px solid {_border};margin-bottom:8px;">
  <div style="font-size:12px;opacity:0.75;margin-bottom:6px;word-break:keep-all;">
    {_badge}{_sc['유형']}<br><span style="font-size:11px;">({_sc['수익률']*100:.1f}%)</span>
  </div>
  <div style="font-size:20px;font-weight:700;">{fmt_won(_sc['월수령액'])}</div>
  <div style="font-size:11px;opacity:0.6;margin-top:4px;">적립금 {fmt_won(_sc['수령시점_적립금'])}</div>
  <div style="font-size:12px;font-weight:600;color:{_delta_color};margin-top:4px;">{_delta_str}</div>
</div>""", unsafe_allow_html=True)

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

                _sel = _nps_age_map[sel_nps_age]
                _cur_nps_info = _nps_age_map.get(_cur_nps_age, _nps_age_map[_normal_age])
                _delta_nps = _sel['monthly_amount'] - _cur_nps_info['monthly_amount']

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
                    st.success(f"{sel_nps_age}세 수급으로 적용 완료! 저장 후 재분석하세요.")
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

                def _calc_balance(ps, new_start_age):
                    cb  = ps.get('_current_balance', 0)
                    pmt = ps.get('_monthly_contribution', 0)
                    ca  = ps.get('_current_age', 40)
                    ea  = ps.get('_contribution_end_age', 60)
                    r   = ps.get('_annual_return', 0.04)
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
                    # 옵션 밖이면 가장 가까운 값으로 스냅
                    if st.session_state.adj_payout.get(pname) not in _period_opts:
                        _snapped = min(_period_opts, key=lambda v: abs(v - cur_y))
                        st.session_state.adj_payout[pname] = _snapped
                    if pname not in st.session_state.adj_start_age:
                        st.session_state.adj_start_age[pname] = orig_start_age

                    with st.expander(f"**{pname}** ({kind})", expanded=True):
                        ca, cb = st.columns(2)
                        with ca:
                            sel_start = st.slider(
                                "수령 개시 연령",
                                min_value=50, max_value=85,
                                value=st.session_state.adj_start_age[pname],
                                step=1,
                                key=f"adj_sa_{pname}",
                            )
                            st.session_state.adj_start_age[pname] = sel_start
                        with cb:
                            sel_years = st.select_slider(
                                "수령기간 (년, 0=종신)",
                                options=_period_opts,
                                value=st.session_state.adj_payout[pname],
                                key=f"adj_sl_{pname}",
                            )
                            st.session_state.adj_payout[pname] = sel_years

                        # 개시연령이 바뀌면 잔액 재계산
                        if sel_start != orig_start_age and ps.get('_current_balance') is not None:
                            adj_balance = _calc_balance(ps, sel_start)
                        else:
                            adj_balance = ps.get('수령시점_적립금', 0)

                        adj_monthly = _monthly_payout(adj_balance, sel_start, sel_years, rate)
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
                                      f"{orig_start_age}세 / {cur_y}년",
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

                # 현재 연금에 기간/개시연령 반영 버튼
                if st.button("✅ 조정값 연금에 적용", width='stretch'):
                    for ps in pension_scenarios:
                        pname = ps['연금명']
                        new_y = st.session_state.adj_payout.get(pname, ps['현재_기간'])
                        new_a = st.session_state.adj_start_age.get(pname, ps.get('수령시작_연령', 65))
                        for i, p in enumerate(st.session_state.pensions):
                            if p['name'] == pname:
                                st.session_state.pensions[i]['payout_period_years'] = new_y
                                st.session_state.pensions[i]['expected_start_age'] = new_a
                    st.success("적용 완료! 분석탭에서 재분석하세요.")
                    st.session_state.analysis_result = None
                    st.rerun()

            st.divider()
            st.download_button(
                "📥 결과 JSON 다운로드",
                data=json.dumps(result, ensure_ascii=False, indent=2, default=str),
                file_name=f"retirement_analysis_{name}.json",
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
    if st.session_state.profile_id is None:
        _prof, _err = call_api("/profiles/latest", method="GET")
        if not _err and _prof and _prof.get('id'):
            _restore_from_profile(_prof)
        else:
            st.session_state.profile_id = 0  # 프로필 없음 표시
        st.rerun()
    show_main_app()
