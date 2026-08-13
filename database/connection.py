"""
MySQL 연결 및 세션 관리 (SQLAlchemy 2.x)
"""
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

DATABASE_URL = (
    f"mysql+pymysql://{quote_plus(os.getenv('DB_USER', 'root'))}:"
    f"{quote_plus(os.getenv('DB_PASSWORD', ''))}@"
    f"{os.getenv('DB_HOST', 'localhost')}:"
    f"{os.getenv('DB_PORT', '3306')}/"
    f"{os.getenv('DB_NAME', 'retirement_app')}"
    "?charset=utf8mb4"
)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI Depends용 DB 세션 제공"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """앱 시작 시 테이블 자동 생성 + 스키마 마이그레이션"""
    from database import orm_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    run_column_migrations(engine)


def _run_migrations():
    """기존 테이블 스키마 변경 (컬럼 추가/변경)"""
    from sqlalchemy import text
    stmts = [
        "ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(255) NULL",
        "ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(20) NULL",
        "ALTER TABLE users ADD COLUMN oauth_id VARCHAR(200) NULL",
    ]
    with engine.connect() as conn:
        for stmt in stmts:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass


def run_column_migrations(engine):
    """신규 컬럼 추가 — INFORMATION_SCHEMA로 존재 여부 확인 후 ALTER TABLE"""
    from sqlalchemy import text
    db_name = os.getenv('DB_NAME', 'retirement')
    new_cols = [
        ('profiles',     'parttime_monthly',      'BIGINT DEFAULT 0'),
        ('profiles',     'parttime_until_age',    'INT DEFAULT 70'),
        ('profiles',     'spouse_nps_monthly',    'BIGINT DEFAULT 0'),
        ('profiles',     'spouse_nps_start_age',  'INT DEFAULT 65'),
        ('profiles',     'spouse_other_monthly',  'BIGINT DEFAULT 0'),
        ('profiles',     'spouse_other_start_age','INT DEFAULT 65'),
        ('users',        'is_admin',              'TINYINT(1) NOT NULL DEFAULT 0'),
        ('real_estates', 'property_category',     "VARCHAR(50) NOT NULL DEFAULT '아파트'"),
    ]
    with engine.connect() as conn:
        for tbl, col, typedef in new_cols:
            try:
                exists = conn.execute(text(
                    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA=:db AND TABLE_NAME=:tbl AND COLUMN_NAME=:col"
                ), {'db': db_name, 'tbl': tbl, 'col': col}).scalar()
                if not exists:
                    conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN {col} {typedef}"))
                    conn.commit()
            except Exception:
                pass
