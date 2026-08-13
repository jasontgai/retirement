"""
사용자 입력 데이터 모델
- 개인정보, 자산, 연금, 부채 등을 구조화
"""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from enum import Enum


class Gender(Enum):
    MALE = "남"
    FEMALE = "여"


class HouseType(Enum):
    OWN = "자가"
    JEONSE = "전세"
    WOLSE = "월세"
    OTHER = "기타"


class PensionType(Enum):
    """연금 종류"""
    NPS = "국민연금"           # 국민연금 (노령연금)
    RETIREMENT_DB = "퇴직연금DB"  # 확정급여형
    RETIREMENT_DC = "퇴직연금DC"  # 확정기여형
    IRP = "IRP"                # 개인형 퇴직연금
    PENSION_SAVINGS = "연금저축"  # 연금저축펀드/보험
    PRIVATE_PENSION = "개인연금"  # 일반 개인연금보험
    HOUSE_PENSION = "주택연금"   # 주택연금


@dataclass
class PersonalInfo:
    """개인 기본정보"""
    name: str
    birth_date: date
    gender: Gender
    retirement_age: int = 60         # 희망 은퇴연령
    expected_lifespan: int = 90      # 기대수명
    spouse_birth_date: Optional[date] = None
    dependents: int = 0              # 부양가족 수
    spouse_nps_monthly: float = 0
    spouse_nps_start_age: int = 65
    spouse_other_monthly: float = 0
    spouse_other_start_age: int = 65

    @property
    def current_age(self) -> int:
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def birth_year(self) -> int:
        return self.birth_date.year


@dataclass
class Pension:
    """연금 정보 (국민연금/퇴직연금/개인연금 공통)"""
    pension_type: PensionType
    name: str                        # 상품명/기관명
    current_balance: float = 0       # 현재 적립금액
    monthly_contribution: float = 0  # 월 납입금액
    contribution_end_age: int = 60   # 납입 종료 연령
    expected_start_age: int = 65     # 수령 개시 연령
    expected_monthly_payout: float = 0  # 예상 월 수령액 (DB형/국민연금)
    annual_return_rate: float = 0.04  # 예상 수익률 (DC형/적립식)
    payout_period_years: int = 0     # 확정기간형인 경우 (0이면 종신)
    contribution_years: float = 0    # 가입(납입) 기간 (년)


@dataclass
class RealEstate:
    """부동산"""
    name: str                        # "본가", "투자용 아파트" 등
    house_type: HouseType
    property_category: str = "아파트"  # 아파트/단독주택/빌라·다세대/상가/오피스텔/토지/기타
    market_value: float = 0          # 시세
    official_price: float = 0        # 공시가격 (건보/세금 산정용)
    debt: float = 0                  # 담보대출 잔액
    monthly_rent_income: float = 0   # 월 임대수입 (임대인 — 있을 경우)
    monthly_rent_expense: float = 0  # 월 임차료 (임차인 — 월세 거주 시 납부액)
    is_primary_residence: bool = True  # 1세대 1주택 여부
    acquisition_date: Optional[date] = None
    acquisition_price: float = 0


@dataclass
class FinancialAsset:
    """금융자산 - 예금/주식/채권/펀드 등"""
    name: str
    asset_type: str                  # "예금", "주식", "채권", "펀드", "ETF"
    amount: float = 0
    annual_return_rate: float = 0.03  # 예상 연수익률
    is_taxable: bool = True          # 과세대상 여부 (ISA 등 비과세 구분)


@dataclass
class Membership:
    """회원권 (골프/콘도 등)"""
    name: str                        # "○○ 골프회원권"
    membership_type: str             # "golf", "condo"
    market_value: float = 0          # 시세
    acquisition_price: float = 0
    annual_dues: float = 0           # 연회비


@dataclass
class Vehicle:
    """차량"""
    name: str
    market_value: float = 0
    annual_cost: float = 0           # 연간 유지비 (보험/세금/유류비)
    purchase_year: int = 0


@dataclass
class Debt:
    """부채"""
    name: str
    debt_type: str                   # "주담대", "신용대출", "전세대출"
    balance: float = 0
    interest_rate: float = 0.04
    monthly_payment: float = 0
    end_date: Optional[date] = None


@dataclass
class Insurance:
    name: str
    insurance_type: str = "연금보험"   # 연금보험 / 종신보험 / 저축보험 / 건강보험
    monthly_premium: float = 0         # 월 납입 보험료
    premium_end_age: int = 65          # 납입 종료 연령
    surrender_value: float = 0         # 현재 해약환급금 (자산)
    maturity_value: float = 0          # 만기/수령 예상 금액
    monthly_payout: float = 0          # 월 수령액 (연금형)
    payout_start_age: int = 65         # 수령 개시 연령
    payout_period_years: int = 0       # 수령기간(년, 0=종신)


@dataclass
class CurrentIncome:
    """현재 소득 (은퇴 전)"""
    annual_salary: float = 0         # 연봉 (세전)
    annual_bonus: float = 0
    other_income: float = 0          # 기타소득
    is_employee: bool = True         # 직장가입자 여부
    parttime_monthly: float = 0      # 은퇴 후 월 근로소득
    parttime_until_age: int = 70     # 근로소득 종료 연령


@dataclass
class ExpectedExpense:
    """은퇴 후 예상 지출 (월)"""
    living_cost: float = 2_500_000   # 기본 생활비
    medical_cost: float = 300_000    # 의료비
    leisure_cost: float = 500_000    # 여가/취미
    family_support: float = 0        # 자녀/부모 지원
    insurance_premium: float = 200_000  # 보험료
    other: float = 0

    @property
    def total_monthly(self) -> float:
        return (self.living_cost + self.medical_cost + self.leisure_cost +
                self.family_support + self.insurance_premium + self.other)


@dataclass
class UserProfile:
    """전체 사용자 프로필 - 모든 정보 통합"""
    personal: PersonalInfo
    current_income: CurrentIncome = field(default_factory=CurrentIncome)
    inflation_rate: float = 0.025
    pensions: List[Pension] = field(default_factory=list)
    real_estates: List[RealEstate] = field(default_factory=list)
    financial_assets: List[FinancialAsset] = field(default_factory=list)
    memberships: List[Membership] = field(default_factory=list)
    vehicles: List[Vehicle] = field(default_factory=list)
    debts: List[Debt] = field(default_factory=list)
    insurances: list = field(default_factory=list)
    expected_expense: ExpectedExpense = field(default_factory=ExpectedExpense)

    @property
    def total_real_estate_value(self) -> float:
        return sum(re.market_value for re in self.real_estates)

    @property
    def total_financial_assets(self) -> float:
        return sum(fa.amount for fa in self.financial_assets)

    @property
    def total_debt(self) -> float:
        return sum(d.balance for d in self.debts)

    @property
    def total_insurance_surrender_value(self) -> float:
        return sum(i.surrender_value for i in self.insurances)

    @property
    def net_worth(self) -> float:
        membership_value = sum(m.market_value for m in self.memberships)
        vehicle_value = sum(v.market_value for v in self.vehicles)
        return (self.total_real_estate_value + self.total_financial_assets +
                membership_value + vehicle_value +
                self.total_insurance_surrender_value - self.total_debt)
