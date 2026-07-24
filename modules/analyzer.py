"""
은퇴설계 통합 분석 엔진
- 사용자 프로필을 받아 모든 모듈을 호출하여 종합 분석
- 시나리오 비교 및 리스크 평가
"""
import sys
import os
import math
from datetime import date as _today_date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import UserProfile, PensionType
from national_pension import (
    get_pension_start_age, adjust_pension_amount,
    calculate_total_npa_payout, compare_start_age_scenarios
)
from private_pension import (
    project_pension_at_retirement, calculate_pension_payout,
    calculate_pension_tax,
)
from house_pension import estimate_house_pension
from tax_calculator import (
    calculate_income_tax, calculate_pension_income_deduction,
    calculate_financial_income_tax, calculate_health_insurance_local,
    calculate_health_insurance_employee, check_dependent_eligibility,
)


class RetirementAnalyzer:
    """은퇴설계 분석기"""

    def __init__(self, profile: UserProfile):
        self.profile = profile
        self.results = {}
        self.inflation_rate = getattr(profile, 'inflation_rate', 0.025)

    def analyze(self) -> dict:
        """전체 분석 실행"""
        self.results = {
            '사용자정보': self._summarize_user(),
            '자산현황': self._analyze_assets(),
            '연금분석': self._analyze_pensions(),
            '주택연금': self._analyze_house_pension(),
            '기초연금': self._analyze_basic_pension(),
            '예상수입': self._project_retirement_income(),
            '나이별수입': self._project_income_by_age(),
            '재투자시뮬레이션': self._project_reinvestment(),
            '세금건보료': self._analyze_tax_and_insurance(),
            '현금흐름': self._project_cash_flow(),
            '현금흐름_보완': self._check_shortfall_remedies(),
            '시나리오비교': self._compare_scenarios(),
            '제언': self._generate_recommendations(),
            '세액공제최적화': self._analyze_tax_optimization(),
        }
        return self.results

    def _summarize_user(self) -> dict:
        p = self.profile.personal
        return {
            '이름': p.name,
            '현재연령': p.current_age,
            '희망은퇴연령': p.retirement_age,
            '기대수명': p.expected_lifespan,
            '은퇴후_여생': p.expected_lifespan - p.retirement_age,
            '국민연금_정상수급연령': get_pension_start_age(p.birth_year),
        }

    def _analyze_assets(self) -> dict:
        p = self.profile
        return {
            '부동산': {
                '항목수': len(p.real_estates),
                '시세_합계': p.total_real_estate_value,
                '상세': [{'이름': re.name, '시세': re.market_value,
                         '대출': re.debt} for re in p.real_estates],
            },
            '금융자산': {
                '항목수': len(p.financial_assets),
                '합계': p.total_financial_assets,
                '상세': [{'이름': fa.name, '종류': fa.asset_type,
                         '금액': fa.amount} for fa in p.financial_assets],
            },
            '회원권': [{'이름': m.name, '종류': m.membership_type,
                       '시세': m.market_value, '연회비': m.annual_dues}
                      for m in p.memberships],
            '차량': [{'이름': v.name, '시세': v.market_value,
                     '연유지비': v.annual_cost} for v in p.vehicles],
            '보험': {
                '항목수': len(p.insurances),
                '해약환급금_합계': p.total_insurance_surrender_value,
                '상세': [{'이름': i.name, '종류': i.insurance_type,
                          '해약환급금': i.surrender_value, '월납입': i.monthly_premium}
                         for i in p.insurances],
            },
            '부채총액': p.total_debt,
            '순자산': p.net_worth,
        }

    def _analyze_pensions(self) -> dict:
        results = {}
        retirement_age = self.profile.personal.retirement_age
        current_age = self.profile.personal.current_age
        birth_year = self.profile.personal.birth_date.year
        current_year = _today_date.today().year

        for pension in self.profile.pensions:
            if pension.pension_type.value == "국민연금":
                normal_age = get_pension_start_age(birth_year)
                actual_start = max(pension.expected_start_age, normal_age - 5)
                original_monthly = round(pension.expected_monthly_payout)
                adjusted_monthly = adjust_pension_amount(
                    pension.expected_monthly_payout, normal_age, actual_start
                )
                diff_years = actual_start - normal_age
                if diff_years < 0:
                    timing_reason = f"조기수령 {abs(diff_years)}년 (연 6% 감액, {diff_years * 6:+.0f}%)"
                elif diff_years > 0:
                    timing_reason = f"연기수령 {diff_years}년 (연 7.2% 가산, +{diff_years * 7.2:.1f}%)"
                else:
                    timing_reason = "정상수령 (조정 없음)"

                # 재직자 노령연금 감액 (2025년 A값 기준, 최대 5년 적용)
                _NPS_A_VALUE = 2_989_237
                _inc = self.profile.current_income
                if actual_start < retirement_age:
                    _income_at_start = (_inc.annual_salary + _inc.annual_bonus) // 12
                elif _inc.parttime_monthly > 0 and actual_start <= _inc.parttime_until_age:
                    _income_at_start = _inc.parttime_monthly
                else:
                    _income_at_start = 0

                income_deduction = 0
                income_deduction_reason = ''
                if _income_at_start > _NPS_A_VALUE:
                    _excess = _income_at_start - _NPS_A_VALUE
                    _reduction = 0
                    for _cap, _rate in [(1_000_000, 0.05), (1_000_000, 0.10),
                                        (1_000_000, 0.15), (1_000_000, 0.20), (float('inf'), 0.25)]:
                        _chunk = min(_excess, _cap)
                        _reduction += _chunk * _rate
                        _excess -= _chunk
                        if _excess <= 0:
                            break
                    income_deduction = round(min(_reduction, adjusted_monthly * 0.5))
                    income_deduction_reason = (
                        f"재직자 노령연금 감액 — 소득 {_income_at_start:,}원/월이 "
                        f"A값({_NPS_A_VALUE:,}원) 초과, 최대 5년간 적용"
                    )

                results[pension.name] = {
                    '종류': pension.pension_type.value,
                    '정상수급연령': normal_age,
                    '실제수급연령': actual_start,
                    '수령시작_연령': actual_start,
                    '개시년도': current_year + max(0, actual_start - current_age),
                    '월수령액_원래': original_monthly,
                    '조정_차이': round(adjusted_monthly) - original_monthly,
                    '조정_사유': timing_reason,
                    '재직자_감액': income_deduction,
                    '재직자_감액_사유': income_deduction_reason,
                    '월수령액_조정': round(adjusted_monthly),
                    '연수령액': round(adjusted_monthly * 12),
                    '과세방식': '연금소득세 (종합소득 합산)',
                }
            else:
                # 사적연금: 적립금 추정 + 분할수령
                projection = project_pension_at_retirement(
                    current_balance=pension.current_balance,
                    monthly_contribution=pension.monthly_contribution,
                    current_age=current_age,
                    contribution_end_age=pension.contribution_end_age,
                    payout_start_age=pension.expected_start_age,
                    annual_return=pension.annual_return_rate,
                )

                _is_lifetime = pension.payout_period_years == 0
                _lifespan = self.profile.personal.expected_lifespan
                # 종신(0)이면 기대수명까지의 기간으로 계산, 저장은 0 유지
                payout_years = (_lifespan - pension.expected_start_age) if _is_lifetime else (pension.payout_period_years or 20)
                payout = calculate_pension_payout(
                    total_amount=projection['balance_at_payout_start'],
                    start_age=pension.expected_start_age,
                    payout_years=payout_years,
                    annual_return=pension.annual_return_rate,
                )

                tax_info = calculate_pension_tax(
                    payout['annual_payout'],
                    age=pension.expected_start_age,
                )

                results[pension.name] = {
                    '종류': pension.pension_type.value,
                    '수령시작_연령': pension.expected_start_age,
                    '개시년도': current_year + max(0, pension.expected_start_age - current_age),
                    '납입완료시_예상금액': projection['balance_at_contribution_end'],
                    '수령시점_적립금': projection['balance_at_payout_start'],
                    '월수령액': payout['monthly_payout'],
                    '연수령액': payout['annual_payout'],
                    '수령기간': 0 if _is_lifetime else payout['payout_years'],
                    '예상세금': tax_info['tax'],
                    '세후월수령액': round((payout['annual_payout'] -
                                          tax_info['tax']) / 12),
                    '과세방식': tax_info['method'],
                }

        return results

    def _analyze_house_pension(self) -> dict:
        """주택연금 가능성 분석 (자가 보유시)"""
        primary = next((re for re in self.profile.real_estates
                       if re.is_primary_residence and re.house_type.value == "자가"),
                      None)
        if not primary:
            return {'가능여부': False, '사유': '자가 보유 부동산 없음'}

        retirement_age = self.profile.personal.retirement_age
        # 공시가격 기준 (없으면 시세의 70% 추정)
        official = primary.official_price or primary.market_value * 0.7

        result = estimate_house_pension(official, retirement_age)
        result['주택명'] = primary.name
        result['시세'] = primary.market_value
        result['공시가격'] = official
        return result

    def _project_retirement_income(self) -> dict:
        """은퇴 후 월/연 예상 수입 (모든 연금 합산)"""
        retirement_age = self.profile.personal.retirement_age

        monthly_sources = {}
        annual_total = 0

        # 각 연금별 수령액
        for pension in self.profile.pensions:
            if pension.expected_start_age <= retirement_age + 30:  # 향후 수령 예정
                if pension.pension_type.value == "국민연금":
                    monthly = pension.expected_monthly_payout
                else:
                    # 사적연금은 _analyze_pensions의 결과 활용
                    pass

        # 부동산 임대수입
        rental_income = sum(re.monthly_rent_income for re in self.profile.real_estates)
        if rental_income > 0:
            monthly_sources['임대수입'] = rental_income
            annual_total += rental_income * 12

        # 금융자산 운용수익 (연 수익률 기반 인출 가정)
        fi_income = 0
        for fa in self.profile.financial_assets:
            fi_income += fa.amount * fa.annual_return_rate
        if fi_income > 0:
            monthly_sources['금융자산수익'] = round(fi_income / 12)
            annual_total += fi_income

        # 연금 합산
        for name, info in self._analyze_pensions().items():
            month_amt = info.get('월수령액_조정') or info.get('월수령액', 0)
            monthly_sources[name] = month_amt
            annual_total += month_amt * 12

        # 연금형 보험 수령액
        for ins in self.profile.insurances:
            if ins.insurance_type == "연금보험" and ins.monthly_payout > 0:
                monthly_sources[ins.name] = ins.monthly_payout
                annual_total += ins.monthly_payout * 12

        # 은퇴 후 근로소득
        inc = self.profile.current_income
        if inc.parttime_monthly > 0:
            monthly_sources['근로소득'] = int(inc.parttime_monthly)
            annual_total += inc.parttime_monthly * 12

        # 배우자 연금
        p_info = self.profile.personal
        if p_info.spouse_nps_monthly > 0:
            monthly_sources['배우자 국민연금'] = int(p_info.spouse_nps_monthly)
            annual_total += p_info.spouse_nps_monthly * 12
        if p_info.spouse_other_monthly > 0:
            monthly_sources['배우자 기타연금'] = int(p_info.spouse_other_monthly)
            annual_total += p_info.spouse_other_monthly * 12

        # 기초연금 (만 65세 이후, 소득인정액 기준 수급 여부 판단)
        if self.profile.personal.retirement_age >= 65:
            nps_monthly = next(
                (int(info.get('월수령액_조정') or info.get('월수령액', 0))
                 for name, info in self._analyze_pensions().items()
                 if '국민연금' in name),
                0,
            )
            has_spouse = p_info.spouse_nps_monthly > 0 or p_info.spouse_other_monthly > 0
            bp = self._calc_basic_pension(sum(monthly_sources.values()), nps_monthly, has_spouse)
            if bp > 0:
                monthly_sources['기초연금'] = bp
                annual_total += bp * 12

        return {
            '월수입_합계': sum(monthly_sources.values()),
            '연수입_합계': annual_total,
            '항목별': monthly_sources,
        }

    def _calc_basic_pension(self, monthly_total: int, nps_monthly: int, has_spouse: bool) -> int:
        """
        기초연금 수급액 계산 (2025년 기준)
        - 선정기준: 소득인정액 ≤ 213만원(단독) / 340.8만원(부부)
        - 기준연금액: 334,810원
        - NPS 연계감액: NPS > 기준×1.5 시 초과분의 50% 감액
        - 부부 수령 시 각각 20% 추가 감액
        """
        BASE = 334_810
        THRESHOLD_SOLO   = 2_130_000
        THRESHOLD_COUPLE = 3_408_000

        threshold = THRESHOLD_COUPLE if has_spouse else THRESHOLD_SOLO
        if monthly_total > threshold:
            return 0

        nps_limit = round(BASE * 1.5)  # 502,215원
        if nps_monthly > nps_limit:
            benefit = BASE - round((nps_monthly - nps_limit) * 0.5)
            benefit = max(benefit, round(BASE * 0.5))  # 최저 167,405원
        else:
            benefit = BASE

        if has_spouse:
            benefit = round(benefit * 0.8)

        return benefit

    def _analyze_basic_pension(self) -> dict:
        """기초연금 수급 가능성 요약 분석"""
        p_info = self.profile.personal
        BASE = 334_810
        THRESHOLD_SOLO   = 2_130_000
        THRESHOLD_COUPLE = 3_408_000

        retirement_income = self._project_retirement_income()
        monthly_total = retirement_income['월수입_합계']

        nps_monthly = next(
            (int(info.get('월수령액_조정') or info.get('월수령액', 0))
             for name, info in self._analyze_pensions().items()
             if '국민연금' in name),
            0,
        )
        has_spouse = p_info.spouse_nps_monthly > 0 or p_info.spouse_other_monthly > 0
        threshold = THRESHOLD_COUPLE if has_spouse else THRESHOLD_SOLO

        eligible_at_65 = p_info.retirement_age >= 65
        income_eligible = monthly_total <= threshold

        benefit = self._calc_basic_pension(monthly_total, nps_monthly, has_spouse) if eligible_at_65 else 0

        nps_deducted = nps_monthly > round(BASE * 1.5) and eligible_at_65 and income_eligible

        return {
            '수급가능': eligible_at_65 and income_eligible,
            '월수급액': benefit,
            '소득인정액': monthly_total,
            '선정기준액': threshold,
            'NPS감액여부': nps_deducted,
            '기준연금액': BASE,
            '비고': (
                '만 65세 미만으로 수급 불가' if not eligible_at_65
                else '소득인정액 초과로 수급 불가' if not income_eligible
                else 'NPS 연계 감액 적용' if nps_deducted
                else '전액 수급 가능'
            ),
        }

    def _project_income_by_age(self) -> list:
        """나이별 예상 월수입 (은퇴~기대수명, 매 연령)"""
        personal = self.profile.personal
        lifespan = personal.expected_lifespan
        retirement_age = personal.retirement_age
        pension_analysis = self._analyze_pensions()

        rental_monthly = sum(re.monthly_rent_income for re in self.profile.real_estates)
        fi_monthly = round(sum(
            fa.amount * fa.annual_return_rate for fa in self.profile.financial_assets
        ) / 12)

        _today = _today_date.today()
        _bd = personal.birth_date
        _current_age = _today.year - _bd.year - (
            1 if (_today.month, _today.day) < (_bd.month, _bd.day) else 0
        )
        _start_age = max(1, min(_current_age, retirement_age - 1))

        rows = []
        for age in range(_start_age, lifespan + 1):
            sources = {}
            if age >= retirement_age:
                if rental_monthly > 0:
                    sources['임대수입'] = rental_monthly
                if fi_monthly > 0:
                    sources['금융자산수익'] = fi_monthly

            for pension in self.profile.pensions:
                info = pension_analysis.get(pension.name, {})
                start = (info.get('수령시작_연령')
                         or info.get('실제수급연령')
                         or pension.expected_start_age)
                period = info.get('수령기간') or pension.payout_period_years or 0
                # 0=종신, 국민연금=종신
                is_lifetime = (period == 0 or pension.pension_type.value == '국민연금')
                end = start + period if not is_lifetime else lifespan + 1
                if start <= age < end:
                    amt = info.get('월수령액_조정') or info.get('월수령액', 0)
                    if amt > 0:
                        if pension.pension_type.value == '국민연금':
                            # 물가상승률 반영 (법정 CPI 연동)
                            amt = round(amt * (1 + self.inflation_rate) ** max(0, age - start))
                            # 재직자 노령연금 감액: 연금 수령 후 최대 5년간, 근로소득 > A값 시 적용
                            _years_since_start = age - start
                            if _years_since_start < 5:
                                _NPS_A = 2_989_237
                                _inc2 = self.profile.current_income
                                _earned = 0
                                if age < retirement_age:
                                    _earned = round((_inc2.annual_salary + _inc2.annual_bonus) / 12)
                                elif _inc2.parttime_monthly > 0 and age < _inc2.parttime_until_age:
                                    _earned = int(_inc2.parttime_monthly)
                                if _earned > _NPS_A:
                                    _excess = _earned - _NPS_A
                                    _red = 0
                                    for _cap, _rate in [
                                        (1_000_000, 0.05), (1_000_000, 0.10),
                                        (1_000_000, 0.15), (1_000_000, 0.20),
                                        (float('inf'), 0.25)
                                    ]:
                                        _chunk = min(_excess, _cap)
                                        _red += _chunk * _rate
                                        _excess -= _chunk
                                        if _excess <= 0:
                                            break
                                    amt = max(0, amt - round(min(_red, amt * 0.5)))
                        sources[pension.name] = amt

            for ins in self.profile.insurances:
                if ins.insurance_type != "연금보험" or ins.monthly_payout <= 0:
                    continue
                start = ins.payout_start_age
                period = ins.payout_period_years
                end = start + period if period > 0 else lifespan + 1
                if start <= age < end:
                    sources[ins.name] = ins.monthly_payout

            # 근로소득: 은퇴 전=급여, 은퇴 후=파트타임
            inc = self.profile.current_income
            if age < retirement_age:
                _sal = round((inc.annual_salary + inc.annual_bonus) / 12)
                if _sal > 0:
                    sources['근로소득'] = _sal
            elif inc.parttime_monthly > 0 and age < inc.parttime_until_age:
                sources['근로소득'] = int(inc.parttime_monthly)

            # 배우자 연금
            p_info = self.profile.personal
            if p_info.spouse_nps_monthly > 0 and age >= p_info.spouse_nps_start_age:
                _sp_nps_years = max(0, age - p_info.spouse_nps_start_age)
                sources['배우자 국민연금'] = round(
                    int(p_info.spouse_nps_monthly) * (1 + self.inflation_rate) ** _sp_nps_years
                )
            if p_info.spouse_other_monthly > 0 and age >= p_info.spouse_other_start_age:
                sources['배우자 기타연금'] = int(p_info.spouse_other_monthly)

            # 기초연금: 만 65세 이상, 소득인정액 기준 수급 가능 시 포함
            if age >= 65:
                _nps_m = sources.get('국민연금', 0)
                _has_sp = p_info.spouse_nps_monthly > 0 or p_info.spouse_other_monthly > 0
                _bp = self._calc_basic_pension(sum(sources.values()), _nps_m, _has_sp)
                if _bp > 0:
                    sources['기초연금'] = _bp

            # 월세금 계산 (소득세 + 건보료 월환산)
            _annual_income = sum(sources.values()) * 12
            _tax_detail: dict = {}

            # 사적연금 이름 → 타입 맵 (분리/종합과세 판정용)
            _private_types = {'퇴직연금DB', '퇴직연금DC', 'IRP', '연금저축'}
            _pension_name_type = {p.name: p.pension_type.value for p in self.profile.pensions}

            if age < retirement_age:
                # 근로소득공제
                _g = _annual_income
                if _g <= 5_000_000:
                    _labor_ded = _g * 0.70
                elif _g <= 15_000_000:
                    _labor_ded = 3_500_000 + (_g - 5_000_000) * 0.40
                elif _g <= 45_000_000:
                    _labor_ded = 7_500_000 + (_g - 15_000_000) * 0.15
                elif _g <= 100_000_000:
                    _labor_ded = 12_000_000 + (_g - 45_000_000) * 0.05
                else:
                    _labor_ded = 20_000_000
                _taxable = max(0, _g - _labor_ded - 1_500_000)
                _tax_result = calculate_income_tax(_taxable)
                _tax_m = round(_tax_result['total'] / 12)
                _hi_m = calculate_health_insurance_employee(_annual_income)['monthly_total']
                _tax_detail = {
                    '소득구분': '근로소득',
                    '연소득': round(_annual_income / 10000),
                    '근로소득공제': round(_labor_ded / 10000),
                    '기본공제': 150,
                    '과세표준': round(_taxable / 10000),
                    '연소득세': round(_tax_result['total'] / 10000),
                    '실효세율': _tax_result['effective_rate'],
                    '건보료구분': '직장가입자',
                    '건보료_월': round(_hi_m / 10000, 1),
                }
            else:
                # 은퇴 후: 연금소득 기준 (임대·금융·근로소득 제외)
                _pension_annual = sum(
                    v for k, v in sources.items()
                    if k not in ('임대수입', '금융자산수익', '근로소득')
                ) * 12
                _p_ded = calculate_pension_income_deduction(_pension_annual)
                _taxable = max(0, _pension_annual - _p_ded - 1_500_000)
                _tax_result = calculate_income_tax(_taxable)
                _tax_m = round(_tax_result['total'] / 12)
                _hi_result = calculate_health_insurance_local(
                    annual_pension_income=_pension_annual,
                    annual_financial_income=fi_monthly * 12,
                    annual_other_income=rental_monthly * 12,
                )
                _hi_m = _hi_result['monthly_total']

                # 사적연금(퇴직연금·IRP·연금저축) 연수령액 합계 → 분리/종합과세 판정
                _private_annual = sum(
                    v for k, v in sources.items()
                    if _pension_name_type.get(k) in _private_types
                ) * 12
                if _private_annual > 15_000_000:
                    _pvt_tax_method = f'종합과세 또는 16.5% 분리과세 선택 (연 {round(_private_annual/10000)}만원)'
                elif _private_annual > 0:
                    _pvt_rate = 5.5 if age < 70 else (4.4 if age < 80 else 3.3)
                    _pvt_tax_method = f'저율 분리과세 {_pvt_rate}% (연 {round(_private_annual/10000)}만원)'
                else:
                    _pvt_tax_method = None

                _tax_detail = {
                    '소득구분': '연금소득',
                    '연연금소득': round(_pension_annual / 10000),
                    '연금소득공제': round(_p_ded / 10000),
                    '기본공제': 150,
                    '과세표준': round(_taxable / 10000),
                    '연소득세': round(_tax_result['total'] / 10000),
                    '실효세율': _tax_result['effective_rate'],
                    '건보료구분': '지역가입자',
                    '건보료_월': round(_hi_m / 10000, 1),
                    '건보료_소득반영': round(_hi_result.get('income_for_calc', 0) / 10000),
                    '사적연금_과세': _pvt_tax_method,
                }

            # NaN/inf 방어: 비정상 값은 0으로 대체
            clean_sources = {
                k: v for k, v in sources.items()
                if isinstance(v, (int, float)) and math.isfinite(v)
            }
            rows.append({
                '나이': age,
                '월수입': sum(clean_sources.values()),
                '항목별': clean_sources,
                '월소득세': _tax_m,
                '월건보료': _hi_m,
                '월세금': _tax_m + _hi_m,
                '세금계산기준': _tax_detail,
            })

        return rows

    def _analyze_tax_and_insurance(self) -> dict:
        """은퇴 후 세금 및 건보료 분석"""
        # 은퇴 후 예상 소득 추정
        annual_pension = 0
        annual_financial = 0
        annual_rental = 0

        for pension in self.profile.pensions:
            if pension.pension_type.value == "국민연금":
                annual_pension += pension.expected_monthly_payout * 12

        for fa in self.profile.financial_assets:
            annual_financial += fa.amount * fa.annual_return_rate

        for re in self.profile.real_estates:
            annual_rental += re.monthly_rent_income * 12

        # ── 재산 산정 ────────────────────────────────────────────
        # 건보료 지역가입자 산정: 공시가격 기준
        re_property_list = []
        for re in self.profile.real_estates:
            official = re.official_price or round(re.market_value * 0.7)
            re_property_list.append({
                'name': re.name,
                'official_price': official,
                'tax_base': round(official * 0.6),   # 재산세 과표 = 공시가 × 60%
                'is_primary': re.is_primary_residence,
                'has_rental': re.monthly_rent_income > 0,
            })
        re_property_total      = sum(r['official_price'] for r in re_property_list)
        # 피부양자 기준 재산세 과표 합산 (주택 공시가 × 60% + 회원권 시가)
        dep_tax_base_total = sum(r['tax_base'] for r in re_property_list)
        membership_value   = sum(m.market_value for m in self.profile.memberships)
        dep_tax_base_total += membership_value
        # 건보료 지역가입자용 property_value (공시가 합산)
        total_property = re_property_total + membership_value

        # ── 소득세 ───────────────────────────────────────────────
        pension_deduction = calculate_pension_income_deduction(annual_pension)
        taxable_pension   = max(0, annual_pension - pension_deduction)
        taxable_income    = taxable_pension + annual_rental - 1_500_000
        income_tax        = calculate_income_tax(max(0, taxable_income))

        fi_tax = calculate_financial_income_tax(annual_financial, taxable_income)

        # ── 건강보험료 (지역가입자) ──────────────────────────────
        health = calculate_health_insurance_local(
            annual_pension_income=annual_pension,
            annual_financial_income=annual_financial,
            annual_other_income=annual_rental,
            property_value=total_property,
        )

        # ── 피부양자 자격 (2022.9 개편 기준) ────────────────────
        # 소득 기준: 공적연금 전액 + 금융소득(1천만 초과 시만 산입) + 임대소득
        FI_DEP_THRESHOLD = 10_000_000  # 금융소득 1천만 초과 시 전액 산입
        dep_fi_income = annual_financial if annual_financial > FI_DEP_THRESHOLD else 0
        dep_annual_income = annual_pension + dep_fi_income + annual_rental
        has_rental_income = annual_rental > 0

        dep_check = check_dependent_eligibility(
            dep_annual_income, dep_tax_base_total,
            has_business_income=has_rental_income,  # 임대소득 = 사업소득 간주
        )

        # 피부양자 등재 시 절감액
        dep_saving_annual = health['annual_total'] if dep_check['eligible'] else 0

        # 자녀 피부양자 가능 여부 안내 (자녀 수 > 0 이면 해당)
        has_dependents = self.profile.personal.dependents > 0

        # 재산 기준 상세
        dep_property_ok   = dep_tax_base_total <= 540_000_000
        dep_property_mid  = 360_000_000 < dep_tax_base_total <= 540_000_000
        dep_income_ok     = dep_annual_income <= 20_000_000
        dep_income_mid_ok = dep_annual_income <= 10_000_000  # 재산 3.6~5.4억 구간

        dep_detail = {
            '연간소득_피부양자기준': round(dep_annual_income),
            '재산세과표_합계': round(dep_tax_base_total),
            '소득기준_충족': dep_income_ok,
            '재산기준_충족': dep_property_ok,
            '임대소득_없음': not has_rental_income,
            '재산중간구간': dep_property_mid,
            '재산중간구간_소득기준_충족': dep_income_mid_ok if dep_property_mid else None,
            '자녀_있음': has_dependents,
            '절감_예상_연': round(dep_saving_annual),
            '재산_항목': re_property_list,
        }
        dep_check.update(dep_detail)

        # ── 직장 임의계속가입 계산 ───────────────────────────────
        # 퇴직 전 급여 기반으로 임의계속가입 보험료 산정
        # 임의계속가입: 사업주+본인 부담분 전액 본인 부담 = 직장 본인분 × 2
        annual_salary = self.profile.current_income.annual_salary
        monthly_salary = annual_salary / 12
        from config.tax_config import HEALTH_INSURANCE_RATE_EMPLOYEE, LONG_TERM_CARE_RATE
        # 전체 직장 보험료 (사업주+본인) = 월급 × 7.09% × (1+장기요양율)
        voluntary_health   = monthly_salary * HEALTH_INSURANCE_RATE_EMPLOYEE
        voluntary_ltc      = voluntary_health * LONG_TERM_CARE_RATE
        voluntary_monthly  = round(voluntary_health + voluntary_ltc)

        local_monthly = health['monthly_total']

        # 임의계속가입이 유리한지 여부
        voluntary_saves = local_monthly - voluntary_monthly  # 양수면 임의계속가입이 유리
        is_voluntary_better = voluntary_monthly < local_monthly

        voluntary_info = {
            '월_보험료': voluntary_monthly,
            '연_보험료': voluntary_monthly * 12,
            '기준_월급여': round(monthly_salary),
            '지역가입자_대비_절감_월': max(0, voluntary_saves),
            '임의계속가입_유리': is_voluntary_better,
            '적용기간': 36,  # 최대 36개월
            '신청기한': '퇴직일로부터 2개월 이내',
        }

        return {
            '예상연금소득': annual_pension,
            '연금소득공제': round(pension_deduction),
            '예상금융소득': round(annual_financial),
            '예상임대소득': annual_rental,
            '재산가액(건보산정)': round(total_property),
            '종합소득세': income_tax,
            '금융소득세': fi_tax,
            '건강보험료': health,
            '피부양자_가능여부': dep_check,
            '임의계속가입': voluntary_info,
            '총_세부담_연': (income_tax['total'] +
                             (fi_tax.get('total_tax') or fi_tax.get('tax', 0)) +
                             health['annual_total']),
        }

    def _project_cash_flow(self) -> dict:
        """월간 현금흐름 분석 (수입 - 지출 - 세금)"""
        income = self._project_retirement_income()
        tax_info = self._analyze_tax_and_insurance()
        expense = self.profile.expected_expense

        # 회원권 연회비
        membership_dues = sum(m.annual_dues for m in self.profile.memberships) / 12
        # 차량 유지비
        vehicle_cost = sum(v.annual_cost for v in self.profile.vehicles) / 12

        monthly_tax = tax_info['총_세부담_연'] / 12
        total_expense = (expense.total_monthly + membership_dues +
                         vehicle_cost + monthly_tax)

        return {
            '월수입': income['월수입_합계'],
            '월지출_생활': expense.total_monthly,
            '월지출_회원권': round(membership_dues),
            '월지출_차량': round(vehicle_cost),
            '월지출_세금건보': round(monthly_tax),
            '월지출_합계': round(total_expense),
            '월잉여(부족)': round(income['월수입_합계'] - total_expense),
            '연잉여(부족)': round((income['월수입_합계'] - total_expense) * 12),
        }

    def _project_reinvestment(self, reinvest_rate: float = 0.03,
                               inflation_rate: float = None) -> dict:
        """잉여금 자동 재투자 시뮬레이션 (은퇴~기대수명)
        매년 (월수입 - 월지출물가반영 - 월세금)의 잉여/부족을 재투자 계좌에 반영.
        부족 시 계좌에서 인출, 계좌 소진 후엔 누적 적자로 표시.
        """
        if inflation_rate is None:
            inflation_rate = self.inflation_rate
        personal = self.profile.personal
        retirement_age = personal.retirement_age
        lifespan = personal.expected_lifespan
        expense = self.profile.expected_expense

        # 은퇴 시점 기준 월지출 (생활비 + 회원권 + 차량)
        membership_dues = sum(m.annual_dues for m in self.profile.memberships) / 12
        vehicle_cost = sum(v.annual_cost for v in self.profile.vehicles) / 12
        base_monthly_expense = expense.total_monthly + membership_dues + vehicle_cost

        age_rows = self._project_income_by_age()
        age_map = {r['나이']: r for r in age_rows}

        balance = 0.0
        rows = []
        exhausted_age = None  # 계좌 소진 나이

        for age in range(retirement_age, lifespan + 1):
            row = age_map.get(age, {})
            monthly_income = row.get('월수입', 0)
            monthly_tax    = row.get('월세금', 0)

            years_since_retire = age - retirement_age
            monthly_expense = base_monthly_expense * ((1 + inflation_rate) ** years_since_retire)

            monthly_surplus = monthly_income - monthly_expense - monthly_tax
            annual_surplus  = monthly_surplus * 12

            # 전년도 잔액에 수익 적용 후 당해 잉여 반영
            balance = balance * (1 + reinvest_rate) + annual_surplus

            if balance < 0 and exhausted_age is None and annual_surplus < 0:
                exhausted_age = age

            rows.append({
                '나이': age,
                '월잉여': round(monthly_surplus),
                '누적잔액': round(balance),
            })

        final_balance = rows[-1]['누적잔액'] if rows else 0
        return {
            '수익률': reinvest_rate,
            '물가상승률': inflation_rate,
            '나이별': rows,
            '최종누적잔액': final_balance,
            '소진나이': exhausted_age,
        }

    def _get_private_pension_scenarios(self) -> list:
        """사적연금별 수령기간 변화에 따른 월수령액 시나리오 (5~30년)"""
        current_age = self.profile.personal.current_age
        results = []
        for pension in self.profile.pensions:
            if pension.pension_type.value == "국민연금":
                continue
            projection = project_pension_at_retirement(
                current_balance=pension.current_balance,
                monthly_contribution=pension.monthly_contribution,
                current_age=current_age,
                contribution_end_age=pension.contribution_end_age,
                payout_start_age=pension.expected_start_age,
                annual_return=pension.annual_return_rate,
            )
            balance = projection['balance_at_payout_start']
            _is_lifetime = pension.payout_period_years == 0
            _lifespan = self.profile.personal.expected_lifespan
            current_years = 0 if _is_lifetime else (pension.payout_period_years or 20)
            # 월수령 계산용 실제 기간 (종신=기대수명까지)
            _calc_years = (_lifespan - pension.expected_start_age) if _is_lifetime else current_years

            period_map = {}
            for years in [5, 10, 15, 20, 25, 30]:
                p = calculate_pension_payout(
                    balance, pension.expected_start_age, years, pension.annual_return_rate
                )
                period_map[years] = {
                    'monthly': p['monthly_payout'],
                    'total': p['total_payout_nominal'],
                }

            cur_payout = calculate_pension_payout(
                balance, pension.expected_start_age, _calc_years, pension.annual_return_rate
            )
            results.append({
                '연금명': pension.name,
                '종류': pension.pension_type.value,
                '수령시작_연령': pension.expected_start_age,
                '수령시점_적립금': balance,
                '현재_기간': current_years,
                '현재_월수령': cur_payout['monthly_payout'],
                '기간별': period_map,
                # 프론트엔드 재계산용 원시 데이터
                '_current_balance': pension.current_balance,
                '_monthly_contribution': pension.monthly_contribution,
                '_contribution_end_age': pension.contribution_end_age,
                '_annual_return': pension.annual_return_rate,
                '_current_age': current_age,
            })
        return results

    def _check_shortfall_remedies(self) -> dict:
        """현금흐름 부족 시 보완 가능 수단 분석 + 사적연금 기간별 시나리오 (항상 반환)"""
        cash_flow = self._project_cash_flow()
        shortfall = cash_flow['월잉여(부족)']
        scenarios = self._get_private_pension_scenarios()

        base = {'부족여부': shortfall < 0, '사적연금_기간별': scenarios}
        if shortfall >= 0:
            return base

        monthly_shortfall = abs(shortfall)
        remedies = []

        # 1. 주택연금
        hp = self._analyze_house_pension()
        if hp.get('eligible'):
            payout = hp.get('monthly_payout', 0)
            remedies.append({
                '방법': '주택연금 가입',
                '월추가수입': payout,
                '충당률': min(100, round(payout / monthly_shortfall * 100)),
                '설명': (f"자가 주택을 담보로 주택연금 가입 시 "
                         f"월 {payout:,}원 비과세 수령 (거주권 보장)"),
            })

        # 2. 금융자산 분할인출
        total_fa = self.profile.total_financial_assets
        remaining_years = (self.profile.personal.expected_lifespan
                           - self.profile.personal.retirement_age)
        if total_fa > 0 and remaining_years > 0:
            monthly_draw = round(total_fa / (remaining_years * 12))
            remedies.append({
                '방법': '금융자산 연금식 분할인출',
                '월추가수입': monthly_draw,
                '충당률': min(100, round(monthly_draw / monthly_shortfall * 100)),
                '설명': (f"금융자산 {total_fa // 10_000:,}만원을 "
                         f"{remaining_years}년간 나눠 인출 시 월 {monthly_draw:,}원"),
            })

        # 3. 사적연금 기간 단축 효과 (현재→10년)
        def _monthly(v, fallback):
            return v['monthly'] if isinstance(v, dict) else (v if v is not None else fallback)

        cur_total = sum(s['현재_월수령'] for s in scenarios)
        short_total = sum(_monthly(s['기간별'].get(10), s['현재_월수령']) for s in scenarios)
        increase = short_total - cur_total
        if increase > 0:
            remedies.append({
                '방법': '사적연금 수령기간 단축 (10년)',
                '월추가수입': increase,
                '충당률': min(100, round(increase / monthly_shortfall * 100)),
                '설명': (f"사적연금 수령기간을 10년으로 줄이면 "
                         f"월 {increase:,}원 추가 수령 가능"),
            })

        base.update({
            '월부족액': monthly_shortfall,
            '보완수단': remedies,
        })
        return base

    def _compare_scenarios(self) -> dict:
        """주요 의사결정 시나리오 비교"""
        scenarios = {}

        # 1. 차량/회원권 보유 vs 처분
        membership_value = sum(m.market_value for m in self.profile.memberships)
        membership_dues = sum(m.annual_dues for m in self.profile.memberships)
        vehicle_value = sum(v.market_value for v in self.profile.vehicles)
        vehicle_cost = sum(v.annual_cost for v in self.profile.vehicles)

        if membership_value > 0 or vehicle_value > 0:
            # 처분시 매각대금을 연 3% 운용 가정
            disposal_proceeds = membership_value + vehicle_value
            annual_return = disposal_proceeds * 0.03
            saved_costs = membership_dues + vehicle_cost

            scenarios['회원권차량_처분효과'] = {
                '매각가능금액': disposal_proceeds,
                '절약되는_연간비용': saved_costs,
                '운용수익_연3%': round(annual_return),
                '처분시_연간개선': round(annual_return + saved_costs),
                '건보료_재산점수_감소': '재산가액 감소로 지역가입자 건보료 인하 가능',
                '비고': '회원권은 양도세 과세대상이므로 매각시 양도차익 확인 필요',
            }

        # 2. 국민연금 수급개시 시기 비교
        nps_pensions = [p for p in self.profile.pensions
                        if p.pension_type.value == "국민연금"]
        if nps_pensions:
            nps = nps_pensions[0]
            normal_age = get_pension_start_age(self.profile.personal.birth_date.year)
            scenarios['국민연금_수급시기'] = compare_start_age_scenarios(
                nps.expected_monthly_payout, normal_age,
                self.profile.personal.expected_lifespan,
            )

        return scenarios

    def _analyze_tax_optimization(self) -> dict:
        """IRP/연금저축 세액공제 최적화 분석"""
        TAX_DEDUCTION_LIMIT = 9_000_000  # 연 900만원 한도
        SALARY_THRESHOLD = 55_000_000    # 5500만원 기준

        income = self.profile.current_income
        annual_income = income.annual_salary + income.annual_bonus

        # 현재 IRP + 연금저축 연간 납입액
        irp_annual = sum(
            p.monthly_contribution * 12
            for p in self.profile.pensions
            if p.pension_type.value in ("IRP", "연금저축")
        )

        remaining = max(0, TAX_DEDUCTION_LIMIT - irp_annual)
        deductible = min(irp_annual, TAX_DEDUCTION_LIMIT)

        # 세율: 총급여 5500만원 이하 16.5%, 초과 13.2%
        rate = 0.165 if annual_income <= SALARY_THRESHOLD else 0.132
        current_refund = round(deductible * rate)
        max_refund = round(TAX_DEDUCTION_LIMIT * rate)
        additional_refund = round(remaining * rate)

        return {
            '연간_납입액': round(irp_annual),
            '세액공제_한도': TAX_DEDUCTION_LIMIT,
            '한도_잔여액': round(remaining),
            '현재_환급액': current_refund,
            '최대_환급액': max_refund,
            '추가_환급가능액': additional_refund,
            '적용세율': rate,
            '한도도달여부': remaining == 0,
        }

    def _generate_recommendations(self) -> list:
        """주요 제언 생성"""
        recs = []
        cash_flow = self._project_cash_flow()
        tax_info = self._analyze_tax_and_insurance()

        # 1. 현금흐름 부족
        if cash_flow['월잉여(부족)'] < 0:
            recs.append({
                '우선순위': '높음',
                '항목': '월 현금흐름 부족',
                '내용': f"월 {abs(cash_flow['월잉여(부족)']):,}원 부족 예상. "
                        "지출 축소 또는 추가 수입원 확보 필요.",
            })

        # 2. 피부양자 자격
        _dep = tax_info['피부양자_가능여부']
        if not _dep['eligible']:
            if _dep.get('소득기준_충족'):
                # 소득은 기준 이하이나 재산 초과 → 피부양자 가능성 있음
                recs.append({
                    '우선순위': '중',
                    '항목': '건보료 부담',
                    '내용': '지역가입자로 건보료 부담 발생. '
                            '소득은 피부양자 기준 충족 — 배우자 직장가입자 통해 피부양자 등재 검토.',
                })
            else:
                # 소득 2,000만원 초과 → 피부양자 자격 없음, 등재 권유 생략
                _dep_income_man = _dep.get('연간소득_피부양자기준', 0) // 10000
                recs.append({
                    '우선순위': '중',
                    '항목': '건보료 부담',
                    '내용': f'지역가입자 건보료 발생 '
                            f'(피부양자 소득 기준 연 2,000만원 초과 — 현재 {_dep_income_man:,}만원). '
                            '임의계속가입·절세 상품 활용으로 부담 완화 검토.',
                })

        # 3. 금융소득종합과세
        if tax_info['예상금융소득'] > 20_000_000:
            recs.append({
                '우선순위': '중',
                '항목': '금융소득종합과세',
                '내용': '연 2천만원 초과시 종합과세. ISA 등 비과세 계좌 활용, '
                        '배우자 명의 분산 등 검토.',
            })

        # 4. 연금소득 1500만원 초과
        annual_private_pension = sum(
            self._analyze_pensions().get(p.name, {}).get('연수령액', 0)
            for p in self.profile.pensions
            if p.pension_type.value != "국민연금"
        )
        if annual_private_pension > 15_000_000:
            recs.append({
                '우선순위': '중',
                '항목': '사적연금 분리과세 한도 초과',
                '내용': f'연 1500만원 초과시(현재 {annual_private_pension:,}원) '
                        '종합과세 또는 16.5% 분리과세 선택. '
                        '수령기간 늘려 연 1500만원 이하 분할 검토.',
            })

        # 5. 회원권/차량 처분 검토
        scenarios = self._compare_scenarios()
        if '회원권차량_처분효과' in scenarios:
            improve = scenarios['회원권차량_처분효과']['처분시_연간개선']
            if improve > 5_000_000:
                recs.append({
                    '우선순위': '검토',
                    '항목': '회원권/차량 처분',
                    '내용': f'처분시 연 {improve:,}원 개선 효과 추정. '
                            '실사용 빈도 대비 비용 검토 필요.',
                })

        # 6. 주택연금 활용 — 은퇴 재원 부족 시에만 제언
        hp = self._analyze_house_pension()
        if hp.get('eligible') and cash_flow['월잉여(부족)'] < 0:
            recs.append({
                '우선순위': '검토',
                '항목': '주택연금',
                '내용': f"월 현금흐름 부족 상황 — 주택연금 가입시 월 {hp['monthly_payout']:,}원 "
                        '비과세 수령으로 부족분 보완 가능. 거주권 보장되며 사망시 정산.',
            })

        # 7. 세액공제 최적화
        tax_opt = self._analyze_tax_optimization()
        if not tax_opt['한도도달여부'] and tax_opt['추가_환급가능액'] > 0:
            recs.append({
                '우선순위': '높음',
                '항목': 'IRP/연금저축 세액공제 미활용',
                '내용': (f"연간 {tax_opt['한도_잔여액']:,}원 추가 납입 시 "
                         f"세금 {tax_opt['추가_환급가능액']:,}원 환급 가능. "
                         f"(세액공제 한도 900만원 중 "
                         f"{tax_opt['연간_납입액']:,}원 납입 중)"),
            })

        return recs


if __name__ == "__main__":
    print("이 모듈은 main.py에서 호출됩니다.")
