"""
은퇴설계 백엔드 API 서버
- FastAPI 기반 REST API
- 실행: uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
"""
import sys
import os
import json
import secrets
import hashlib
import time
import requests as http_client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
from datetime import date, datetime, timedelta
from typing import List, Optional
from urllib.parse import urlencode, quote

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.models import (
    UserProfile, PersonalInfo, Gender, Pension, PensionType,
    RealEstate, HouseType, FinancialAsset, Membership, Vehicle, Debt,
    Insurance, CurrentIncome, ExpectedExpense,
)
from modules.analyzer import RetirementAnalyzer
from modules.national_pension import get_pension_start_age, compare_start_age_scenarios
from modules.house_pension import estimate_house_pension, compare_sell_vs_pension
from modules.tax_calculator import (
    calculate_income_tax, calculate_health_insurance_local,
    check_dependent_eligibility,
)
from database.connection import get_db, create_all_tables
from database import auth as auth_utils
from database import repository as repo
from database.orm_models import PasswordResetToken, RevokedToken
from backend.email_sender import send_password_reset_email


app = FastAPI(
    title="은퇴설계 API",
    description="은퇴설계 종합분석 백엔드 API",
    version="0.2.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# ── 보안 헤더 미들웨어 ──────────────────────────────────────────
class _SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

# ── 로그인 브루트포스 방어 (IP당 1분에 5회) ────────────────────
_login_attempts: dict[str, list[float]] = {}

def _check_login_rate(ip: str) -> None:
    now = time.time()
    hits = [t for t in _login_attempts.get(ip, []) if now - t < 60]
    if len(hits) >= 5:
        raise HTTPException(status_code=429, detail="로그인 시도가 너무 많습니다. 1분 후 다시 시도하세요.")
    hits.append(now)
    _login_attempts[ip] = hits

_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
_ALLOWED_ORIGINS = (
    [o.strip() for o in _raw_origins.split(",") if o.strip()]
    if _raw_origins
    else ["http://localhost:8443", "http://127.0.0.1:8443"]
)

_allowed_hosts = ["kairang.pe.kr", "localhost", "127.0.0.1"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
app.add_middleware(_SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)

_static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

STREAMLIT_URL = os.getenv("STREAMLIT_URL", "http://localhost:8501")

_OAUTH_CONFIG = {
    "kakao": {
        "client_id":     os.getenv("KAKAO_CLIENT_ID", ""),
        "client_secret": os.getenv("KAKAO_CLIENT_SECRET", ""),
        "auth_url":  "https://kauth.kakao.com/oauth/authorize",
        "token_url": "https://kauth.kakao.com/oauth/token",
        "user_url":  "https://kapi.kakao.com/v2/user/me",
        "scope":     "profile_nickname account_email",
    },
    "naver": {
        "client_id":     os.getenv("NAVER_CLIENT_ID", ""),
        "client_secret": os.getenv("NAVER_CLIENT_SECRET", ""),
        "auth_url":  "https://nid.naver.com/oauth2.0/authorize",
        "token_url": "https://nid.naver.com/oauth2.0/token",
        "user_url":  "https://openapi.naver.com/v1/nid/me",
        "scope":     "",
    },
    "google": {
        "client_id":     os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "auth_url":  "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_url":  "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope":     "openid email profile",
    },
}

_oauth_states: dict[str, tuple[str, float]] = {}        # state -> (provider, timestamp)
_delete_pending: dict[str, tuple[int, str, float]] = {}  # state -> (user_id, provider, timestamp)


@app.on_event("startup")
def on_startup():
    create_all_tables()


# ============================================================
# 인증 의존성
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    payload = auth_utils.decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰이 유효하지 않습니다.")
    # 로그아웃된 토큰(블랙리스트) 체크
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if db.query(RevokedToken).filter(RevokedToken.token_hash == token_hash).first():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그아웃된 토큰입니다.")
    user = db.query(auth_utils.User).filter(auth_utils.User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다.")
    return user


# ============================================================
# Pydantic 입력 모델
# ============================================================

class RegisterIn(BaseModel):
    email: str
    password: str
    name: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    is_admin: bool = False


class PersonalInfoIn(BaseModel):
    name: str = "사용자"
    birth_year: int
    birth_month: int = 1
    birth_day: int = 1
    gender: str = "남"
    retirement_age: int = 60
    expected_lifespan: int = 90
    dependents: int = 0
    spouse_nps_monthly: float = 0
    spouse_nps_start_age: int = 65
    spouse_other_monthly: float = 0
    spouse_other_start_age: int = 65


class PensionIn(BaseModel):
    pension_type: str
    name: str
    current_balance: float = 0
    monthly_contribution: float = 0
    contribution_end_age: int = 60
    expected_start_age: int = 65
    expected_monthly_payout: float = 0
    annual_return_rate: float = 0.04
    payout_period_years: int = 20
    contribution_years: float = 0


class RealEstateIn(BaseModel):
    name: str
    house_type: str = "자가"
    market_value: float = 0
    official_price: float = 0
    debt: float = 0
    monthly_rent_income: float = 0
    is_primary_residence: bool = True


class FinancialAssetIn(BaseModel):
    name: str
    asset_type: str = "예금"
    amount: float = 0
    annual_return_rate: float = 0.03
    is_taxable: bool = True


class MembershipIn(BaseModel):
    name: str
    membership_type: str = "golf"
    market_value: float = 0
    annual_dues: float = 0


class VehicleIn(BaseModel):
    name: str
    market_value: float = 0
    annual_cost: float = 0


class DebtIn(BaseModel):
    name: str
    debt_type: str = "주담대"
    balance: float = 0
    interest_rate: float = 0.04
    monthly_payment: float = 0


class InsuranceIn(BaseModel):
    name: str
    insurance_type: str = "연금보험"
    monthly_premium: float = 0
    premium_end_age: int = 65
    surrender_value: float = 0
    maturity_value: float = 0
    monthly_payout: float = 0
    payout_start_age: int = 65
    payout_period_years: int = 0


class CurrentIncomeIn(BaseModel):
    annual_salary: float = 0
    annual_bonus: float = 0
    other_income: float = 0
    is_employee: bool = True
    parttime_monthly: float = 0
    parttime_until_age: int = 70


class ExpectedExpenseIn(BaseModel):
    living_cost: float = 2_500_000
    medical_cost: float = 300_000
    leisure_cost: float = 500_000
    family_support: float = 0
    insurance_premium: float = 200_000
    other: float = 0


class FullProfileIn(BaseModel):
    title: str = "기본 플랜"
    personal: PersonalInfoIn
    current_income: CurrentIncomeIn = Field(default_factory=CurrentIncomeIn)
    pensions: List[PensionIn] = []
    real_estates: List[RealEstateIn] = []
    financial_assets: List[FinancialAssetIn] = []
    memberships: List[MembershipIn] = []
    vehicles: List[VehicleIn] = []
    debts: List[DebtIn] = []
    insurances: List[InsuranceIn] = []
    expected_expense: ExpectedExpenseIn = Field(default_factory=ExpectedExpenseIn)
    inflation_rate: float = 0.025  # 2.5%


# ============================================================
# 변환 헬퍼
# ============================================================

_PENSION_TYPE_MAP = {
    "국민연금": PensionType.NPS,
    "퇴직연금DB": PensionType.RETIREMENT_DB,
    "퇴직연금DC": PensionType.RETIREMENT_DC,
    "IRP": PensionType.IRP,
    "연금저축": PensionType.PENSION_SAVINGS,
    "개인연금": PensionType.PRIVATE_PENSION,
    "주택연금": PensionType.HOUSE_PENSION,
}
_HOUSE_TYPE_MAP = {"자가": HouseType.OWN, "전세": HouseType.JEONSE, "월세": HouseType.WOLSE}


def pydantic_to_userprofile(data: FullProfileIn) -> UserProfile:
    p = data.personal
    personal = PersonalInfo(
        name=p.name,
        birth_date=date(p.birth_year, p.birth_month, p.birth_day),
        gender=Gender.MALE if p.gender == "남" else Gender.FEMALE,
        retirement_age=p.retirement_age,
        expected_lifespan=p.expected_lifespan,
        dependents=p.dependents,
        spouse_nps_monthly=p.spouse_nps_monthly,
        spouse_nps_start_age=p.spouse_nps_start_age,
        spouse_other_monthly=p.spouse_other_monthly,
        spouse_other_start_age=p.spouse_other_start_age,
    )
    pensions = [
        Pension(
            pension_type=_PENSION_TYPE_MAP.get(pn.pension_type, PensionType.IRP),
            name=pn.name,
            current_balance=pn.current_balance,
            monthly_contribution=pn.monthly_contribution,
            contribution_end_age=pn.contribution_end_age,
            expected_start_age=pn.expected_start_age,
            expected_monthly_payout=pn.expected_monthly_payout,
            annual_return_rate=pn.annual_return_rate,
            payout_period_years=pn.payout_period_years,
            contribution_years=pn.contribution_years,
        )
        for pn in data.pensions
    ]
    real_estates = [
        RealEstate(
            name=r.name,
            house_type=_HOUSE_TYPE_MAP.get(r.house_type, HouseType.OWN),
            market_value=r.market_value,
            official_price=r.official_price,
            debt=r.debt,
            monthly_rent_income=r.monthly_rent_income,
            is_primary_residence=r.is_primary_residence,
        )
        for r in data.real_estates
    ]
    financial_assets = [
        FinancialAsset(name=f.name, asset_type=f.asset_type, amount=f.amount,
                       annual_return_rate=f.annual_return_rate, is_taxable=f.is_taxable)
        for f in data.financial_assets
    ]
    memberships = [
        Membership(name=m.name, membership_type=m.membership_type,
                   market_value=m.market_value, annual_dues=m.annual_dues)
        for m in data.memberships
    ]
    vehicles = [Vehicle(name=v.name, market_value=v.market_value, annual_cost=v.annual_cost)
                for v in data.vehicles]
    debts = [Debt(name=d.name, debt_type=d.debt_type, balance=d.balance,
                  interest_rate=d.interest_rate, monthly_payment=d.monthly_payment)
             for d in data.debts]
    insurances = [
        Insurance(
            name=i.name, insurance_type=i.insurance_type,
            monthly_premium=i.monthly_premium, premium_end_age=i.premium_end_age,
            surrender_value=i.surrender_value, maturity_value=i.maturity_value,
            monthly_payout=i.monthly_payout, payout_start_age=i.payout_start_age,
            payout_period_years=i.payout_period_years,
        )
        for i in data.insurances
    ]
    income = CurrentIncome(
        annual_salary=data.current_income.annual_salary,
        annual_bonus=data.current_income.annual_bonus,
        other_income=data.current_income.other_income,
        is_employee=data.current_income.is_employee,
        parttime_monthly=data.current_income.parttime_monthly,
        parttime_until_age=data.current_income.parttime_until_age,
    )
    expense = ExpectedExpense(
        living_cost=data.expected_expense.living_cost,
        medical_cost=data.expected_expense.medical_cost,
        leisure_cost=data.expected_expense.leisure_cost,
        family_support=data.expected_expense.family_support,
        insurance_premium=data.expected_expense.insurance_premium,
        other=data.expected_expense.other,
    )
    return UserProfile(
        personal=personal, current_income=income, pensions=pensions,
        inflation_rate=data.inflation_rate,
        real_estates=real_estates, financial_assets=financial_assets,
        memberships=memberships, vehicles=vehicles, debts=debts,
        insurances=insurances, expected_expense=expense,
    )


# ============================================================
# 엔드포인트 - 기본
# ============================================================

@app.get("/")
def root():
    return {
        "service": "은퇴설계 API",
        "version": "0.2.0",
        "auth_endpoints": [
            "POST /auth/register  - 회원가입",
            "POST /auth/login     - 로그인 (JWT 발급)",
        ],
        "profile_endpoints": [
            "GET    /profiles           - 내 프로필 목록",
            "POST   /profiles           - 프로필 저장",
            "GET    /profiles/{id}      - 프로필 상세",
            "DELETE /profiles/{id}      - 프로필 삭제",
            "POST   /profiles/{id}/analyze       - 분석 실행 + 저장",
            "GET    /profiles/{id}/analyses      - 분석 이력",
            "GET    /profiles/{id}/analyses/{aid} - 분석 결과 상세",
        ],
        "stateless_endpoints": [
            "POST /analyze        - 비로그인 분석 (저장 안 됨)",
            "GET  /pension/start-age/{birth_year}",
            "POST /pension/scenarios",
            "POST /house-pension",
            "POST /tax/income",
            "POST /tax/health",
        ],
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ============================================================
# 인증 엔드포인트
# ============================================================

@app.post("/auth/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if auth_utils.get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
    user = auth_utils.create_user(db, data.email, data.password, data.name)
    token = auth_utils.create_access_token(user.id, user.email)
    return TokenOut(access_token=token, user_id=user.id, name=user.name,
                    is_admin=bool(getattr(user, 'is_admin', False)))


@app.post("/auth/login", response_model=TokenOut)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    _check_login_rate(request.client.host)
    user = auth_utils.get_user_by_email(db, form.username)
    if not user:
        raise HTTPException(status_code=401, detail="등록되지 않은 이메일입니다.")
    if not user.password_hash or not auth_utils.verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다.")
    token = auth_utils.create_access_token(user.id, user.email)
    return TokenOut(access_token=token, user_id=user.id, name=user.name,
                    is_admin=bool(getattr(user, 'is_admin', False)))


# ============================================================
# 비밀번호 재설정 (이메일 인증번호)
# ============================================================

class PasswordResetRequestIn(BaseModel):
    email: str

class PasswordResetConfirmIn(BaseModel):
    email: str
    code: str
    new_password: str

@app.post("/auth/password-reset/request", status_code=200)
def password_reset_request(data: PasswordResetRequestIn, db: Session = Depends(get_db)):
    """이메일로 6자리 인증번호 발송 (항상 200 반환 — 이메일 존재 여부 노출 방지)"""
    user = auth_utils.get_user_by_email(db, data.email)
    if user and user.password_hash:  # OAuth 전용 계정은 비밀번호 재설정 불가
        # 기존 미사용 토큰 만료 처리
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
        ).update({"used": True})

        # 6자리 숫자 인증번호 생성
        code = f"{secrets.randbelow(1_000_000):06d}"
        token_hash = hashlib.sha256(code.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        ))
        db.commit()
        sent = send_password_reset_email(user.email, user.name, code)
        if not sent:
            import logging
            logging.getLogger(__name__).warning(
                "비밀번호 재설정 이메일 발송 실패 — SMTP 설정을 확인하세요. (user_id=%s)", user.id
            )

    return {"message": "입력하신 이메일로 인증번호를 발송했습니다."}


@app.post("/auth/password-reset/confirm", status_code=200)
def password_reset_confirm(data: PasswordResetConfirmIn, db: Session = Depends(get_db)):
    """인증번호 확인 후 비밀번호 변경"""
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="비밀번호는 6자 이상이어야 합니다.")

    user = auth_utils.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=400, detail="인증번호가 올바르지 않거나 만료되었습니다.")

    token_hash = hashlib.sha256(data.code.encode()).hexdigest()
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow(),
    ).first()

    if not reset_token:
        raise HTTPException(status_code=400, detail="인증번호가 올바르지 않거나 만료되었습니다.")

    user.password_hash = auth_utils.hash_password(data.new_password)
    reset_token.used = True
    db.commit()

    return {"message": "비밀번호가 성공적으로 변경되었습니다."}


# ============================================================
# 프로필 CRUD (인증 필요)
# ============================================================

@app.get("/profiles")
def list_profiles(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profiles = repo.list_profiles(db, current_user.id)
    return [
        {
            "id": p.id,
            "title": p.title,
            "name": p.name,
            "retirement_age": p.retirement_age,
            "created_at": str(p.created_at),
            "updated_at": str(p.updated_at),
        }
        for p in profiles
    ]


@app.post("/profiles", status_code=201)
def create_profile(
    data: FullProfileIn,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_profile = pydantic_to_userprofile(data)
    row = repo.save_profile(db, current_user.id, user_profile, title=data.title)
    return {"id": row.id, "title": row.title, "created_at": str(row.created_at)}


def _serialize_profile(row) -> dict:
    bd = row.birth_date
    return {
        "id": row.id,
        "title": row.title,
        "personal": {
            "name": row.name,
            "birth_year": bd.year, "birth_month": bd.month, "birth_day": bd.day,
            "gender": row.gender,
            "retirement_age": row.retirement_age,
            "expected_lifespan": row.expected_lifespan,
            "dependents": row.dependents,
            "spouse_nps_monthly": row.spouse_nps_monthly,
            "spouse_nps_start_age": row.spouse_nps_start_age,
            "spouse_other_monthly": row.spouse_other_monthly,
            "spouse_other_start_age": row.spouse_other_start_age,
        },
        "current_income": {
            "annual_salary": row.annual_salary,
            "annual_bonus": row.annual_bonus,
            "is_employee": row.is_employee,
            "parttime_monthly": row.parttime_monthly,
            "parttime_until_age": row.parttime_until_age,
        },
        "pensions": [
            {
                "pension_type": p.pension_type, "name": p.name,
                "current_balance": p.current_balance,
                "monthly_contribution": p.monthly_contribution,
                "contribution_end_age": p.contribution_end_age,
                "expected_start_age": p.expected_start_age,
                "expected_monthly_payout": p.expected_monthly_payout,
                "annual_return_rate": p.annual_return_rate,
                "payout_period_years": p.payout_period_years,
                "contribution_years": p.contribution_years,
            } for p in row.pensions
        ],
        "real_estates": [
            {
                "name": r.name, "house_type": r.house_type,
                "market_value": r.market_value, "official_price": r.official_price,
                "debt": r.debt, "monthly_rent_income": r.monthly_rent_income,
                "is_primary_residence": r.is_primary_residence,
            } for r in row.real_estates
        ],
        "financial_assets": [
            {
                "name": f.name, "asset_type": f.asset_type, "amount": f.amount,
                "annual_return_rate": f.annual_return_rate, "is_taxable": f.is_taxable,
            } for f in row.financial_assets
        ],
        "memberships": [
            {
                "name": m.name, "membership_type": m.membership_type,
                "market_value": m.market_value, "annual_dues": m.annual_dues,
            } for m in row.memberships
        ],
        "vehicles": [
            {"name": v.name, "market_value": v.market_value, "annual_cost": v.annual_cost}
            for v in row.vehicles
        ],
        "debts": [
            {
                "name": d.name, "debt_type": d.debt_type, "balance": d.balance,
                "interest_rate": d.interest_rate, "monthly_payment": d.monthly_payment,
            } for d in row.debts
        ],
        "insurances": [
            {
                "name": i.name, "insurance_type": i.insurance_type,
                "monthly_premium": i.monthly_premium, "premium_end_age": i.premium_end_age,
                "surrender_value": i.surrender_value, "maturity_value": i.maturity_value,
                "monthly_payout": i.monthly_payout, "payout_start_age": i.payout_start_age,
                "payout_period_years": i.payout_period_years,
            } for i in row.insurances
        ],
        "expected_expense": {
            "living_cost": row.living_cost, "medical_cost": row.medical_cost,
            "leisure_cost": row.leisure_cost, "family_support": row.family_support,
            "insurance_premium": row.insurance_premium, "other": row.other_expense,
        },
        "created_at": str(row.created_at),
        "updated_at": str(row.updated_at),
    }


@app.get("/profiles/latest")
def get_latest_profile(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profiles = repo.list_profiles(db, current_user.id)
    if not profiles:
        return {}
    return _serialize_profile(profiles[0])


@app.get("/profiles/{profile_id}")
def get_profile(
    profile_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = repo.get_profile(db, profile_id, current_user.id)
    if not row:
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")
    return _serialize_profile(row)


@app.put("/profiles/{profile_id}")
def update_profile(
    profile_id: int,
    data: FullProfileIn,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_profile = pydantic_to_userprofile(data)
    row = repo.upsert_profile(db, current_user.id, user_profile,
                               profile_id=profile_id, title=data.title)
    return {"id": row.id, "title": row.title, "updated_at": str(row.updated_at)}


@app.delete("/profiles/{profile_id}", status_code=204)
def delete_profile(
    profile_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not repo.delete_profile(db, profile_id, current_user.id):
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")


# ============================================================
# 분석 실행 + 이력 (인증 필요)
# ============================================================

@app.post("/profiles/{profile_id}/analyze")
def analyze_and_save(
    profile_id: int,
    data: FullProfileIn,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """분석 실행 후 결과를 DB에 저장"""
    if not repo.get_profile(db, profile_id, current_user.id):
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")
    try:
        user_profile = pydantic_to_userprofile(data)
        results = RetirementAnalyzer(user_profile).analyze()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"분석 오류: {str(e)}")
    analysis = repo.save_analysis(db, profile_id, results)
    results["_meta"] = {"analysis_id": analysis.id, "saved_at": str(analysis.created_at)}
    return results


@app.get("/profiles/{profile_id}/analyses")
def list_analyses(
    profile_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not repo.get_profile(db, profile_id, current_user.id):
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")
    rows = repo.list_analyses(db, profile_id)
    return [{"id": r.id, "created_at": str(r.created_at)} for r in rows]


@app.get("/profiles/{profile_id}/analyses/{analysis_id}")
def get_analysis(
    profile_id: int,
    analysis_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not repo.get_profile(db, profile_id, current_user.id):
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")
    row = repo.get_analysis(db, analysis_id, profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
    import json
    return json.loads(row.result_json)


# ============================================================
# Stateless 분석 (비로그인 가능 - 저장 안 됨)
# ============================================================

@app.post("/analyze")
def analyze_stateless(profile: FullProfileIn):
    try:
        user_profile = pydantic_to_userprofile(profile)
        return RetirementAnalyzer(user_profile).analyze()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"분석 오류: {str(e)}")


@app.get("/pension/start-age/{birth_year}")
def get_start_age(birth_year: int):
    return {"birth_year": birth_year, "normal_start_age": get_pension_start_age(birth_year)}


class ScenarioRequest(BaseModel):
    base_monthly: float = Field(..., description="정상수급 월 예상금액")
    birth_year: int
    end_age: int = 90


@app.post("/pension/scenarios")
def pension_scenarios(req: ScenarioRequest):
    normal_age = get_pension_start_age(req.birth_year)
    return {
        "normal_age": normal_age,
        "scenarios": compare_start_age_scenarios(req.base_monthly, normal_age, req.end_age),
    }


class HousePensionRequest(BaseModel):
    house_value: float
    age: int = Field(..., ge=55)


@app.post("/house-pension")
def house_pension(req: HousePensionRequest):
    return estimate_house_pension(req.house_value, req.age)


class HousePensionCompareRequest(BaseModel):
    house_value: float
    age: int
    rental_income: float = 0
    end_age: int = 90
    investment_return: float = 0.03


@app.post("/house-pension/compare")
def house_pension_compare(req: HousePensionCompareRequest):
    return compare_sell_vs_pension(req.house_value, req.age, req.rental_income, req.end_age, req.investment_return)


class IncomeTaxRequest(BaseModel):
    taxable_income: float


@app.post("/tax/income")
def tax_income(req: IncomeTaxRequest):
    return calculate_income_tax(req.taxable_income)


class HealthInsuranceRequest(BaseModel):
    annual_pension_income: float = 0
    annual_financial_income: float = 0
    annual_other_income: float = 0
    property_value: float = 0


@app.post("/tax/health")
def tax_health(req: HealthInsuranceRequest):
    return calculate_health_insurance_local(
        req.annual_pension_income, req.annual_financial_income,
        req.annual_other_income, req.property_value,
    )


class DependentRequest(BaseModel):
    annual_income: float
    property_value: float
    has_business_income: bool = False


@app.post("/tax/dependent")
def tax_dependent(req: DependentRequest):
    return check_dependent_eligibility(req.annual_income, req.property_value, req.has_business_income)


# ============================================================
# 내 계정 관리 (인증 필요)
# ============================================================

@app.get("/auth/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "is_admin": bool(getattr(current_user, 'is_admin', False)),
        "oauth_provider": getattr(current_user, 'oauth_provider', None) or "",
        "created_at": str(current_user.created_at),
    }


def _revoke_token(token: str, db) -> None:
    """JWT 토큰을 블랙리스트에 등록"""
    payload = auth_utils.decode_token(token)
    if payload:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if not db.query(RevokedToken).filter(RevokedToken.token_hash == token_hash).first():
            exp = datetime.utcfromtimestamp(payload.get("exp", 0))
            db.add(RevokedToken(token_hash=token_hash, expires_at=exp))
            db.query(RevokedToken).filter(RevokedToken.expires_at < datetime.utcnow()).delete()
            db.commit()


@app.post("/auth/logout", status_code=200)
def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    _revoke_token(token, db)
    return {"message": "로그아웃되었습니다."}


@app.get("/auth/logout-page")
def logout_page(request: Request, deleted: bool = False, db: Session = Depends(get_db)):
    """브라우저 리다이렉트 방식 로그아웃 — HTTP Set-Cookie로 쿠키 삭제 후 앱으로 이동"""
    cookie_token = request.cookies.get("ret_token")
    if cookie_token:
        _revoke_token(cookie_token, db)

    dest = f"{STREAMLIT_URL}?account_deleted=true" if deleted else STREAMLIT_URL
    response = RedirectResponse(dest, status_code=302)
    for name in ["ret_token", "ret_uid", "ret_name", "ret_email"]:
        response.delete_cookie(key=name, path="/", samesite="lax")
    return response


class UpdateMeIn(BaseModel):
    current_password: str
    new_name: Optional[str] = None
    new_password: Optional[str] = None


@app.put("/auth/me")
def update_me(
    data: UpdateMeIn,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # OAuth 전용 계정은 비밀번호 검증 건너뜀
    if current_user.password_hash:
        if not data.current_password or not auth_utils.verify_password(data.current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")
    if data.new_name:
        current_user.name = data.new_name
    if data.new_password:
        if len(data.new_password) < 6:
            raise HTTPException(status_code=400, detail="비밀번호는 6자 이상이어야 합니다.")
        current_user.password_hash = auth_utils.hash_password(data.new_password)
    db.commit()
    return {"message": "업데이트 완료", "name": current_user.name}


class DeleteMeIn(BaseModel):
    current_password: str = ""


@app.delete("/auth/me", status_code=204)
def delete_me(
    data: DeleteMeIn,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.password_hash:
        if not data.current_password or not auth_utils.verify_password(data.current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="비밀번호가 올바르지 않습니다.")
    db.delete(current_user)
    db.commit()


# ============================================================
# 소셜 로그인 (OAuth2)
# ============================================================

def _callback_uri(provider: str) -> str:
    base = os.getenv("BACKEND_URL", "http://localhost:9080")
    return f"{base}/auth/callback/{provider}"


def _parse_oauth_user(provider: str, data: dict) -> tuple[str, str, str]:
    """(oauth_id, name, email) 파싱"""
    if provider == "kakao":
        oauth_id = str(data.get("id", ""))
        account = data.get("kakao_account", {})
        name = account.get("profile", {}).get("nickname", "카카오사용자")
        email = account.get("email", "")
    elif provider == "naver":
        r = data.get("response", {})
        oauth_id = str(r.get("id", ""))
        name = r.get("name") or r.get("nickname", "네이버사용자")
        email = r.get("email", "")
    else:  # google
        oauth_id = data.get("sub", "")
        name = data.get("name", "구글사용자")
        email = data.get("email", "")
    return oauth_id, name, email


@app.get("/auth/oauth/{provider}")
def oauth_start(provider: str):
    cfg = _OAUTH_CONFIG.get(provider)
    if not cfg:
        raise HTTPException(400, "지원하지 않는 플랫폼입니다.")
    if not cfg["client_id"]:
        provider_name = {"kakao": "카카오", "naver": "네이버", "google": "구글"}.get(provider, provider)
        raise HTTPException(400, f"{provider_name} 로그인은 현재 준비 중입니다. 곧 서비스될 예정입니다.")

    state = secrets.token_urlsafe(16)
    _oauth_states[state] = (provider, time.time())

    params: dict = {
        "client_id": cfg["client_id"],
        "redirect_uri": _callback_uri(provider),
        "response_type": "code",
        "state": state,
    }
    if cfg["scope"]:
        params["scope"] = cfg["scope"]
    if provider == "kakao":
        params["prompt"] = "login"
    elif provider == "naver":
        params["auth_type"] = "reauthenticate"

    return RedirectResponse(cfg["auth_url"] + "?" + urlencode(params))


def _exchange_oauth_token(provider: str, code: str) -> tuple[dict, str | None]:
    """OAuth 코드 → 사용자 정보. 성공 시 (user_data, None), 실패 시 ({}, 오류메시지)"""
    cfg = _OAUTH_CONFIG[provider]
    token_data = {
        "grant_type": "authorization_code",
        "client_id": cfg["client_id"],
        "code": code,
        "redirect_uri": _callback_uri(provider),
    }
    if cfg.get("client_secret"):
        token_data["client_secret"] = cfg["client_secret"]
    try:
        token_resp = http_client.post(
            cfg["token_url"],
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        if not token_resp.ok:
            return {}, f"token_error({token_resp.status_code}): {token_resp.text[:200]}"
        access_token = token_resp.json().get("access_token")
        user_resp = http_client.get(
            cfg["user_url"],
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        user_resp.raise_for_status()
        return user_resp.json(), None
    except Exception as exc:
        return {}, str(exc)


@app.get("/auth/callback/{provider}")
def oauth_callback(
    provider: str,
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db),
):
    fail_url = f"{STREAMLIT_URL}?oauth_error="

    if error or not code:
        return RedirectResponse(fail_url + quote(error or "cancelled"))

    # ── 탈퇴용 재인증 흐름 ──────────────────────────────────────
    if state and state.startswith("del:"):
        del_state = state[4:]
        pending = _delete_pending.pop(del_state, None)
        if not pending or pending[1] != provider or time.time() - pending[2] > 300:
            return RedirectResponse(fail_url + quote("탈퇴 인증이 만료되었습니다. 다시 시도하세요."))

        user_id, _, _ = pending
        user_data, err = _exchange_oauth_token(provider, code)
        if err:
            return RedirectResponse(fail_url + quote(err))

        oauth_id, _, _ = _parse_oauth_user(provider, user_data)
        if not oauth_id:
            return RedirectResponse(fail_url + quote("소셜 계정 정보를 가져올 수 없습니다."))

        # 재인증한 소셜 계정이 탈퇴 요청한 계정과 동일한지 확인
        verified = auth_utils.get_user_by_oauth(db, provider, oauth_id)
        if not verified or verified.id != user_id:
            return RedirectResponse(fail_url + quote("본인 확인 실패: 다른 계정으로 로그인하셨습니다."))

        db.delete(verified)
        db.commit()
        return RedirectResponse("/auth/logout-page?deleted=true")

    # ── 일반 로그인 흐름 ────────────────────────────────────────
    stored = _oauth_states.pop(state, None)
    if not stored or stored[0] != provider or time.time() - stored[1] > 300:
        return RedirectResponse(fail_url + "invalid_state")

    user_data, err = _exchange_oauth_token(provider, code)
    if err:
        return RedirectResponse(fail_url + quote(err))

    oauth_id, name, email = _parse_oauth_user(provider, user_data)
    if not oauth_id:
        return RedirectResponse(fail_url + "user_info_failed")
    if not email:
        email = f"{provider}_{oauth_id}@oauth.local"

    # 기존 OAuth 계정 조회 (provider + oauth_id)
    user = auth_utils.get_user_by_oauth(db, provider, oauth_id)
    if not user:
        existing = auth_utils.get_user_by_email(db, email)
        if existing and not existing.oauth_provider:
            # 이메일/비밀번호 계정에 소셜 연동 (ex. 이메일 가입 후 카카오로 로그인)
            existing.oauth_provider = provider
            existing.oauth_id = oauth_id
            db.commit()
            user = existing
        elif existing and existing.oauth_provider:
            # 다른 소셜 계정이 이미 같은 이메일 사용 중 → 별도 계정 생성
            user = auth_utils.create_oauth_user(
                db, f"{provider}_{oauth_id}@oauth.local", name, provider, oauth_id)
        else:
            user = auth_utils.create_oauth_user(db, email, name, provider, oauth_id)

    jwt_token = auth_utils.create_access_token(user.id, user.email)
    _is_admin = int(bool(getattr(user, 'is_admin', False)))
    _oauth_prov = getattr(user, 'oauth_provider', '') or ''
    return RedirectResponse(
        f"{STREAMLIT_URL}?token={jwt_token}"
        f"&user_id={user.id}"
        f"&name={quote(user.name)}"
        f"&email={quote(user.email)}"
        f"&is_admin={_is_admin}"
        f"&oauth_provider={_oauth_prov}"
    )


_delete_tokens: dict[str, tuple[int, str, float]] = {}  # dt -> (user_id, provider, timestamp)


@app.post("/auth/delete-request", status_code=200)
def delete_request(current_user=Depends(get_current_user)):
    """소셜 계정 탈퇴용 임시 토큰 발급 (5분 유효)"""
    provider = getattr(current_user, 'oauth_provider', None)
    if not provider:
        raise HTTPException(400, "소셜 로그인 계정이 아닙니다.")
    dt = secrets.token_urlsafe(24)
    _delete_tokens[dt] = (current_user.id, provider, time.time())
    return {"dt": dt}


@app.get("/auth/delete-start")
def delete_start(dt: str):
    """임시 토큰으로 OAuth 재인증 시작 (브라우저 리다이렉트)"""
    pending = _delete_tokens.pop(dt, None)
    if not pending or time.time() - pending[2] > 300:
        return RedirectResponse(f"{STREAMLIT_URL}?oauth_error=" + quote("탈퇴 요청이 만료되었습니다. 다시 시도하세요."))

    user_id, provider, _ = pending
    cfg = _OAUTH_CONFIG.get(provider)
    if not cfg or not cfg["client_id"]:
        return RedirectResponse(f"{STREAMLIT_URL}?oauth_error=" + quote("소셜 로그인 설정 오류"))

    state = secrets.token_urlsafe(16)
    _delete_pending[state] = (user_id, provider, time.time())

    params: dict = {
        "client_id": cfg["client_id"],
        "redirect_uri": _callback_uri(provider),
        "response_type": "code",
        "state": f"del:{state}",
    }
    if cfg["scope"]:
        params["scope"] = cfg["scope"]
    if provider == "kakao":
        params["prompt"] = "login"
    elif provider == "naver":
        params["auth_type"] = "reauthenticate"

    return RedirectResponse(cfg["auth_url"] + "?" + urlencode(params))


# ============================================================
# 시나리오 비교 (DB 기반 — GOOD / BEST / STANDARD)
# ============================================================

class ScenarioIn(BaseModel):
    label: str        # GOOD | BEST | STANDARD
    retire_age: int = 0
    monthly_income: int = 0
    monthly_expense: int = 0
    monthly_surplus: int = 0
    total_assets: int = 0
    detail: dict = {}


def require_admin(current_user=Depends(get_current_user)):
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")
    return current_user


def _scenario_row_to_dict(row) -> dict:
    return {
        "label":           row.label,
        "user_id":         row.user_id,
        "retire_age":      row.retire_age,
        "monthly_income":  row.monthly_income,
        "monthly_expense": row.monthly_expense,
        "monthly_surplus": row.monthly_surplus,
        "total_assets":    row.total_assets,
        "detail":          json.loads(row.detail_json) if row.detail_json else {},
    }


@app.get("/admin/users")
def admin_list_users(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    UserModel = auth_utils.User
    users = db.query(UserModel).order_by(UserModel.id).all()
    return [
        {
            "id":         u.id,
            "email":      u.email,
            "name":       u.name,
            "is_admin":   bool(u.is_admin),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@app.put("/admin/users/{user_id}/toggle-admin")
def admin_toggle_admin(
    user_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="자신의 관리자 권한은 변경할 수 없습니다.")
    UserModel = auth_utils.User
    u = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="사용자 없음")
    u.is_admin = not bool(u.is_admin)
    db.commit()
    return {"id": u.id, "email": u.email, "is_admin": bool(u.is_admin)}


@app.post("/scenarios", status_code=201)
def save_scenario(
    data: ScenarioIn,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    import traceback
    from database.orm_models import Scenario as ScenarioRow
    try:
        label = data.label.upper()
        row = db.query(ScenarioRow).filter(
            ScenarioRow.label == label,
        ).first()
        detail_json = json.dumps(data.detail, ensure_ascii=False)
        if row:
            row.retire_age      = data.retire_age
            row.monthly_income  = data.monthly_income
            row.monthly_expense = data.monthly_expense
            row.monthly_surplus = data.monthly_surplus
            row.total_assets    = data.total_assets
            row.detail_json     = detail_json
        else:
            db.add(ScenarioRow(
                user_id=None, label=label,
                retire_age=data.retire_age,
                monthly_income=data.monthly_income,
                monthly_expense=data.monthly_expense,
                monthly_surplus=data.monthly_surplus,
                total_assets=data.total_assets,
                detail_json=detail_json,
            ))
        db.commit()
        return {"label": label, "status": "saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"저장 오류: {traceback.format_exc()}")


@app.get("/scenarios")
def get_scenarios(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from database.orm_models import Scenario as ScenarioRow
    result = []
    for lbl in ("GOOD", "BEST", "STANDARD"):
        row = db.query(ScenarioRow).filter(
            ScenarioRow.label == lbl,
        ).first()
        if row:
            result.append(_scenario_row_to_dict(row))
    return result


@app.delete("/scenarios/{label}", status_code=204)
def delete_scenario(
    label: str,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from database.orm_models import Scenario as ScenarioRow
    label = label.upper()
    row = db.query(ScenarioRow).filter(
        ScenarioRow.label == label,
    ).first()
    if row:
        db.delete(row)
        db.commit()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000, reload=True)
