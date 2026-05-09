"""
주택연금 (역모기지) 계산
- 한국주택금융공사(HF) 주택연금 기준
- 비과세 (세금 없음)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.tax_config import (
    HOUSE_PENSION_MIN_AGE,
    HOUSE_PENSION_MAX_HOUSE_VALUE,
    HOUSE_PENSION_RATIO,
)


def is_eligible_for_house_pension(age: int, house_value: float,
                                    is_owner: bool = True) -> dict:
    """주택연금 가입자격 확인"""
    reasons = []

    if age < HOUSE_PENSION_MIN_AGE:
        reasons.append(f"가입연령 미달 (만 {HOUSE_PENSION_MIN_AGE}세 이상 필요)")
    if not is_owner:
        reasons.append("주택소유자 본인 또는 배우자만 가입 가능")
    if house_value > HOUSE_PENSION_MAX_HOUSE_VALUE:
        reasons.append(f"공시가격 {HOUSE_PENSION_MAX_HOUSE_VALUE/100_000_000:.0f}억원 초과")

    return {
        'eligible': len(reasons) == 0,
        'reasons': reasons,
    }


def interpolate_ratio(age: int) -> float:
    """연령별 주택연금 지급비율 보간"""
    ages = sorted(HOUSE_PENSION_RATIO.keys())

    if age <= ages[0]:
        return HOUSE_PENSION_RATIO[ages[0]]
    if age >= ages[-1]:
        return HOUSE_PENSION_RATIO[ages[-1]]

    # 선형 보간
    for i in range(len(ages) - 1):
        if ages[i] <= age <= ages[i+1]:
            x1, x2 = ages[i], ages[i+1]
            y1, y2 = HOUSE_PENSION_RATIO[x1], HOUSE_PENSION_RATIO[x2]
            return y1 + (y2 - y1) * (age - x1) / (x2 - x1)

    return HOUSE_PENSION_RATIO[ages[-1]]


def estimate_house_pension(
    house_value: float,
    age: int,
    payout_type: str = "lifetime_fixed"  # 종신정액형
) -> dict:
    """
    주택연금 예상 수령액 추정 (간이 계산)

    ※ 정확한 금액은 한국주택금융공사 사이트에서 모의계산 필요
       https://www.hf.go.kr
    """
    eligibility = is_eligible_for_house_pension(age, house_value)
    if not eligibility['eligible']:
        return {
            'eligible': False,
            'reasons': eligibility['reasons'],
        }

    # 지급한도: 공시가격 12억 초과시 12억으로 제한
    base_value = min(house_value, HOUSE_PENSION_MAX_HOUSE_VALUE)
    annual_ratio = interpolate_ratio(age)
    monthly_payout = base_value * annual_ratio / 12

    return {
        'eligible': True,
        'house_value_used': round(base_value),
        'age_at_start': age,
        'monthly_payout': round(monthly_payout),
        'annual_payout': round(monthly_payout * 12),
        'tax': 0,  # 주택연금은 비과세
        'after_tax_monthly': round(monthly_payout),
        'note': "주택연금은 비과세이며, 종신지급형 가정. 실제 금액은 HF 모의계산 필요.",
    }


def compare_house_pension_start_ages(
    house_value: float,
    current_age: int,
    end_age: int = 90
) -> list:
    """주택연금 가입 시점별 비교"""
    scenarios = []
    for start_age in range(max(current_age, 55), 81, 5):
        result = estimate_house_pension(house_value, start_age)
        if result.get('eligible'):
            years = end_age - start_age
            total = result['monthly_payout'] * 12 * years
            scenarios.append({
                'start_age': start_age,
                'monthly_payout': result['monthly_payout'],
                'years_received': years,
                'total_payout': total,
            })
    return scenarios


def compare_sell_vs_pension(
    house_value: float,
    age: int,
    rental_income: float = 0,
    end_age: int = 90,
    investment_return: float = 0.03
) -> dict:
    """
    주택연금 vs 매각 후 운용 비교
    """
    # 옵션 1: 주택연금
    hp = estimate_house_pension(house_value, age)
    if not hp.get('eligible'):
        return {'error': '주택연금 가입불가'}

    years = end_age - age
    hp_total = hp['monthly_payout'] * 12 * years

    # 옵션 2: 매각 후 예금/투자
    # 단순화: 매각대금을 투자수익률로 운용하면서 매월 동일 금액 인출
    # 1세대 1주택은 양도세 비과세 가정 (12억 이하)
    sale_proceeds = house_value
    if house_value > 1_200_000_000:
        # 12억 초과분에 대한 양도세 단순 추정 (15% 가정)
        sale_proceeds -= (house_value - 1_200_000_000) * 0.15

    monthly_rate = investment_return / 12
    months = years * 12
    if monthly_rate > 0:
        annuity_factor = (1 - (1 + monthly_rate) ** -months) / monthly_rate
        sale_monthly = sale_proceeds / annuity_factor
    else:
        sale_monthly = sale_proceeds / months

    return {
        '주택연금': {
            '월수령액': hp['monthly_payout'],
            '총수령액': hp_total,
            '주택소유권': "본인 (사망시 정산)",
            '세금': "비과세",
        },
        '매각_후_운용': {
            '매각대금': round(sale_proceeds),
            '월수령액': round(sale_monthly),
            '총수령액': round(sale_monthly * months),
            '주택소유권': "없음",
            '세금': "양도세(12억초과분), 운용수익 과세",
        },
        '추가_고려사항': [
            "주택연금은 거주권 보장",
            "주택가격 상승시 주택연금이 불리할 수 있음",
            "매각시 거주지 별도 마련 필요 (월세/전세)",
            "상속 의향에 따라 선택 달라짐",
        ],
    }


if __name__ == "__main__":
    # 테스트: 65세, 8억 주택
    result = estimate_house_pension(800_000_000, 65)
    print("=== 65세, 8억 주택, 주택연금 ===")
    for k, v in result.items():
        if isinstance(v, (int, float)):
            print(f"  {k}: {v:,}")
        else:
            print(f"  {k}: {v}")

    print("\n=== 가입 시점별 비교 ===")
    scenarios = compare_house_pension_start_ages(800_000_000, 60, 90)
    for s in scenarios:
        print(f"  {s['start_age']}세 시작: 월 {s['monthly_payout']:,}원, "
              f"{s['years_received']}년간 총 {s['total_payout']:,}원")

    print("\n=== 주택연금 vs 매각 비교 ===")
    comp = compare_sell_vs_pension(800_000_000, 65)
    for k, v in comp.items():
        print(f"\n{k}:")
        if isinstance(v, dict):
            for k2, v2 in v.items():
                print(f"  {k2}: {v2}")
        elif isinstance(v, list):
            for item in v:
                print(f"  - {item}")
        else:
            print(f"  {v}")
