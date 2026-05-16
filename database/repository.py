"""
DB CRUD 작업 - Profile / AnalysisResult
"""
import json
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
            market_value=int(re.market_value),
            official_price=int(re.official_price),
            debt=int(re.debt),
            monthly_rent_income=int(re.monthly_rent_income),
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
    """기존 프로필 있으면 같은 트랜잭션에서 삭제 후 재생성 (원자적)"""
    if profile_id:
        existing = get_profile(db, profile_id, user_id)
        if existing:
            db.delete(existing)
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
