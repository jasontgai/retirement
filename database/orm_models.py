"""
SQLAlchemy ORM 테이블 정의
"""
from datetime import datetime
from sqlalchemy import (
    Integer, String, BigInteger, Float, Boolean, Date, DateTime,
    Text, ForeignKey, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connection import Base


class User(Base):
    """회원 계정"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    oauth_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    oauth_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    profiles: Mapped[list["Profile"]] = relationship("Profile", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    """사용자 은퇴설계 프로필"""
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="기본 플랜")

    # 개인정보
    name: Mapped[str] = mapped_column(String(100))
    birth_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10))
    retirement_age: Mapped[int] = mapped_column(Integer, default=60)
    expected_lifespan: Mapped[int] = mapped_column(Integer, default=90)
    spouse_birth_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    dependents: Mapped[int] = mapped_column(Integer, default=0)
    spouse_nps_monthly: Mapped[int] = mapped_column(BigInteger, default=0)
    spouse_nps_start_age: Mapped[int] = mapped_column(Integer, default=65)
    spouse_other_monthly: Mapped[int] = mapped_column(BigInteger, default=0)
    spouse_other_start_age: Mapped[int] = mapped_column(Integer, default=65)

    # 현재 소득
    annual_salary: Mapped[int] = mapped_column(BigInteger, default=0)
    annual_bonus: Mapped[int] = mapped_column(BigInteger, default=0)
    other_income: Mapped[int] = mapped_column(BigInteger, default=0)
    is_employee: Mapped[bool] = mapped_column(Boolean, default=True)
    parttime_monthly: Mapped[int] = mapped_column(BigInteger, default=0)
    parttime_until_age: Mapped[int] = mapped_column(Integer, default=70)

    # 예상 지출
    living_cost: Mapped[int] = mapped_column(BigInteger, default=2_500_000)
    medical_cost: Mapped[int] = mapped_column(BigInteger, default=300_000)
    leisure_cost: Mapped[int] = mapped_column(BigInteger, default=500_000)
    family_support: Mapped[int] = mapped_column(BigInteger, default=0)
    insurance_premium: Mapped[int] = mapped_column(BigInteger, default=200_000)
    other_expense: Mapped[int] = mapped_column(BigInteger, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="profiles")
    pensions: Mapped[list["PensionRow"]] = relationship("PensionRow", back_populates="profile", cascade="all, delete-orphan")
    real_estates: Mapped[list["RealEstateRow"]] = relationship("RealEstateRow", back_populates="profile", cascade="all, delete-orphan")
    financial_assets: Mapped[list["FinancialAssetRow"]] = relationship("FinancialAssetRow", back_populates="profile", cascade="all, delete-orphan")
    memberships: Mapped[list["MembershipRow"]] = relationship("MembershipRow", back_populates="profile", cascade="all, delete-orphan")
    vehicles: Mapped[list["VehicleRow"]] = relationship("VehicleRow", back_populates="profile", cascade="all, delete-orphan")
    debts: Mapped[list["DebtRow"]] = relationship("DebtRow", back_populates="profile", cascade="all, delete-orphan")
    insurances: Mapped[list["InsuranceRow"]] = relationship("InsuranceRow", back_populates="profile", cascade="all, delete-orphan")
    analyses: Mapped[list["AnalysisResult"]] = relationship("AnalysisResult", back_populates="profile", cascade="all, delete-orphan")


class PensionRow(Base):
    __tablename__ = "pensions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    pension_type: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))
    current_balance: Mapped[int] = mapped_column(BigInteger, default=0)
    monthly_contribution: Mapped[int] = mapped_column(BigInteger, default=0)
    contribution_end_age: Mapped[int] = mapped_column(Integer, default=60)
    expected_start_age: Mapped[int] = mapped_column(Integer, default=65)
    expected_monthly_payout: Mapped[int] = mapped_column(BigInteger, default=0)
    annual_return_rate: Mapped[float] = mapped_column(Float, default=0.04)
    payout_period_years: Mapped[int] = mapped_column(Integer, default=0)
    contribution_years: Mapped[float] = mapped_column(Float, default=0)

    profile: Mapped["Profile"] = relationship("Profile", back_populates="pensions")


class RealEstateRow(Base):
    __tablename__ = "real_estates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100))
    house_type: Mapped[str] = mapped_column(String(20))
    property_category: Mapped[str] = mapped_column(String(50), default="아파트")
    market_value: Mapped[int] = mapped_column(BigInteger, default=0)
    official_price: Mapped[int] = mapped_column(BigInteger, default=0)
    debt: Mapped[int] = mapped_column(BigInteger, default=0)
    monthly_rent_income: Mapped[int] = mapped_column(BigInteger, default=0)
    monthly_rent_expense: Mapped[int] = mapped_column(BigInteger, default=0)
    is_primary_residence: Mapped[bool] = mapped_column(Boolean, default=True)
    acquisition_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    acquisition_price: Mapped[int] = mapped_column(BigInteger, default=0)

    profile: Mapped["Profile"] = relationship("Profile", back_populates="real_estates")


class FinancialAssetRow(Base):
    __tablename__ = "financial_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100))
    asset_type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[int] = mapped_column(BigInteger, default=0)
    annual_return_rate: Mapped[float] = mapped_column(Float, default=0.03)
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True)

    profile: Mapped["Profile"] = relationship("Profile", back_populates="financial_assets")


class MembershipRow(Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100))
    membership_type: Mapped[str] = mapped_column(String(50))
    market_value: Mapped[int] = mapped_column(BigInteger, default=0)
    acquisition_price: Mapped[int] = mapped_column(BigInteger, default=0)
    annual_dues: Mapped[int] = mapped_column(BigInteger, default=0)

    profile: Mapped["Profile"] = relationship("Profile", back_populates="memberships")


class VehicleRow(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100))
    market_value: Mapped[int] = mapped_column(BigInteger, default=0)
    annual_cost: Mapped[int] = mapped_column(BigInteger, default=0)
    purchase_year: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped["Profile"] = relationship("Profile", back_populates="vehicles")


class DebtRow(Base):
    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100))
    debt_type: Mapped[str] = mapped_column(String(50))
    balance: Mapped[int] = mapped_column(BigInteger, default=0)
    interest_rate: Mapped[float] = mapped_column(Float, default=0.04)
    monthly_payment: Mapped[int] = mapped_column(BigInteger, default=0)
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)

    profile: Mapped["Profile"] = relationship("Profile", back_populates="debts")


class InsuranceRow(Base):
    __tablename__ = "insurances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    insurance_type: Mapped[str] = mapped_column(String(50), default="연금보험")
    monthly_premium: Mapped[int] = mapped_column(BigInteger, default=0)
    premium_end_age: Mapped[int] = mapped_column(Integer, default=65)
    surrender_value: Mapped[int] = mapped_column(BigInteger, default=0)
    maturity_value: Mapped[int] = mapped_column(BigInteger, default=0)
    monthly_payout: Mapped[int] = mapped_column(BigInteger, default=0)
    payout_start_age: Mapped[int] = mapped_column(Integer, default=65)
    payout_period_years: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped["Profile"] = relationship("Profile", back_populates="insurances")


class AnalysisResult(Base):
    """분석 결과 이력"""
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    result_json: Mapped[str] = mapped_column(Text(length=2**24))  # MEDIUMTEXT
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    profile: Mapped["Profile"] = relationship("Profile", back_populates="analyses")


class RevokedToken(Base):
    """로그아웃된 JWT 블랙리스트 (토큰 만료 전 무효화)"""
    __tablename__ = "revoked_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA-256
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # JWT exp (정리용)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Scenario(Base):
    """시나리오 비교 (GOOD / BEST / STANDARD) — DB 저장"""
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    label: Mapped[str] = mapped_column(String(20), nullable=False)   # GOOD | BEST | STANDARD
    retire_age: Mapped[int] = mapped_column(Integer, default=0)
    monthly_income: Mapped[int] = mapped_column(BigInteger, default=0)
    monthly_expense: Mapped[int] = mapped_column(BigInteger, default=0)
    monthly_surplus: Mapped[int] = mapped_column(BigInteger, default=0)
    total_assets: Mapped[int] = mapped_column(BigInteger, default=0)
    detail_json: Mapped[str | None] = mapped_column(Text(length=2**24), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class PasswordResetToken(Base):
    """비밀번호 재설정 인증번호"""
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hex
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserActivity(Base):
    """사용자 활동 로그 (접속 IP, 디바이스, 행동 이력)"""
    __tablename__ = "user_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)       # JSON
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)   # IPv6 max 45
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # desktop/mobile/tablet
    browser: Mapped[str | None] = mapped_column(String(50), nullable=True)
    os_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
