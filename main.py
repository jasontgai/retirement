"""
은퇴설계 어플 메인 실행파일
- 샘플 사용자 데이터로 전체 분석 데모
- --db 플래그: 결과를 MySQL에 저장 (게스트 계정 자동 생성)
"""
import sys
import os
import json
import argparse
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.models import (
    UserProfile, PersonalInfo, Gender, Pension, PensionType,
    RealEstate, HouseType, FinancialAsset, Membership, Vehicle, Debt,
    CurrentIncome, ExpectedExpense,
)
from modules.analyzer import RetirementAnalyzer


def create_sample_profile() -> UserProfile:
    """샘플 사용자 프로필 생성 - 55세 남성, 일반적 자산 보유"""

    personal = PersonalInfo(
        name="홍길동",
        birth_date=date(1971, 5, 15),
        gender=Gender.MALE,
        retirement_age=60,
        expected_lifespan=90,
        spouse_birth_date=date(1973, 8, 20),
        dependents=1,
    )

    income = CurrentIncome(
        annual_salary=80_000_000,
        annual_bonus=10_000_000,
        is_employee=True,
    )

    pensions = [
        Pension(
            pension_type=PensionType.NPS,
            name="국민연금",
            contribution_end_age=60,
            expected_start_age=65,
            expected_monthly_payout=1_500_000,
            contribution_years=30,
        ),
        Pension(
            pension_type=PensionType.RETIREMENT_DC,
            name="회사 퇴직연금(DC)",
            current_balance=120_000_000,
            monthly_contribution=600_000,  # 회사 부담분
            contribution_end_age=60,
            expected_start_age=60,
            annual_return_rate=0.04,
            payout_period_years=20,
        ),
        Pension(
            pension_type=PensionType.IRP,
            name="개인 IRP",
            current_balance=50_000_000,
            monthly_contribution=500_000,
            contribution_end_age=60,
            expected_start_age=65,
            annual_return_rate=0.05,
            payout_period_years=20,
        ),
        Pension(
            pension_type=PensionType.PENSION_SAVINGS,
            name="연금저축펀드",
            current_balance=30_000_000,
            monthly_contribution=300_000,
            contribution_end_age=60,
            expected_start_age=65,
            annual_return_rate=0.06,
            payout_period_years=20,
        ),
    ]

    real_estates = [
        RealEstate(
            name="자가 (서울 아파트)",
            house_type=HouseType.OWN,
            market_value=1_500_000_000,
            official_price=1_050_000_000,
            debt=200_000_000,
            is_primary_residence=True,
            acquisition_date=date(2015, 3, 1),
            acquisition_price=900_000_000,
        ),
        RealEstate(
            name="투자용 오피스텔",
            house_type=HouseType.OWN,
            market_value=300_000_000,
            official_price=200_000_000,
            debt=0,
            monthly_rent_income=1_200_000,
            is_primary_residence=False,
        ),
    ]

    financial_assets = [
        FinancialAsset(
            name="은행 예금",
            asset_type="예금",
            amount=100_000_000,
            annual_return_rate=0.03,
        ),
        FinancialAsset(
            name="주식 포트폴리오",
            asset_type="주식",
            amount=80_000_000,
            annual_return_rate=0.07,
        ),
        FinancialAsset(
            name="채권형 펀드",
            asset_type="펀드",
            amount=50_000_000,
            annual_return_rate=0.04,
        ),
        FinancialAsset(
            name="ISA 계좌",
            asset_type="ETF",
            amount=20_000_000,
            annual_return_rate=0.06,
            is_taxable=False,
        ),
    ]

    memberships = [
        Membership(
            name="○○ 골프회원권",
            membership_type="golf",
            market_value=80_000_000,
            acquisition_price=120_000_000,
            annual_dues=2_400_000,
        ),
        Membership(
            name="△△ 콘도회원권",
            membership_type="condo",
            market_value=15_000_000,
            acquisition_price=20_000_000,
            annual_dues=600_000,
        ),
    ]

    vehicles = [
        Vehicle(
            name="제네시스 G80",
            market_value=40_000_000,
            annual_cost=4_000_000,  # 보험+세금+유류비
            purchase_year=2022,
        ),
    ]

    debts = [
        Debt(
            name="주택담보대출",
            debt_type="주담대",
            balance=200_000_000,
            interest_rate=0.045,
            monthly_payment=1_500_000,
        ),
    ]

    expense = ExpectedExpense(
        living_cost=2_500_000,
        medical_cost=500_000,
        leisure_cost=800_000,
        family_support=300_000,
        insurance_premium=300_000,
        other=200_000,
    )

    return UserProfile(
        personal=personal,
        current_income=income,
        pensions=pensions,
        real_estates=real_estates,
        financial_assets=financial_assets,
        memberships=memberships,
        vehicles=vehicles,
        debts=debts,
        expected_expense=expense,
    )


def print_section(title: str, data, indent: int = 0):
    """결과를 보기 좋게 출력"""
    prefix = "  " * indent
    if indent == 0:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print('='*70)
    else:
        print(f"\n{prefix}[{title}]")

    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                print_section(str(k), v, indent + 1)
            elif isinstance(v, (int, float)) and abs(v) > 100:
                print(f"{prefix}  - {k}: {v:,}")
            else:
                print(f"{prefix}  - {k}: {v}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                print(f"{prefix}  - 항목 {i+1}:")
                for k, v in item.items():
                    if isinstance(v, (int, float)) and abs(v) > 100:
                        print(f"{prefix}      {k}: {v:,}")
                    else:
                        print(f"{prefix}      {k}: {v}")
            else:
                print(f"{prefix}  - {item}")
    else:
        print(f"{prefix}  {data}")


def save_to_db(profile, results: dict, email: str, password: str, title: str) -> None:
    """분석 결과를 MySQL에 저장 (계정 없으면 자동 생성)"""
    from database.connection import SessionLocal, create_all_tables
    from database import auth as auth_utils
    from database import repository as repo

    create_all_tables()
    db = SessionLocal()
    try:
        user = auth_utils.get_user_by_email(db, email)
        if not user:
            user = auth_utils.create_user(db, email, password, name=profile.personal.name)
            print(f"  새 계정 생성: {email}")
        else:
            if not auth_utils.verify_password(password, user.password_hash):
                print("  오류: 비밀번호가 맞지 않습니다. DB 저장을 건너뜁니다.")
                return

        profile_row = repo.save_profile(db, user.id, profile, title=title)
        analysis_row = repo.save_analysis(db, profile_row.id, results)
        print(f"  프로필 저장 완료 (profile_id={profile_row.id})")
        print(f"  분석 결과 저장 완료 (analysis_id={analysis_row.id})")
    except Exception as e:
        print(f"  DB 저장 오류: {e}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="은퇴설계 종합분석")
    parser.add_argument("--db", action="store_true", help="분석 결과를 MySQL DB에 저장")
    parser.add_argument("--email", default="demo@retirement.app", help="DB 저장 계정 이메일")
    parser.add_argument("--password", default="demo1234!", help="DB 저장 계정 비밀번호")
    parser.add_argument("--title", default="샘플 분석", help="프로필 제목")
    args = parser.parse_args()

    print("\n" + "="*70)
    print(" "*20 + "은퇴설계 종합분석 리포트")
    print("="*70)

    # 1. 샘플 프로필 생성
    profile = create_sample_profile()

    # 2. 분석 실행
    analyzer = RetirementAnalyzer(profile)
    results = analyzer.analyze()

    # 3. 결과 출력
    print_section("1. 사용자 정보", results['사용자정보'])
    print_section("2. 자산 현황", results['자산현황'])
    print_section("3. 연금별 분석", results['연금분석'])
    print_section("4. 주택연금 가능성", results['주택연금'])
    print_section("5. 은퇴 후 예상 수입", results['예상수입'])
    print_section("6. 세금 및 건보료", results['세금건보료'])
    print_section("7. 월간 현금흐름", results['현금흐름'])
    print_section("8. 시나리오 비교", results['시나리오비교'])
    print_section("9. 핵심 제언", results['제언'])

    # 4. JSON 파일 저장
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'sample_analysis.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n분석결과 JSON 저장: {output_path}")

    # 5. DB 저장 (--db 플래그)
    if args.db:
        print("\n[DB 저장 중...]")
        save_to_db(profile, results, args.email, args.password, args.title)


if __name__ == "__main__":
    main()
