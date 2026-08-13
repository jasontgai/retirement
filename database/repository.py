"""
DB CRUD 작업 - Profile / AnalysisResult / UserActivity
"""
import json
import re as _re
from datetime import date
from sqlalchemy.orm import Session
from database.orm_models import Profile, PensionRow, RealEstateRow, FinancialAssetRow, MembershipRow, VehicleRow, DebtRow, InsuranceRow, AnalysisResult


# ============================================================
# Profile 저장 (신규 생성)
# ============================================================

def save_profile(db: Session, user_id: int, user_profile, title: str = "기본 플랜") -> Profile:
    """UserProfile 데이터클래스 → DB 저장 후 Profile 반환"""
    p = user_profile.personal
    inc = user_profile.current_income
    exp = user_profile.expected_expense

    row = Profile(
        user_id=user_id,
        title=title,
        name=p.name,
        birth_date=p.birth_date,
        gender=p.gender.value,
        retirement_age=p.retirement_age,
        expected_lifespan=p.expected_lifespan,
        spouse_birth_date=p.spouse_birth_date,
        dependents=p.dependents,
        spouse_nps_monthly=int(p.spouse_nps_monthly),
        spouse_nps_start_age=p.spouse_nps_start_age,
        spouse_other_monthly=int(p.spouse_other_monthly),
        spouse_other_start_age=p.spouse_other_start_age,
        annual_salary=int(inc.annual_salary),
        annual_bonus=int(inc.annual_bonus),
        other_income=int(inc.other_income),
        is_employee=inc.is_employee,
        parttime_monthly=int(inc.parttime_monthly),
        parttime_until_age=inc.parttime_until_age,
        living_cost=int(exp.living_cost),
        medical_cost=int(exp.medical_cost),
        leisure_cost=int(exp.leisure_cost),
        family_support=int(exp.family_support),
        insurance_premium=int(exp.insurance_premium),
        other_expense=int(exp.other),
    )
    db.add(row)
    db.flush()  # ID 확보

    for pension in user_profile.pensions:
        db.add(PensionRow(
            profile_id=row.id,
            pension_type=pension.pension_type.value,
            name=pension.name,
            current_balance=int(pension.current_balance),
            monthly_contribution=int(pension.monthly_contribution),
            contribution_end_age=pension.contribution_end_age,
            expected_start_age=pension.expected_start_age,
            expected_monthly_payout=int(pension.expected_monthly_payout),
            annual_return_rate=pension.annual_return_rate,
            payout_period_years=pension.payout_period_years,
            contribution_years=pension.contribution_years,
        ))

    for re in user_profile.real_estates:
        db.add(RealEstateRow(
            profile_id=row.id,
            name=re.name,
            house_type=re.house_type.value,
            property_category=getattr(re, 'property_category', '아파트'),
            market_value=int(re.market_value),
            official_price=int(re.official_price),
            debt=int(re.debt),
            monthly_rent_income=int(re.monthly_rent_income),
            monthly_rent_expense=int(re.monthly_rent_expense),
            is_primary_residence=re.is_primary_residence,
            acquisition_date=re.acquisition_date,
            acquisition_price=int(re.acquisition_price),
        ))

    for fa in user_profile.financial_assets:
        db.add(FinancialAssetRow(
            profile_id=row.id,
            name=fa.name,
            asset_type=fa.asset_type,
            amount=int(fa.amount),
            annual_return_rate=fa.annual_return_rate,
            is_taxable=fa.is_taxable,
        ))

    for m in user_profile.memberships:
        db.add(MembershipRow(
            profile_id=row.id,
            name=m.name,
            membership_type=m.membership_type,
            market_value=int(m.market_value),
            acquisition_price=int(m.acquisition_price),
            annual_dues=int(m.annual_dues),
        ))

    for v in user_profile.vehicles:
        db.add(VehicleRow(
            profile_id=row.id,
            name=v.name,
            market_value=int(v.market_value),
            annual_cost=int(v.annual_cost),
            purchase_year=v.purchase_year,
        ))

    for d in user_profile.debts:
        db.add(DebtRow(
            profile_id=row.id,
            name=d.name,
            debt_type=d.debt_type,
            balance=int(d.balance),
            interest_rate=d.interest_rate,
            monthly_payment=int(d.monthly_payment),
            end_date=d.end_date,
        ))

    for ins in user_profile.insurances:
        db.add(InsuranceRow(
            profile_id=row.id,
            name=ins.name,
            insurance_type=ins.insurance_type,
            monthly_premium=int(ins.monthly_premium),
            premium_end_age=ins.premium_end_age,
            surrender_value=int(ins.surrender_value),
            maturity_value=int(ins.maturity_value),
            monthly_payout=int(ins.monthly_payout),
            payout_start_age=ins.payout_start_age,
            payout_period_years=ins.payout_period_years,
        ))

    db.commit()
    db.refresh(row)
    return row


# ============================================================
# Profile 조회
# ============================================================

def list_profiles(db: Session, user_id: int) -> list[Profile]:
    return db.query(Profile).filter(Profile.user_id == user_id).order_by(Profile.created_at.desc()).all()


def get_profile(db: Session, profile_id: int, user_id: int) -> Profile | None:
    return db.query(Profile).filter(Profile.id == profile_id, Profile.user_id == user_id).first()


def delete_profile(db: Session, profile_id: int, user_id: int) -> bool:
    row = get_profile(db, profile_id, user_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def upsert_profile(db: Session, user_id: int, user_profile, profile_id: int | None = None, title: str = "기본 플랜") -> Profile:
    """기존 프로필을 삭제 후 재생성 (유저당 1개 원칙 유지).
    profile_id가 없거나 이미 삭제된 경우 첫 번째 기존 프로필을 대신 교체."""
    target = get_profile(db, profile_id, user_id) if profile_id else None
    if target is None:
        # 지정 ID가 없거나 이미 삭제된 경우 → 첫 번째 기존 프로필 교체
        others = list_profiles(db, user_id)
        target = others[0] if others else None
    if target:
        db.delete(target)
        # commit 하지 않음 — save_profile의 commit이 delete+insert를 한 번에 처리
    return save_profile(db, user_id, user_profile, title)


# ============================================================
# 분석 결과 저장 / 조회
# ============================================================

def save_analysis(db: Session, profile_id: int, result: dict) -> AnalysisResult:
    row = AnalysisResult(
        profile_id=profile_id,
        result_json=json.dumps(result, ensure_ascii=False, default=str),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_analyses(db: Session, profile_id: int) -> list[AnalysisResult]:
    return (
        db.query(AnalysisResult)
        .filter(AnalysisResult.profile_id == profile_id)
        .order_by(AnalysisResult.created_at.desc())
        .all()
    )


def get_analysis(db: Session, analysis_id: int, profile_id: int) -> AnalysisResult | None:
    return db.query(AnalysisResult).filter(
        AnalysisResult.id == analysis_id,
        AnalysisResult.profile_id == profile_id,
    ).first()


# ============================================================
# 사용자 활동 로그
# ============================================================

def _parse_ua(ua_str: str) -> tuple[str, str, str]:
    """User-Agent → (browser, os_name, device_type)"""
    ua = ua_str or ""
    if _re.search(r'Mobile|iPhone', ua) and not _re.search(r'iPad', ua):
        device_type = "mobile"
    elif _re.search(r'iPad|Tablet', ua):
        device_type = "tablet"
    else:
        device_type = "desktop"

    if "Edg/" in ua or "Edge/" in ua:
        browser = "Edge"
    elif "OPR/" in ua or "Opera/" in ua:
        browser = "Opera"
    elif "Chrome/" in ua and "Safari/" in ua:
        browser = "Chrome"
    elif "Firefox/" in ua:
        browser = "Firefox"
    elif "Safari/" in ua:
        browser = "Safari"
    elif "MSIE" in ua or "Trident/" in ua:
        browser = "IE"
    else:
        browser = "Other"

    if "Windows" in ua:
        os_name = "Windows"
    elif "Android" in ua:
        os_name = "Android"
    elif "iPhone" in ua or "iPad" in ua:
        os_name = "iOS"
    elif "Mac OS X" in ua:
        os_name = "macOS"
    elif "Linux" in ua:
        os_name = "Linux"
    else:
        os_name = "Other"

    return browser, os_name, device_type


def log_activity(
    db: Session,
    action: str,
    *,
    user_id: int | None = None,
    user_email: str | None = None,
    detail: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """활동 로그 기록 — 실패해도 예외를 전파하지 않음"""
    try:
        from database.orm_models import UserActivity
        browser, os_name, device_type = _parse_ua(user_agent)
        row = UserActivity(
            user_id=user_id,
            user_email=user_email,
            action=action,
            detail=json.dumps(detail, ensure_ascii=False) if detail else None,
            ip_address=(ip_address or "")[:45] or None,
            user_agent=(user_agent or "")[:500] or None,
            device_type=device_type,
            browser=browser,
            os_name=os_name,
        )
        db.add(row)
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


def get_activities(
    db: Session,
    *,
    limit: int = 100,
    offset: int = 0,
    user_id: int | None = None,
    action: str | None = None,
):
    from database.orm_models import UserActivity
    q = db.query(UserActivity)
    if user_id is not None:
        q = q.filter(UserActivity.user_id == user_id)
    if action:
        q = q.filter(UserActivity.action.like(f"%{action}%"))
    return q.order_by(UserActivity.created_at.desc()).offset(offset).limit(limit).all()

