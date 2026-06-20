# -*- coding: utf-8 -*-
"""
STANDARD(user_id=1) / BEST(user_id=2) / GOOD(user_id=3) 레퍼런스 프로필
부동산·금융자산·부채·연금 각 테이블에 저장
출처: 2024 통계청 가계금융복지조사, 국민연금공단 → 2026년 물가 반영(×1.025²)
기준: 60세 부부 (생년 1966-05-31), 부부 합산
"""
import sys
sys.path.insert(0, 'c:/Users/jason004/retirement_app')
from datetime import date
from database.connection import SessionLocal
from database.orm_models import (
    User, Profile, PensionRow, RealEstateRow,
    FinancialAssetRow, DebtRow,
)

def pv(pmt, rate_pct, yrs, payout_yr=20):
    """월수령액 → 현재나이 기준 PV (적립금 추정용)"""
    if pmt <= 0 or yrs < 0:
        return 0
    r_a = max(rate_pct / 100, 0.001)
    r   = r_a / 12
    n   = int(payout_yr * 12)
    pv_s = pmt * (1 - (1 + r) ** (-n)) / r
    return int(pv_s / (1 + r_a) ** yrs)

# ─────────────────────────────────────────────────────────────
# 시나리오별 데이터 정의
# 현재나이=60세, 국민연금 개시=65세 → yrs_to_nps=5
# ─────────────────────────────────────────────────────────────

SCENARIOS = {

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STANDARD (user_id=1): 60대 국민연금 수급 평균 부부
    # 총자산 6억, 부동산 80%, 부부합산 NPS 126만, 60세 은퇴
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1: {
        'label': 'STANDARD',
        'profile': {
            'title':               '표준 은퇴 가이드 (60세 부부 평균)',
            'name':                '표준가이드',
            'birth_date':          date(1966, 5, 31),   # 60세
            'gender':              '남',
            'retirement_age':      60,
            'expected_lifespan':   90,
            'spouse_birth_date':   date(1968, 5, 31),   # 아내 58세
            'spouse_nps_monthly':  500_000,             # 아내 국민연금 2026
            'spouse_nps_start_age':65,
            'spouse_other_monthly':0,
            'annual_salary':       0,
            'annual_bonus':        0,
            'other_income':        0,
            'is_employee':         False,
            'parttime_monthly':    0,
            'living_cost':         2_000_000,
            'medical_cost':          250_000,
            'leisure_cost':          200_000,
            'insurance_premium':      70_000,
            'other_expense':           0,
        },
        # 연금 (남편 기준, 아내 NPS는 spouse_nps_monthly)
        'pensions': [
            {
                'pension_type':           '국민연금',
                'name':                   '국민연금 (남편)',
                'current_balance':        pv(760_000, 4.0, 5),   # PV at 60
                'monthly_contribution':   0,
                'contribution_end_age':   60,
                'expected_start_age':     65,
                'expected_monthly_payout':760_000,    # 남편 NPS 2026
                'annual_return_rate':     0.04,
                'payout_period_years':    20,
                'contribution_years':     30.0,
            },
            {
                'pension_type':           '퇴직연금DB',
                'name':                   '퇴직연금',
                'current_balance':        pv(460_000, 4.0, 0),
                'monthly_contribution':   0,
                'contribution_end_age':   60,
                'expected_start_age':     60,
                'expected_monthly_payout':460_000,
                'annual_return_rate':     0.04,
                'payout_period_years':    20,
                'contribution_years':     30.0,
            },
            {
                'pension_type':           'IRP',
                'name':                   'IRP',
                'current_balance':        pv(140_000, 4.0, 0),
                'monthly_contribution':   0,
                'contribution_end_age':   60,
                'expected_start_age':     60,
                'expected_monthly_payout':140_000,
                'annual_return_rate':     0.04,
                'payout_period_years':    20,
                'contribution_years':     10.0,
            },
            {
                'pension_type':           '개인연금',
                'name':                   '개인연금',
                'current_balance':        pv(180_000, 3.5, 0),
                'monthly_contribution':   0,
                'contribution_end_age':   60,
                'expected_start_age':     60,
                'expected_monthly_payout':180_000,
                'annual_return_rate':     0.035,
                'payout_period_years':    20,
                'contribution_years':     20.0,
            },
        ],
        # 부동산: 자가 아파트 1채 (480,000,000), 주담대는 부동산.debt에 기록
        'real_estates': [
            {
                'name':                '자가 아파트',
                'house_type':          '아파트',
                'market_value':        480_000_000,
                'official_price':      360_000_000,   # 공시가 = 시가 75%
                'debt':                40_000_000,    # 주택담보대출
                'monthly_rent_income': 0,
                'is_primary_residence':True,
                'acquisition_price':   300_000_000,
            },
        ],
        # 금융자산: 예금 60% + 주식/펀드 30% + 채권 10% (총 1.2억)
        'financial_assets': [
            {'name':'예금/적금',     'asset_type':'예금',      'amount': 72_000_000, 'annual_return_rate':0.035},
            {'name':'주식/펀드',     'asset_type':'주식',      'amount': 36_000_000, 'annual_return_rate':0.07 },
            {'name':'채권',          'asset_type':'채권',      'amount': 12_000_000, 'annual_return_rate':0.04 },
        ],
        # 부채: 기타 1,200만 (주담대 40M은 부동산.debt에 입력, 합계=52M)
        'debts': [
            {'name':'기타부채', 'debt_type':'기타대출', 'balance':12_000_000, 'interest_rate':0.05, 'monthly_payment':50_000},
        ],
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BEST (user_id=2): 상위 10% 수준, 65세 은퇴
    # 총자산 15억, 부동산 65%, 부부합산 NPS 270만
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    2: {
        'label': 'BEST',
        'profile': {
            'title':               'BEST 은퇴 가이드 (상위 10%, 65세 은퇴)',
            'name':                'BEST가이드',
            'birth_date':          date(1966, 5, 31),
            'gender':              '남',
            'retirement_age':      65,
            'expected_lifespan':   95,
            'spouse_birth_date':   date(1968, 5, 31),
            'spouse_nps_monthly':  1_000_000,          # 아내 NPS 2026
            'spouse_nps_start_age':65,
            'spouse_other_monthly':0,
            'annual_salary':       0,
            'annual_bonus':        0,
            'other_income':        0,
            'is_employee':         False,
            'parttime_monthly':    500_000,             # 파트타임 근로
            'parttime_until_age':  68,
            'living_cost':         3_600_000,
            'medical_cost':          400_000,
            'leisure_cost':          600_000,
            'insurance_premium':     200_000,
            'other_expense':           0,
        },
        'pensions': [
            {
                'pension_type':           '국민연금',
                'name':                   '국민연금 (남편)',
                'current_balance':        pv(1_700_000, 4.0, 5),
                'monthly_contribution':   0,
                'contribution_end_age':   65,
                'expected_start_age':     65,
                'expected_monthly_payout':1_700_000,
                'annual_return_rate':     0.04,
                'payout_period_years':    20,
                'contribution_years':     35.0,
            },
            {
                'pension_type':           '퇴직연금DB',
                'name':                   '퇴직연금',
                'current_balance':        pv(1_600_000, 4.0, 5),
                'monthly_contribution':   0,
                'contribution_end_age':   65,
                'expected_start_age':     65,
                'expected_monthly_payout':1_600_000,
                'annual_return_rate':     0.04,
                'payout_period_years':    20,
                'contribution_years':     35.0,
            },
            {
                'pension_type':           'IRP',
                'name':                   'IRP',
                'current_balance':        pv(750_000, 4.5, 5),
                'monthly_contribution':   0,
                'contribution_end_age':   65,
                'expected_start_age':     65,
                'expected_monthly_payout':750_000,
                'annual_return_rate':     0.045,
                'payout_period_years':    20,
                'contribution_years':     15.0,
            },
            {
                'pension_type':           '개인연금',
                'name':                   '개인연금',
                'current_balance':        pv(1_200_000, 3.7, 5),
                'monthly_contribution':   0,
                'contribution_end_age':   65,
                'expected_start_age':     65,
                'expected_monthly_payout':1_200_000,
                'annual_return_rate':     0.037,
                'payout_period_years':    20,
                'contribution_years':     25.0,
            },
        ],
        # 부동산: 자가 75억 + 투자용 2.25억 = 9.75억
        'real_estates': [
            {
                'name':                '자가 아파트',
                'house_type':          '아파트',
                'market_value':        750_000_000,
                'official_price':      562_500_000,
                'debt':                0,
                'monthly_rent_income': 0,
                'is_primary_residence':True,
                'acquisition_price':   400_000_000,
            },
            {
                'name':                '투자용 부동산',
                'house_type':          '아파트',
                'market_value':        225_000_000,
                'official_price':      168_750_000,
                'debt':                0,
                'monthly_rent_income': 600_000,
                'is_primary_residence':False,
                'acquisition_price':   150_000_000,
            },
        ],
        # 금융자산: 예금 50% + 주식 40% + 채권 10% (총 5.25억)
        'financial_assets': [
            {'name':'예금/적금',     'asset_type':'예금', 'amount':262_500_000, 'annual_return_rate':0.04},
            {'name':'주식/ETF/펀드', 'asset_type':'주식', 'amount':210_000_000, 'annual_return_rate':0.09},
            {'name':'채권/MMF',      'asset_type':'채권', 'amount': 52_500_000, 'annual_return_rate':0.04},
        ],
        'debts': [
            {'name':'기타부채', 'debt_type':'기타대출', 'balance':10_000_000, 'interest_rate':0.03, 'monthly_payment':30_000},
        ],
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GOOD (user_id=3): 상위 25~30% 수준, 63세 은퇴
    # 총자산 8.5억, 부동산 70%, 부부합산 NPS 170만
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    3: {
        'label': 'GOOD',
        'profile': {
            'title':               'GOOD 은퇴 가이드 (상위 25%, 63세 은퇴)',
            'name':                'GOOD가이드',
            'birth_date':          date(1966, 5, 31),
            'gender':              '남',
            'retirement_age':      63,
            'expected_lifespan':   90,
            'spouse_birth_date':   date(1968, 5, 31),
            'spouse_nps_monthly':  650_000,
            'spouse_nps_start_age':65,
            'spouse_other_monthly':0,
            'annual_salary':       0,
            'annual_bonus':        0,
            'other_income':        0,
            'is_employee':         False,
            'parttime_monthly':    200_000,
            'parttime_until_age':  65,
            'living_cost':         2_450_000,
            'medical_cost':          300_000,
            'leisure_cost':          300_000,
            'insurance_premium':      50_000,
            'other_expense':           0,
        },
        'pensions': [
            {
                'pension_type':           '국민연금',
                'name':                   '국민연금 (남편)',
                'current_balance':        pv(1_050_000, 4.0, 5),
                'monthly_contribution':   0,
                'contribution_end_age':   63,
                'expected_start_age':     65,
                'expected_monthly_payout':1_050_000,
                'annual_return_rate':     0.04,
                'payout_period_years':    20,
                'contribution_years':     33.0,
            },
            {
                'pension_type':           '퇴직연금DB',
                'name':                   '퇴직연금',
                'current_balance':        pv(850_000, 4.0, 3),
                'monthly_contribution':   0,
                'contribution_end_age':   63,
                'expected_start_age':     63,
                'expected_monthly_payout':850_000,
                'annual_return_rate':     0.04,
                'payout_period_years':    20,
                'contribution_years':     33.0,
            },
            {
                'pension_type':           'IRP',
                'name':                   'IRP',
                'current_balance':        pv(280_000, 4.5, 3),
                'monthly_contribution':   0,
                'contribution_end_age':   63,
                'expected_start_age':     63,
                'expected_monthly_payout':280_000,
                'annual_return_rate':     0.045,
                'payout_period_years':    20,
                'contribution_years':     13.0,
            },
            {
                'pension_type':           '개인연금',
                'name':                   '개인연금',
                'current_balance':        pv(550_000, 3.7, 3),
                'monthly_contribution':   0,
                'contribution_end_age':   63,
                'expected_start_age':     63,
                'expected_monthly_payout':550_000,
                'annual_return_rate':     0.037,
                'payout_period_years':    20,
                'contribution_years':     23.0,
            },
        ],
        # 부동산: 자가 5.5억 + 투자용 0.95억 = 5.95억
        'real_estates': [
            {
                'name':                '자가 아파트',
                'house_type':          '아파트',
                'market_value':        550_000_000,
                'official_price':      412_500_000,
                'debt':                0,
                'monthly_rent_income': 0,
                'is_primary_residence':True,
                'acquisition_price':   350_000_000,
            },
            {
                'name':                '투자용 부동산',
                'house_type':          '오피스텔',
                'market_value':         45_000_000,
                'official_price':        33_750_000,
                'debt':                0,
                'monthly_rent_income': 200_000,
                'is_primary_residence':False,
                'acquisition_price':    35_000_000,
            },
        ],
        # 금융자산: 예금 60% + 주식 30% + 채권 10% (총 2.55억)
        'financial_assets': [
            {'name':'예금/적금',    'asset_type':'예금', 'amount':153_000_000, 'annual_return_rate':0.035},
            {'name':'주식/ETF',     'asset_type':'주식', 'amount': 76_500_000, 'annual_return_rate':0.08},
            {'name':'채권/MMF',     'asset_type':'채권', 'amount': 25_500_000, 'annual_return_rate':0.035},
        ],
        'debts': [
            {'name':'기타대출', 'debt_type':'기타대출', 'balance':30_000_000, 'interest_rate':0.04, 'monthly_payment':100_000},
        ],
    },
}


# ── DB 저장 ─────────────────────────────────────────────────────
db = SessionLocal()

for uid, sc in SCENARIOS.items():
    print(f"\n{'='*55}")
    print(f"  [{sc['label']}] user_id={uid}")
    print(f"{'='*55}")

    # 1. User 확인
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        print(f"  ⚠ user_id={uid} 없음 — skip")
        continue

    # 2. Profile 조회 or 생성
    profile = db.query(Profile).filter(Profile.user_id == uid).first()
    pd = sc['profile']
    if profile:
        print(f"  Profile id={profile.id} 업데이트")
    else:
        profile = Profile(user_id=uid)
        db.add(profile)
        print(f"  Profile 신규 생성")

    # Profile 필드 업데이트
    profile.title               = pd['title']
    profile.name                = pd['name']
    profile.birth_date          = pd['birth_date']
    profile.gender              = pd['gender']
    profile.retirement_age      = pd['retirement_age']
    profile.expected_lifespan   = pd['expected_lifespan']
    profile.spouse_birth_date   = pd['spouse_birth_date']
    profile.spouse_nps_monthly  = pd['spouse_nps_monthly']
    profile.spouse_nps_start_age= pd['spouse_nps_start_age']
    profile.spouse_other_monthly= pd['spouse_other_monthly']
    profile.annual_salary       = pd['annual_salary']
    profile.annual_bonus        = pd['annual_bonus']
    profile.other_income        = pd['other_income']
    profile.is_employee         = pd['is_employee']
    profile.parttime_monthly    = pd.get('parttime_monthly', 0)
    profile.parttime_until_age  = pd.get('parttime_until_age', 70)
    profile.living_cost         = pd['living_cost']
    profile.medical_cost        = pd['medical_cost']
    profile.leisure_cost        = pd['leisure_cost']
    profile.insurance_premium   = pd['insurance_premium']
    profile.other_expense       = pd.get('other_expense', 0)
    db.flush()

    pid = profile.id

    # 3. 기존 관련 데이터 삭제
    for Model in [PensionRow, RealEstateRow, FinancialAssetRow, DebtRow]:
        cnt = db.query(Model).filter(Model.profile_id == pid).delete()
        if cnt:
            print(f"  기존 {Model.__tablename__} {cnt}건 삭제")
    db.flush()

    # 4. 연금 입력
    for p in sc['pensions']:
        db.add(PensionRow(
            profile_id             = pid,
            pension_type           = p['pension_type'],
            name                   = p['name'],
            current_balance        = p['current_balance'],
            monthly_contribution   = p['monthly_contribution'],
            contribution_end_age   = p['contribution_end_age'],
            expected_start_age     = p['expected_start_age'],
            expected_monthly_payout= p['expected_monthly_payout'],
            annual_return_rate     = p['annual_return_rate'],
            payout_period_years    = p['payout_period_years'],
            contribution_years     = p['contribution_years'],
        ))
        print(f"  연금: {p['name']:15s} 월{p['expected_monthly_payout']:>9,}  잔액={p['current_balance']:>12,}")

    # 5. 부동산 입력
    for r in sc['real_estates']:
        db.add(RealEstateRow(
            profile_id          = pid,
            name                = r['name'],
            house_type          = r['house_type'],
            market_value        = r['market_value'],
            official_price      = r['official_price'],
            debt                = r['debt'],
            monthly_rent_income = r['monthly_rent_income'],
            is_primary_residence= r['is_primary_residence'],
            acquisition_price   = r['acquisition_price'],
        ))
        print(f"  부동산: {r['name']:20s} {r['market_value']:>12,}원")

    # 6. 금융자산 입력
    for f in sc['financial_assets']:
        db.add(FinancialAssetRow(
            profile_id       = pid,
            name             = f['name'],
            asset_type       = f['asset_type'],
            amount           = f['amount'],
            annual_return_rate=f['annual_return_rate'],
        ))
        print(f"  금융: {f['name']:15s} {f['amount']:>12,}원  수익률={f['annual_return_rate']*100:.1f}%")

    # 7. 부채 입력
    for d in sc['debts']:
        db.add(DebtRow(
            profile_id     = pid,
            name           = d['name'],
            debt_type      = d['debt_type'],
            balance        = d['balance'],
            interest_rate  = d['interest_rate'],
            monthly_payment= d['monthly_payment'],
        ))
        print(f"  부채: {d['name']:15s} {d['balance']:>12,}원  금리={d['interest_rate']*100:.1f}%")

db.commit()
db.close()
print("\n\n✓ 모든 시나리오 프로필 저장 완료!")

# ── 검증 ────────────────────────────────────────────────────
db2 = SessionLocal()
print("\n[ 검증 요약 ]")
for uid in [1, 2, 3]:
    prof = db2.query(Profile).filter(Profile.user_id == uid).first()
    if not prof: continue
    pens = db2.query(PensionRow).filter(PensionRow.profile_id == prof.id).all()
    reas = db2.query(RealEstateRow).filter(RealEstateRow.profile_id == prof.id).all()
    fins = db2.query(FinancialAssetRow).filter(FinancialAssetRow.profile_id == prof.id).all()
    debs = db2.query(DebtRow).filter(DebtRow.profile_id == prof.id).all()
    total_fin = sum(f.amount for f in fins)
    total_re  = sum(r.market_value for r in reas)
    total_debt= sum(d.balance for d in debs)
    monthly_pen = sum(p.expected_monthly_payout for p in pens) + prof.spouse_nps_monthly
    print(f"\n  user_id={uid} ({prof.title[:20]})")
    print(f"    연금 {len(pens)}건  부부합산월={monthly_pen:,}")
    print(f"    부동산 {len(reas)}건  합계={total_re:,}")
    print(f"    금융자산 {len(fins)}건  합계={total_fin:,}")
    print(f"    부채 {len(debs)}건  합계={total_debt:,}")
    print(f"    총자산={total_re+total_fin:,}  순자산={total_re+total_fin-total_debt:,}")
db2.close()
