"""
사적연금 계산
- 퇴직연금 (DB/DC), IRP, 연금저축
- 적립금 미래가치 계산
- 분할수령시 세금 계산
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.tax_config import (
    PRIVATE_PENSION_TAX_BY_AGE,
    PRIVATE_PENSION_SEPARATE_LIMIT,
    PRIVATE_PENSION_HIGH_RATE,
)


def future_value(present_value: float, monthly_contribution: float,
                 annual_rate: float, years: float) -> float:
    """
    적립식 미래가치 계산
    FV = PV × (1+r)^n + PMT × [((1+r)^n - 1) / r]
    """
    if years <= 0:
        return present_value

    monthly_rate = annual_rate / 12
    months = int(years * 12)

    # 현재 적립금의 미래가치
    fv_pv = present_value * ((1 + monthly_rate) ** months)

    # 매월 납입금의 미래가치 (기말 납입 가정)
    if monthly_rate > 0:
        fv_pmt = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    else:
        fv_pmt = monthly_contribution * months

    return fv_pv + fv_pmt


def calculate_pension_payout(total_amount: float, start_age: int,
                              payout_years: int = 20,
                              annual_return: float = 0.03) -> dict:
    """
    적립금을 분할수령할 때 월 수령액 계산
    - 종신: payout_years=0 → 기대여명까지 단순 분할
    - 확정기간: 지정 기간 동안 수령
    """
    if payout_years <= 0:
        # 종신: 90세까지 가정 → (90 - start_age)년 수령
        payout_years = max(1, 90 - start_age)

    # 연금현가공식 역산: 월 수령액 계산
    # PV = PMT × [(1 - (1+r)^-n) / r]
    monthly_rate = annual_return / 12
    months = payout_years * 12

    if monthly_rate > 0:
        annuity_factor = (1 - (1 + monthly_rate) ** -months) / monthly_rate
        monthly_payout = total_amount / annuity_factor
    else:
        monthly_payout = total_amount / months

    return {
        'monthly_payout': round(monthly_payout),
        'annual_payout': round(monthly_payout * 12),
        'payout_years': payout_years,
        'end_age': start_age + payout_years - 1,
        'total_payout_nominal': round(monthly_payout * months),
    }


def get_pension_tax_rate_by_age(age: int) -> float:
    """연금수령 연령별 분리과세율"""
    for (start, end), rate in PRIVATE_PENSION_TAX_BY_AGE.items():
        if start <= age < end:
            return rate
    return 0.055


def calculate_pension_tax(annual_payout: float, age: int,
                          is_retirement_pension: bool = False) -> dict:
    """
    사적연금 수령시 세금 계산
    - 연 1,500만원 이하: 분리과세 (3.3~5.5%)
    - 연 1,500만원 초과: 종합과세 또는 16.5% 분리과세 선택

    is_retirement_pension=True: 퇴직금 재원 연금은 별도 (퇴직소득세 30~40% 감면)
    """
    base_rate = get_pension_tax_rate_by_age(age)

    if annual_payout <= PRIVATE_PENSION_SEPARATE_LIMIT:
        # 저율 분리과세
        tax = annual_payout * base_rate
        method = f"저율분리과세 ({base_rate*100:.1f}%)"
    else:
        # 한도 초과 → 두 가지 옵션
        # 옵션 1: 16.5% 분리과세
        option1_tax = annual_payout * PRIVATE_PENSION_HIGH_RATE
        # 옵션 2: 종합과세 (다른 소득과 합산 - 여기선 단순화)
        # 실제로는 다른 소득과 합산해야 정확
        tax = option1_tax
        method = f"분리과세 ({PRIVATE_PENSION_HIGH_RATE*100:.1f}%) 또는 종합과세 비교 필요"

    return {
        'annual_payout': round(annual_payout),
        'tax': round(tax),
        'after_tax': round(annual_payout - tax),
        'effective_rate': round(tax / annual_payout * 100, 2) if annual_payout > 0 else 0,
        'method': method,
    }


def project_pension_at_retirement(
    current_balance: float,
    monthly_contribution: float,
    current_age: int,
    contribution_end_age: int,
    payout_start_age: int,
    annual_return: float = 0.04,
) -> dict:
    """
    납입정보로부터 수령시점 적립금 추정
    """
    # 1단계: 납입종료시점까지 적립
    contribution_years = max(0, contribution_end_age - current_age)
    balance_at_end = future_value(
        current_balance, monthly_contribution, annual_return, contribution_years
    )

    # 2단계: 납입종료 후 수령시점까지 거치 운용
    deferral_years = max(0, payout_start_age - contribution_end_age)
    balance_at_payout = future_value(
        balance_at_end, 0, annual_return, deferral_years
    )

    return {
        'balance_at_contribution_end': round(balance_at_end),
        'balance_at_payout_start': round(balance_at_payout),
        'total_contributed': round(monthly_contribution * 12 * contribution_years),
        'investment_gain': round(balance_at_payout - current_balance -
                                  monthly_contribution * 12 * contribution_years),
    }


if __name__ == "__main__":
    # 테스트: 현재 50세, IRP 5천만원 적립, 월 50만원 납입,
    # 60세까지 납입, 65세부터 20년 수령
    result = project_pension_at_retirement(
        current_balance=50_000_000,
        monthly_contribution=500_000,
        current_age=50,
        contribution_end_age=60,
        payout_start_age=65,
        annual_return=0.04,
    )
    print("=== IRP 적립 시뮬레이션 ===")
    for k, v in result.items():
        print(f"  {k}: {v:,}원" if isinstance(v, (int, float)) else f"  {k}: {v}")

    payout = calculate_pension_payout(
        total_amount=result['balance_at_payout_start'],
        start_age=65,
        payout_years=20,
    )
    print("\n=== 65세부터 20년 수령 ===")
    for k, v in payout.items():
        print(f"  {k}: {v:,}원" if isinstance(v, (int, float)) else f"  {k}: {v}")

    tax = calculate_pension_tax(payout['annual_payout'], age=65)
    print("\n=== 세금 계산 ===")
    for k, v in tax.items():
        print(f"  {k}: {v}")
