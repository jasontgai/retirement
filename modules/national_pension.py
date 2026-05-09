"""
국민연금 (노령연금) 계산
- 수급개시 연령 결정
- 조기/연기 수령에 따른 가감액
- 예상 수령액 추정
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.tax_config import (
    NPS_PENSION_START_AGE,
    EARLY_PENSION_DISCOUNT_PER_YEAR,
    DEFERRED_PENSION_BONUS_PER_YEAR,
)


def get_pension_start_age(birth_year: int) -> int:
    """출생연도별 노령연금 정상 수급개시 연령"""
    for (start, end), age in NPS_PENSION_START_AGE.items():
        if start <= birth_year <= end:
            return age
    return 65  # 기본값


def adjust_pension_amount(base_monthly: float, normal_age: int,
                           actual_start_age: int) -> float:
    """
    조기/연기 수령에 따른 연금액 조정
    - 조기수령(최대 5년): 연 6% 감액
    - 연기수령(최대 5년): 연 7.2% 가산
    """
    diff = actual_start_age - normal_age

    if diff < -5:
        diff = -5  # 최대 5년 조기
    elif diff > 5:
        diff = 5   # 최대 5년 연기

    if diff < 0:
        # 조기수령: 매월 0.5% 감액 (연 6%)
        adjustment = 1 + (diff * EARLY_PENSION_DISCOUNT_PER_YEAR)
    elif diff > 0:
        # 연기수령: 매월 0.6% 가산 (연 7.2%)
        adjustment = 1 + (diff * DEFERRED_PENSION_BONUS_PER_YEAR)
    else:
        adjustment = 1.0

    return base_monthly * adjustment


def estimate_pension_from_contribution(
    monthly_avg_income: float,
    contribution_years: float,
    A_value: float = 3_089_062  # 2024년 기준 A값 (전체 가입자 평균소득월액의 평균액)
) -> float:
    """
    납입정보 기반 노령연금 예상 월 수령액 (간이 추정)

    노령연금 = 1.2 × (A + B) × (1 + 0.05n) × P/12  (단순화)
    - A: 전체가입자 평균소득월액 평균
    - B: 본인 가입기간 평균소득월액
    - n: 20년 초과 가입년수
    - P: 가입월수/480 (40년 만기)

    ※ 정확한 계산은 국민연금공단 모의계산기 사용 권장
    """
    if contribution_years < 10:
        return 0  # 10년 미만은 노령연금 수급권 없음 (반환일시금)

    B = monthly_avg_income
    months = contribution_years * 12
    excess_years = max(0, contribution_years - 20)

    # 단순화된 산식
    base = 1.2 * (A_value + B) * (1 + 0.05 * excess_years)
    pension_annual = base * (months / 480)

    return pension_annual / 12  # 월 수령액


def calculate_total_npa_payout(
    monthly_amount: float,
    start_age: int,
    end_age: int = 90,
    inflation_rate: float = 0.02
) -> dict:
    """
    노령연금 총 수령액 추정 (인플레이션 반영)
    국민연금은 매년 전년도 물가상승률 반영
    """
    total = 0
    yearly_breakdown = []
    current = monthly_amount * 12

    for age in range(start_age, end_age + 1):
        total += current
        yearly_breakdown.append({
            'age': age,
            'annual_amount': round(current),
            'monthly_amount': round(current / 12),
        })
        current *= (1 + inflation_rate)

    return {
        'total_payout': round(total),
        'years_received': end_age - start_age + 1,
        'yearly_breakdown': yearly_breakdown,
    }


def compare_start_age_scenarios(
    base_monthly: float,
    normal_age: int,
    end_age: int = 90
) -> list:
    """수급 개시 연령별 시나리오 비교"""
    scenarios = []
    for start_age in range(max(60, normal_age - 5), min(70, normal_age + 5) + 1):
        adjusted = adjust_pension_amount(base_monthly, normal_age, start_age)
        result = calculate_total_npa_payout(adjusted, start_age, end_age)
        scenarios.append({
            'start_age': start_age,
            'monthly_amount': round(adjusted),
            'total_payout': result['total_payout'],
            'diff_from_normal': start_age - normal_age,
        })
    return scenarios


if __name__ == "__main__":
    # 테스트: 1970년생, 정상 수급 65세, 월 150만원 예상
    birth_year = 1970
    normal_age = get_pension_start_age(birth_year)
    print(f"{birth_year}년생 정상 수급개시 연령: {normal_age}세")

    # 시나리오 비교
    scenarios = compare_start_age_scenarios(1_500_000, normal_age, 90)
    print("\n수급개시 연령별 시나리오 (월 150만원 기준, 90세까지):")
    for s in scenarios:
        marker = "★" if s['diff_from_normal'] == 0 else ""
        print(f"  {s['start_age']}세 개시: 월 {s['monthly_amount']:>10,}원, "
              f"총 {s['total_payout']:>15,}원 {marker}")
