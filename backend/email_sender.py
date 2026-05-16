"""
SMTP 이메일 발송 유틸
.env 환경변수:
  SMTP_HOST     - SMTP 서버 (기본: smtp.gmail.com)
  SMTP_PORT     - 포트 (기본: 587, STARTTLS)
  SMTP_USER     - 발신 계정
  SMTP_PASSWORD - 앱 비밀번호
  SMTP_FROM     - 발신자명 포함 주소 (기본: SMTP_USER)
"""
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)


def _send(to_email: str, subject: str, html_body: str) -> bool:
    """SMTP STARTTLS로 HTML 메일 발송. 성공 True / 실패 False."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP 설정이 없어 이메일을 발송하지 않습니다 (콘솔 출력만).")
        logger.info("[EMAIL] to=%s subject=%s body=%s", to_email, subject, html_body)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to_email], msg.as_bytes())
        return True
    except Exception as exc:
        logger.error("이메일 발송 실패: %s", exc)
        return False


def send_password_reset_email(to_email: str, name: str, code: str) -> bool:
    """비밀번호 재설정 인증번호 메일 발송 (유효시간 15분)"""
    subject = "[은퇴설계] 비밀번호 재설정 인증번호"
    html = f"""
<div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:24px;
            border:1px solid #e0e0e0;border-radius:12px;">
  <h2 style="color:#1565c0;margin-bottom:4px;">💰 은퇴설계</h2>
  <p style="color:#555;margin-top:0;">비밀번호 재설정</p>
  <hr style="border:none;border-top:1px solid #eee;margin:16px 0;">
  <p>안녕하세요, <strong>{name}</strong>님.</p>
  <p>아래 <strong>6자리 인증번호</strong>를 앱의 비밀번호 찾기 화면에 입력하세요.</p>
  <div style="background:#f5f5f5;border-radius:8px;padding:20px;text-align:center;margin:20px 0;">
    <span style="font-size:36px;font-weight:bold;letter-spacing:8px;color:#1565c0;">{code}</span>
  </div>
  <p style="color:#e53935;font-size:13px;">⏰ 유효시간: <strong>15분</strong> (1회 사용 후 만료)</p>
  <p style="color:#888;font-size:12px;margin-top:24px;">
    본인이 요청하지 않은 경우 이 메일을 무시하세요.
  </p>
</div>
"""
    return _send(to_email, subject, html)
