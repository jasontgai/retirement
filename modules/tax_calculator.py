"""
세금/건보료 통합 계산
- 종합소득세 (누진세율)
- 연금소득공제
- 건강보험료 (직장/지역)
- 금융소득종합과세
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.tax_config import (
    INCOME_TAX_BRACKETS,
    LOCAL_TAX_RATE,
    PENSION_INCOME_DEDUCTION,
    PENSION_INCOME_DEDUCTION_MAX,
    FINANCIAL_INCOME_SEPARATE_LIMIT,
    FINANCIAL_INCOME_TAX_RATE,
    HEALTH_INSURANCE_RATE_EMPLOYEE,
    LONG_TERM_CARE_RATE,
    DEPENDENT_INCOME_LIMIT,
    DEPENDENT_PROPERTY_LIMIT,
    DEPENDENT_PROPERTY_INCOME_LIMIT,
)


def calculate_income_tax(taxable_income: float) -> dict:
    """
    종합소득세 계산 (누진세율)
    과세표준 기준 (각종 공제 후 금액)
    """
    if taxable_income <= 0:
        return {'tax': 0, 'local_tax': 0, 'total': 0, 'effective_rate': 0}

    tax = 0
    for limit, rate, deduction in INCOME_TAX_BRACKETS:
        if taxable_income <= limit:
            tax = taxable_income * rate - deduction
            break

    tax = max(0, tax)
    local_tax = tax * LOCAL_TAX_RATE  # 지방소득세
    total = tax + local_tax

    return {
        'tax': round(tax),
        'local_tax': round(local_tax),
        'total': round(total),
        'effective_rate': round(total / taxable_income * 100, 2),
    }


def calculate_pension_income_deduction(annual_pension: float) -> float:
    """
    연금소득공제 계산
    국민연금 + 사적연금(종합과세분) 합산 기준
    """
    if annual_pension <= 0:
        return 0

    deduction = 0
    for limit, rate, base in PENSION_INCOME_DEDUCTION:
        if annual_pension <= limit:
            # 누진공제 방식
            if base == 0:
                deduction = annual_pension * rate
            else:
                # 단계별 공제: base = 이전 단계까지 공제액
                prev_limit = 0
                for plimit, prate, pbase in PENSION_INCOME_DEDUCTION:
                    if plimit < limit:
                        prev_limit = plimit
                    else:
                        break
                deduction = base + (annual_pension - prev_limit) * rate
            break

    return min(deduction, PENSION_INCOME_DEDUCTION_MAX)


def calculate_financial_income_tax(financial_income: float,
                                    other_income: float = 0) -> dict:
    """
    금융소득 (이자/배당) 세금 계산
    - 2천만원 이하: 15.4% 분리과세 (원천징수)
    - 2천만원 초과: 종합과세 (다른 소득과 합산)
    """
    if financial_income <= FINANCIAL_INCOME_SEPARATE_LIMIT:
        tax = financial_income * FINANCIAL_INCOME_TAX_RATE
        return {
            'method': '분리과세',
            'tax': round(tax),
            'after_tax': round(financial_income - tax),
            'note': '15.4% 원천징수로 종결',
        }
    else:
        # 2천만원까지는 분리과세, 초과분은 종합과세
        separate_part = FINANCIAL_INCOME_SEPARATE_LIMIT
        synthetic_part = financial_income - separate_part

        separate_tax = separate_part * FINANCIAL_INCOME_TAX_RATE

        # 종합과세: 다른 소득과 합산
        total_taxable = other_income + synthetic_part
        synthetic_tax_result = calculate_income_tax(total_taxable)
        other_tax_only = calculate_income_tax(other_income)
        synthetic_tax = synthetic_tax_result['total'] - other_tax_only['total']

        total_tax = separate_tax + synthetic_tax

        return {
            'method': '종합과세',
            'separate_tax': round(separate_tax),
            'synthetic_tax': round(synthetic_tax),
            'total_tax': round(total_tax),
            'after_tax': round(financial_income - total_tax),
            'note': f'2천만원 초과분 {synthetic_part:,.0f}원 종합과세',
        }


def calculate_health_insurance_employee(annual_salary: float) -> dict:
    """직장가입자 건강보험료 (본인부담분)"""
    monthly_salary = annual_salary / 12
    health_insurance = monthly_salary * HEALTH_INSURANCE_RATE_EMPLOYEE / 2
    long_term_care = health_insurance * LONG_TERM_CARE_RATE
    total_monthly = health_insurance + long_term_care

    return {
        'type': '직장가입자',
        'monthly_health': round(health_insurance),
        'monthly_long_term_care': round(long_term_care),
        'monthly_total': round(total_monthly),
        'annual_total': round(total_monthly * 12),
    }


def calculate_health_insurance_local(
    annual_pension_income: float = 0,
    annual_financial_income: float = 0,
    annual_other_income: float = 0,
    property_value: float = 0,  # 재산세 과표 (공시가격의 60% 등)
) -> dict:
    """
    지역가입자 건강보험료 (간이 추정)
    ※ 실제는 점수표 방식이며, 매우 복잡함
       공식: 소득점수 + 재산점수 = 부과점수
       부과점수 × 점당금액(208.4원, 2024) = 월 보험료

    ※ 2022.9월 개편: 공적연금/금융소득 등 모든 소득 합산
       단, 공적연금소득은 50%만 반영 (2024년 기준)
    """
    # 소득 합산 (공적연금은 50%만 반영)
    income_for_health = (
        annual_pension_income * 0.5 +
        annual_financial_income +
        annual_other_income
    )

    # 매우 단순화된 모델 (실제와 차이 있음 - 참고용)
    # 일반적으로 지역가입자는 월소득의 약 8% 정도를 보험료로 부담
    income_premium_monthly = (income_for_health / 12) * 0.08

    # 재산보험료 (단순 추정 - 실제는 구간별 점수)
    # 5억 초과분에 대해 0.1% 정도 부담 (대략)
    property_premium_monthly = max(0, (property_value - 500_000_000)) * 0.001 / 12

    health_monthly = income_premium_monthly + property_premium_monthly
    long_term_care_monthly = health_monthly * LONG_TERM_CARE_RATE
    total_monthly = health_monthly + long_term_care_monthly

    return {
        'type': '지역가입자',
        'income_for_calc': round(income_for_health),
        'monthly_income_premium': round(income_premium_monthly),
        'monthly_property_premium': round(property_premium_monthly),
        'monthly_health': round(health_monthly),
        'monthly_long_term_care': round(long_term_care_monthly),
        'monthly_total': round(total_monthly),
        'annual_total': round(total_monthly * 12),
        'note': '간이 추정치. 정확한 금액은 건강보험공단 모의계산 필요',
    }


def check_dependent_eligibility(
    annual_income: float,
    property_value: float,
    has_business_income: bool = False
) -> dict:
    """
    피부양자 자격 확인
    - 2022.9월 개편: 소득기준 강화 (3,400만→2,000만원)
    """
    reasons_disqualified = []

    if annual_income > DEPENDENT_INCOME_LIMIT:
        reasons_disqualified.append(
            f"연소득 {annual_income:,.0f}원 (2천만원 초과)"
        )

    if property_value > DEPENDENT_PROPERTY_LIMIT:
        reasons_disqualified.append(
            f"재산 {property_value:,.0f}원 (5.4억 초과)"
        )
    elif property_value > DEPENDENT_PROPERTY_INCOME_LIMIT and annual_income > 10_000_000:
        reasons_disqualified.append(
            f"재산 3.6억 초과 + 소득 1천만원 초과"
        )

    if has_business_income:
        reasons_disqualified.append("사업소득 발생")

    return {
        'eligible': len(reasons_disqualified) == 0,
        'reasons_disqualified': reasons_disqualified,
        'note': '배우자 직장가입자가 있을 때 피부양자 등재 가능 시 건보료 0원',
    }


if __name__ == "__main__":
    print("=== 종합소득세 계산 (과세표준 5천만원) ===")
    tax = calculate_income_tax(50_000_000)
    for k, v in tax.items():
        print(f"  {k}: {v}")

    print("\n=== 연금소득공제 (연 2천만원 수령) ===")
    deduction = calculate_pension_income_deduction(20_000_000)
    print(f"  공제액: {deduction:,.0f}원")

    print("\n=== 금융소득 3천만원 (다른 소득 5천만원) ===")
    fi_tax = calculate_financial_income_tax(30_000_000, 50_000_000)
    for k, v in fi_tax.items():
        print(f"  {k}: {v}")

    print("\n=== 지역가입자 건보료 (연금 2400만, 금융 500만, 재산 8억) ===")
    health = calculate_health_insurance_local(
        annual_pension_income=24_000_000,
        annual_financial_income=5_000_000,
        property_value=800_000_000,
    )
    for k, v in health.items():
        print(f"  {k}: {v}")

    print("\n=== 피부양자 자격 확인 (소득 1500만, 재산 4억) ===")
    dep = check_dependent_eligibility(15_000_000, 400_000_000)
    for k, v in dep.items():
        print(f"  {k}: {v}")
