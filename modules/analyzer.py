"""
은퇴설계 통합 분석 엔진
- 사용자 프로필을 받아 모든 모듈을 호출하여 종합 분석
- 시나리오 비교 및 리스크 평가
"""
import sys
import os
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
    check_dependent_eligibility,
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
            '예상수입': self._project_retirement_income(),
            '나이별수입': self._project_income_by_age(),
            '퇴직연금_포트폴리오': self._analyze_pension_portfolio_scenarios(),
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
                adjusted_monthly = adjust_pension_amount(
                    pension.expected_monthly_payout, normal_age, actual_start
                )
                results[pension.name] = {
                    '종류': pension.pension_type.value,
                    '정상수급연령': normal_age,
                    '실제수급연령': actual_start,
                    '수령시작_연령': actual_start,
                    '개시년도': current_year + max(0, actual_start - current_age),
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

                payout_years = pension.payout_period_years or 20
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
                    '수령기간': payout['payout_years'],
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

        return {
            '월수입_합계': sum(monthly_sources.values()),
            '연수입_합계': annual_total,
            '항목별': monthly_sources,
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

        rows = []
        for age in range(55, lifespan + 1):
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
                        sources[pension.name] = amt

            for ins in self.profile.insurances:
                if ins.insurance_type != "연금보험" or ins.monthly_payout <= 0:
                    continue
                start = ins.payout_start_age
                period = ins.payout_period_years
                end = start + period if period > 0 else lifespan + 1
                if start <= age < end:
                    sources[ins.name] = ins.monthly_payout

            # 은퇴 후 근로소득
            inc = self.profile.current_income
            if inc.parttime_monthly > 0 and retirement_age <= age < inc.parttime_until_age:
                sources['근로소득'] = int(inc.parttime_monthly)

            # 배우자 연금
            p_info = self.profile.personal
            if p_info.spouse_nps_monthly > 0 and age >= p_info.spouse_nps_start_age:
                sources['배우자 국민연금'] = int(p_info.spouse_nps_monthly)
            if p_info.spouse_other_monthly > 0 and age >= p_info.spouse_other_start_age:
                sources['배우자 기타연금'] = int(p_info.spouse_other_monthly)

            rows.append({
                '나이': age,
                '월수입': sum(sources.values()),
                '항목별': sources,
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

        # 부동산 공시가격 합산 (건보료 산정용)
        property_value = sum(
            (re.official_price or re.market_value * 0.7)
            for re in self.profile.real_estates
        )
        # 회원권도 재산에 포함
        membership_value = sum(m.market_value for m in self.profile.memberships)
        total_property = property_value + membership_value

        # 종합소득세 (연금 + 임대 + 금융소득 종합과세분)
        pension_deduction = calculate_pension_income_deduction(annual_pension)
        taxable_pension = max(0, annual_pension - pension_deduction)
        # 단순화: 기본공제 150만원만 적용
        taxable_income = taxable_pension + annual_rental - 1_500_000
        income_tax = calculate_income_tax(max(0, taxable_income))

        # 금융소득세
        fi_tax = calculate_financial_income_tax(
            annual_financial, taxable_income
        )

        # 건강보험료 (지역가입자 가정)
        health = calculate_health_insurance_local(
            annual_pension_income=annual_pension,
            annual_financial_income=annual_financial,
            annual_other_income=annual_rental,
            property_value=total_property,
        )

        # 피부양자 가능성
        total_income_for_dependent = (
            annual_pension * 0.5 + annual_financial + annual_rental
        )
        dep_check = check_dependent_eligibility(
            total_income_for_dependent, total_property
        )

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
            current_years = pension.payout_period_years or 20

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
                balance, pension.expected_start_age, current_years, pension.annual_return_rate
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

    def _analyze_pension_portfolio_scenarios(self) -> list:
        """DC형·IRP 퇴직연금의 포트폴리오 유형별 시나리오 비교"""
        SCENARIOS = [
            ('예금형',  0.015),
            ('채권형',  0.040),
            ('TDF/혼합', 0.055),
            ('주식형',  0.080),
        ]
        current_age = self.profile.personal.current_age
        results = []

        for pension in self.profile.pensions:
            if pension.pension_type.value not in ('퇴직연금DC', 'IRP', '연금저축'):
                continue

            payout_years = pension.payout_period_years or 20
            scenarios_out = []
            current_rate = pension.annual_return_rate

            for label, rate in SCENARIOS:
                proj = project_pension_at_retirement(
                    current_balance=pension.current_balance,
                    monthly_contribution=pension.monthly_contribution,
                    current_age=current_age,
                    contribution_end_age=pension.contribution_end_age,
                    payout_start_age=pension.expected_start_age,
                    annual_return=rate,
                )
                payout = calculate_pension_payout(
                    total_amount=proj['balance_at_payout_start'],
                    start_age=pension.expected_start_age,
                    payout_years=payout_years,
                    annual_return=rate,
                )
                is_current = abs(rate - current_rate) < 0.005
                scenarios_out.append({
                    '유형': label,
                    '수익률': rate,
                    '수령시점_적립금': proj['balance_at_payout_start'],
                    '월수령액': payout['monthly_payout'],
                    '현재설정': is_current,
                })

            # 현재 설정 기준 비교값 계산
            base = next((s for s in scenarios_out if s['현재설정']), scenarios_out[0])
            for s in scenarios_out:
                s['월수령액_증감'] = s['월수령액'] - base['월수령액']
                s['적립금_증감'] = s['수령시점_적립금'] - base['수령시점_적립금']

            results.append({
                '연금명': pension.name,
                '종류': pension.pension_type.value,
                '현재_수익률': current_rate,
                '수령기간': payout_years,
                '시나리오': scenarios_out,
            })

        return results

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
        if not tax_info['피부양자_가능여부']['eligible']:
            recs.append({
                '우선순위': '중',
                '항목': '건보료 부담',
                '내용': '지역가입자로 건보료 부담 발생. '
                        '배우자 직장가입자 통한 피부양자 등재 검토.',
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

        # 6. 주택연금 활용
        hp = self._analyze_house_pension()
        if hp.get('eligible'):
            recs.append({
                '우선순위': '검토',
                '항목': '주택연금',
                '내용': f"주택연금 가입시 월 {hp['monthly_payout']:,}원 비과세 수령 가능. "
                        '거주권 보장되며 사망시 정산.',
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
