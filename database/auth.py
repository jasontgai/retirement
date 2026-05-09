"""
인증 유틸리티 - 비밀번호 해싱 / JWT 토큰
"""
import os
import bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from database.orm_models import User

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_this_secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """토큰 검증 후 payload 반환. 실패 시 None"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ============================================================
# DB 헬퍼
# ============================================================

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str, name: str) -> User:
    user = User(email=email, password_hash=hash_password(password), name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user and user.password_hash and verify_password(password, user.password_hash):
        return user
    return None


def get_user_by_oauth(db: Session, provider: str, oauth_id: str) -> User | None:
    return db.query(User).filter(
        User.oauth_provider == provider,
        User.oauth_id == oauth_id,
    ).first()


def create_oauth_user(db: Session, email: str, name: str, provider: str, oauth_id: str) -> User:
    user = User(email=email, name=name, oauth_provider=provider, oauth_id=oauth_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
