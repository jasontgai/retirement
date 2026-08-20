"""
상세 인터랙티브 차트 HTML 생성기
D3.js v7 기반 standalone HTML 반환
"""
import json
import os as _os

# D3.js 인라인 캐시 — CDN 의존성 제거 (모듈 로드 시 1회만 읽음)
_D3_JS_PATH = _os.path.join(_os.path.dirname(__file__), 'static', 'd3.v7.min.js')
try:
    with open(_D3_JS_PATH, 'r', encoding='utf-8') as _f:
        _D3_JS_INLINE = _f.read()
except Exception:
    _D3_JS_INLINE = None  # 파일 없으면 CDN 폴백


def generate_detail_html(data: dict, compact: bool = False, show_detail: bool = False) -> str:
    """data dict → 완전한 standalone HTML string.
    compact=True: iframe 삽입용 (차트 높이 고정). compact=False: 새 창 전체화면용.
    show_detail=True: 상세보기 모드로 초기화 (범례 확장, 세부 선 표시).
    """
    data_json = json.dumps(data, ensure_ascii=False, default=str)
    _d3_tag = (f'<script>{_D3_JS_INLINE}</script>'
               if _D3_JS_INLINE
               else '<script src="https://d3js.org/d3.v7.min.js"></script>')
    _detail_cls  = 'show-detail' if show_detail else ''
    _detail_js   = 'true'  if show_detail else 'false'
    _get_height_js = (
        # compact: 너비 기반 반응형 — 넓은 화면일수록 차트가 높아짐 (height ↔ iframe 연동)
        # innerWidth(=iframe 너비)는 height와 순환 의존성이 없어 안전
        "function getHeight() { const w = window.innerWidth || 400; return Math.max(180, Math.min(280, Math.round(w * 0.42))); }"
        if compact else
        "function getHeight() { return Math.max(400, window.innerHeight - 280); }"
    )
    _resize_report_js = (
        """function reportHeight() {
  const isMobile = window.innerWidth <= 640;
  const h = Math.ceil(document.body.scrollHeight) + (isMobile ? 12 : 8);
  window.parent.postMessage({type:'streamlit:setFrameHeight', height: h}, '*');
}
function reportHeightDeferred() {
  requestAnimationFrame(reportHeight);
  setTimeout(reportHeight, 200);
  setTimeout(reportHeight, 600);
}
// Streamlit이 setFrameHeight를 수신하려면 componentReady를 먼저 보내야 함
window.parent.postMessage({type:'streamlit:componentReady', apiVersion: 1}, '*');
if (window.ResizeObserver) {
  new ResizeObserver(reportHeight).observe(document.body);
}
window.addEventListener('resize', reportHeightDeferred);
reportHeightDeferred();"""
        if compact else ""
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>은퇴 시나리오 상세 분석</title>
{_d3_tag}
<style>
  :root {{
    --bg:          #ffffff;
    --bg-panel:    #f8f8ff;
    --border:      #e0e0f0;
    --text:        #1a1a2e;
    --text-muted:  #7070a0;
    --h1-color:    #7B2FFF;
    --val-color:   #FF6600;
    --input-bg:    #ffffff;
    --input-bdr:   #d0d0e8;
    --grid-line:   #f0f0f8;
    --axis-text:   #9090b0;
    --zero-line:   #9090b8;
    --tt-bg:       rgba(255,255,255,0.97);
    --tt-border:   #e0e0f0;
    --tt-age:      #7B2FFF;
    --tt-key:      #9090b0;
    --tt-pos:      #00AA55;
    --tt-neg:      #FF0077;
    --sb-bg:       #f8f8ff;
    --sb-border:   #e0e0f0;
    --retire-clr:  #FF6600;
    --inc-line:    #00AAFF;
    --exp-line:    #FF0077;
    --sur-line:    #7B2FFF;
    --def-fill:    rgba(255,0,119,0.08);
    --dot-fill:    #00AAFF;
    --dot-stroke:  #0077CC;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg:          #0A0A12;
      --bg-panel:    #10101E;
      --border:      #28283E;
      --text:        #e0e0f4;
      --text-muted:  #6868a0;
      --h1-color:    #9B5FFF;
      --val-color:   #FF8833;
      --input-bg:    #14141E;
      --input-bdr:   #28283E;
      --grid-line:   #12121E;
      --axis-text:   #505078;
      --zero-line:   #5858a0;
      --tt-bg:       rgba(10,10,20,0.96);
      --tt-border:   #28283E;
      --tt-age:      #9B5FFF;
      --tt-key:      #6868a0;
      --tt-pos:      #44DD88;
      --tt-neg:      #FF4499;
      --sb-bg:       #10101E;
      --sb-border:   #28283E;
      --retire-clr:  #FF8833;
      --inc-line:    #00AAFF;
      --exp-line:    #FF0077;
      --sur-line:    #9B5FFF;
      --def-fill:    rgba(255,0,119,0.10);
      --dot-fill:    #00AAFF;
      --dot-stroke:  #0077CC;
    }}
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ height: auto; }}
  body {{
    font-family: 'Segoe UI', 'Apple SD Gothic Neo', sans-serif;
    background: var(--bg);
    color: var(--text);
    {'min-height:0;' if compact else 'min-height:100vh;'}
  }}
  h1 {{
    font-size: 1.1rem;
    font-weight: 600;
    padding: 8px 16px 2px;
    color: var(--h1-color);
  }}
  .subtitle {{
    font-size: 0.72rem;
    color: var(--text-muted);
    padding: 0 16px 6px;
  }}

  /* ─── 컨트롤 패널 ─── */
  .controls {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 6px 12px 2px;
    background: var(--bg-panel);
  }}
  .ctrl-group {{
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 140px;
  }}
  .ctrl-group label {{
    font-size: 0.72rem;
    color: var(--text-muted);
    font-weight: 500;
  }}
  .ctrl-group input[type=range] {{
    width: 160px;
    cursor: pointer;
    -webkit-appearance: none;
    appearance: none;
    height: 28px;
    background: transparent;
    outline: none;
    padding: 0;
    margin: 0;
  }}
  .ctrl-group input[type=range]::-webkit-slider-runnable-track {{
    height: 2px;
    background: var(--border);
    border-radius: 2px;
  }}
  .ctrl-group input[type=range]::-moz-range-track {{
    height: 2px;
    background: var(--border);
    border-radius: 2px;
  }}
  .ctrl-group input[type=range]::-webkit-slider-thumb {{
    -webkit-appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--retire-clr);
    cursor: pointer;
    border: none;
    box-shadow: 0 0 0 2px var(--bg);
    margin-top: -7px;
  }}
  .ctrl-group input[type=range]::-moz-range-thumb {{
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--retire-clr);
    cursor: pointer;
    border: none;
    box-shadow: 0 0 0 2px var(--bg);
  }}
  .ctrl-group input[type=number] {{
    width: 80px;
    background: var(--input-bg);
    border: 1px solid var(--input-bdr);
    border-radius: 4px;
    color: var(--text);
    padding: 3px 7px;
    font-size: 0.8rem;
  }}
  .val-display {{
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--val-color);
  }}
  .spending-grid {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .spending-item {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }}
  .spending-item label {{
    font-size: 0.68rem;
    color: var(--text-muted);
    text-align: center;
  }}
  .spending-item input[type=number] {{
    width: 60px;
    text-align: center;
  }}

  /* ─── 차트 영역 ─── */
  #chart-container {{
    position: relative;
    padding: 0 10px 0;
    user-select: none;
  }}
  svg {{
    display: block;
    width: 100%;
    overflow: visible;
  }}
  .grid line {{
    stroke: var(--grid-line);
    stroke-dasharray: 3,3;
  }}
  .axis text {{ fill: var(--axis-text); font-size: 11px; }}
  .axis path, .axis line {{ stroke: var(--border); }}
  .axis-label {{ fill: var(--text-muted); font-size: 11px; }}

  /* ── 선 굵기 계층 ──────────────────────────────
     잉여/부족 3px  >  합계선 2px  >  거울/세부 1px  >  기준선 0.8px
  ─────────────────────────────────────────────── */
  .source-line {{        /* 수입 세부항목 — 얇은선 (상세보기) */
    fill: none;
    stroke-width: 1px;
    stroke-opacity: 0.65;
  }}
  .ctb-neg-line {{       /* 지출 세부항목 — 얇은 점선 (상세보기) */
    fill: none;
    stroke-width: 1px;
    stroke-dasharray: 4,3;
    stroke-opacity: 0.60;
  }}
  .income-total-line {{  /* 수입 합계 */
    fill: none;
    stroke: var(--inc-line);
    stroke-width: 2px;
  }}
  .expense-neg-line {{   /* 지출 합계 실선 (음수) */
    fill: none;
    stroke: var(--exp-line);
    stroke-width: 2px;
  }}
  .expense-mirror-line {{ /* 지출 합계 거울 점선 (양수) */
    fill: none;
    stroke: var(--exp-line);
    stroke-width: 2px;
    stroke-dasharray: 5,4;
    stroke-opacity: 0.45;
  }}
  .surplus-line {{       /* 잉여/부족 — 점선 */
    fill: none;
    stroke: var(--sur-line);
    stroke-width: 2px;
    stroke-dasharray: 8,5;
    stroke-linejoin: round;
    stroke-linecap: round;
  }}
  .surplus-zone, .deficit-zone {{
    fill: none;
    pointer-events: none;
  }}
  .zero-line {{          /* 기준 0선 */
    stroke: var(--zero-line);
    stroke-width: 1.8px;
  }}
  .retire-line {{        /* 은퇴선 — 참조선 */
    stroke: var(--retire-clr);
    stroke-width: 1.5px;
    stroke-dasharray: 6,4;
    cursor: ew-resize;
  }}
  .retire-handle {{
    fill: var(--retire-clr);
    cursor: ew-resize;
    opacity: 0.9;
  }}
  .retire-label {{
    fill: var(--retire-clr);
    font-size: 11px;
    font-weight: 700;
    pointer-events: none;
  }}

  /* ─── 범례 ─── */
  #legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 5px 12px;
    padding: 4px 12px 6px;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 5px;
    cursor: pointer;
    font-size: 0.75rem;
    color: var(--text);
    transition: opacity .2s;
  }}
  .legend-item.hidden {{ opacity: 0.3; }}
  .leg-detail {{ display: none; }}
  #legend.show-detail .leg-detail {{ display: block; }}
  #legend.show-detail .leg-detail.legend-item {{ display: flex; }}
  .legend-swatch {{
    width: 12px;
    height: 12px;
    border-radius: 2px;
    flex-shrink: 0;
  }}

  /* ─── 툴팁 ─── */
  #tooltip {{
    position: fixed;
    pointer-events: auto;
    background: var(--tt-bg);
    border: 1px solid var(--tt-border);
    border-radius: 8px;
    padding: clamp(6px, 0.8vw + 2px, 10px) clamp(9px, 1vw + 4px, 14px);
    font-size: clamp(0.60rem, 0.35rem + 1vw, 0.78rem);
    line-height: 1.6;
    max-width: clamp(180px, 38vw, 260px);
    max-height: 78vh;
    overflow-y: auto;
    display: none;
    z-index: 999;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  }}
  #tooltip .tt-toggle {{
    display: block;
    width: 100%;
    margin-top: 6px;
    padding: 3px 0;
    background: none;
    border: none;
    border-top: 1px solid var(--border);
    color: var(--tt-key);
    font-size: clamp(0.54rem, 0.24rem + 1vw, 0.72rem);
    cursor: pointer;
    text-align: center;
    opacity: 0.75;
  }}
  #tooltip .tt-toggle:hover {{ opacity: 1; color: var(--tt-age); }}
  #tooltip .tt-age {{
    font-weight: 700;
    color: var(--tt-age);
    margin-bottom: 4px;
    font-size: clamp(0.66rem, 0.42rem + 1vw, 0.85rem);
  }}
  #tooltip .tt-row {{
    display: flex;
    justify-content: space-between;
    gap: 12px;
  }}
  #tooltip .tt-key {{ color: var(--tt-key); }}
  #tooltip .tt-val {{ font-weight: 600; color: var(--text); }}
  #tooltip .tt-neg {{ color: var(--tt-neg); }}
  #tooltip .tt-pos {{ color: var(--tt-pos); }}
  #tooltip .tt-div {{
    border-top: 1px solid var(--border);
    margin: 4px 0;
  }}

  /* ─── 하단 상태 바 ─── */
  #statusbar {{
    position: sticky;
    bottom: 0;
    background: var(--sb-bg);
    border-top: 1px solid var(--sb-border);
    padding: 6px 20px;
    font-size: 0.73rem;
    color: var(--text-muted);
    display: flex;
    gap: 20px;
  }}
  #statusbar span b {{ color: var(--text); }}
</style>
</head>
<body>

<h1>📊 시나리오 분석</h1>
<p class="subtitle">은퇴선을 드래그하여 은퇴연령 조정 | 슬라이더로 물가·지출 체감률 실시간 변경 | 범례 클릭으로 항목 숨김/표시</p>

<div class="controls">
  <div class="ctrl-group">
    <label>🟠 은퇴연령</label>
    <input type="range" id="retireSlider" min="55" max="80" step="1" value="60">
    <span class="val-display"><span id="retireVal">60</span>세</span>
  </div>
  <div class="ctrl-group">
    <label>📈 물가상승률</label>
    <input type="range" id="inflSlider" min="0" max="10" step="0.1" value="2.5">
    <span class="val-display"><span id="inflVal">2.5</span>%</span>
  </div>

  <div class="ctrl-group" style="min-width:auto">
    <label>💸 나이별 지출 체감률 (%)</label>
    <div class="spending-grid">
      <div class="spending-item">
        <label> ~64세</label>
        <input type="number" class="sr-input" id="sr0" min="10" max="150" step="5" value="100">
      </div>
      <div class="spending-item">
        <label>65~69세</label>
        <input type="number" class="sr-input" id="sr1" min="10" max="150" step="5" value="90">
      </div>
      <div class="spending-item">
        <label>70~74세</label>
        <input type="number" class="sr-input" id="sr2" min="10" max="150" step="5" value="80">
      </div>
      <div class="spending-item">
        <label>75~79세</label>
        <input type="number" class="sr-input" id="sr3" min="10" max="150" step="5" value="70">
      </div>
      <div class="spending-item">
        <label>80~84세</label>
        <input type="number" class="sr-input" id="sr4" min="10" max="150" step="5" value="65">
      </div>
      <div class="spending-item">
        <label>85세+</label>
        <input type="number" class="sr-input" id="sr5" min="10" max="150" step="5" value="55">
      </div>
    </div>
  </div>
</div>

<div id="chart-container">
  <svg id="main-svg"></svg>
</div>
<div id="legend" class="{_detail_cls}"></div>
<div id="tooltip"></div>

<div id="statusbar">
  <span>은퇴연령: <b id="sb-retire">-</b></span>
  <span>물가상승률: <b id="sb-infl">-</b></span>
  <span>은퇴시 월수입: <b id="sb-income">-</b></span>
  <span>은퇴시 월지출: <b id="sb-expense">-</b></span>
  <span>잉여/부족: <b id="sb-surplus">-</b></span>
</div>

<script>
const RAW = {data_json};

// ─── CSS 변수 읽기 헬퍼 ───
function cssVar(name) {{
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}}

// ─── 초기 설정 ───
let retireAge  = RAW.retire_age;
let inflRate   = RAW.inflation;
let spendRates = [
  RAW.spending_rates.under65,
  RAW.spending_rates['65_69'],
  RAW.spending_rates['70_74'],
  RAW.spending_rates['75_79'],
  RAW.spending_rates['80_84']  ?? RAW.spending_rates['80plus'] ?? 0.65,
  RAW.spending_rates['85plus'] ?? 0.55,
];
let hiddenKeys  = new Set();
let showDetail  = {_detail_js};   // Python show_detail 파라미터로 초기화

// ─── 슬라이더 초기화 (범위는 데이터 나이 범위 그대로) ───
const _rs = document.getElementById('retireSlider');
_rs.min   = RAW.min_age ?? 50;
_rs.max   = RAW.max_age ?? 95;
_rs.value = retireAge;
document.getElementById('retireVal').textContent = retireAge;
document.getElementById('inflSlider').value = inflRate;
document.getElementById('inflVal').textContent = inflRate.toFixed(1);
document.querySelectorAll('.sr-input').forEach((el, i) => {{
  el.value = Math.round(spendRates[i] * 100);
}});

// ─── 유틸 ───
function expMult(age) {{
  if (age < 65)  return spendRates[0];
  if (age < 70)  return spendRates[1];
  if (age < 75)  return spendRates[2];
  if (age < 80)  return spendRates[3];
  if (age < 85)  return spendRates[4];
  return spendRates[5];
}}
function medicalMult(age) {{
  if (age < 65)  return 1.0;
  if (age < 70)  return 1.3;
  if (age < 75)  return 1.7;
  if (age < 80)  return 2.2;
  if (age < 85)  return 2.8;
  return 3.5;
}}
function fmt(v) {{ return Math.round(v).toLocaleString() + '만'; }}
function fmtSign(v) {{ return (v >= 0 ? '+' : '') + Math.round(v).toLocaleString() + '만'; }}

// ─── 데이터 계산 ───
function computeData() {{
  const ages = RAW.ages;
  const income = RAW.income;
  const contribItems = RAW.contrib_items;
  const tax = RAW.tax;
  const hi  = RAW.health_ins;
  const baseExp = RAW.base_expense_man;

  const salaryMan    = RAW.salary_man || 0;
  const retDepSet    = new Set(RAW.ret_dep_pensions || []);
  const infLinked    = RAW.inf_linked_pensions || {{}};
  const rawDebt      = RAW.debt_man      || 0;
  const rawRent      = RAW.rent_man      || 0;
  const livingBase   = RAW.living_man    || 0;   // 기본 생활비
  const medicalBase  = RAW.medical_man   || 0;   // 의료비 (증가)
  const leisureBase  = RAW.leisure_man   || 0;   // 여가/취미
  const familyBase   = RAW.family_man    || 0;   // 자녀/부모 지원
  const insBase      = RAW.insurance_man || 0;   // 보험료
  const otherBase    = RAW.other_man     || 0;   // 기타
  const residualBase = baseExp - rawDebt - rawRent;  // 회원권·차량비 (체감률 적용)

  return ages.map(age => {{
    const aNum = +age;
    const srcMap = {{}};
    const srcRaw = income[age] || {{}};
    for (const [k, v] of Object.entries(srcRaw)) {{
      if (k === '근로소득') {{
        srcMap[k] = aNum >= retireAge ? 0 : salaryMan;
      }} else if (retDepSet.has(k) && aNum < retireAge) {{
        srcMap[k] = 0;
      }} else if (infLinked[k]) {{
        const {{start_age, base_man}} = infLinked[k];
        srcMap[k] = base_man * Math.pow(1 + inflRate / 100, Math.max(0, aNum - start_age));
      }} else {{
        srcMap[k] = v || 0;
      }}
    }}
    if (salaryMan > 0 && !('근로소득' in srcRaw)) {{
      srcMap['근로소득'] = aNum >= retireAge ? 0 : salaryMan;
    }}
    const stackTotal  = Object.values(srcMap).reduce((a, b) => a + b, 0);
    const totalIncome = Object.entries(srcMap)
      .filter(([k]) => !hiddenKeys.has(k))
      .reduce((a, [, v]) => a + v, 0);

    const contribMap = {{}};
    for (const ci of contribItems) {{
      if (aNum < ci.until_age) {{
        const isEmpCut = ci.is_employment && aNum >= retireAge;
        contribMap[ci.label] = isEmpCut ? 0 : (ci.amount_man || 0);
      }}
    }}

    const taxVal = -(tax[age] || 0);
    const hiVal  = -(hi[age] || 0);

    const yrs      = Math.max(0, aNum - (RAW.ages[0] || retireAge));
    const infMult  = Math.pow(1 + inflRate / 100, yrs);
    const ageMult  = expMult(aNum);

    const rentInfYrs = Math.max(0, aNum - (RAW.ages[0] || retireAge));
    const rentExp  = rawRent * Math.pow(1 + inflRate / 100, rentInfYrs); // 현시점부터 물가 반영
    const visDebt  = hiddenKeys.has('대출상환금') ? 0 : rawDebt;
    const visRent  = hiddenKeys.has('임차료')     ? 0 : rentExp;
    const fixedExp = rawDebt + rentExp;

    const livingExp   = livingBase   * infMult * ageMult;
    const medicalExp  = medicalBase  * infMult * medicalMult(aNum);
    const leisureExp  = leisureBase  * infMult * ageMult;
    const familyExp   = familyBase   * infMult * ageMult;
    const insExp      = insBase      * infMult * ageMult;
    const otherExp    = otherBase    * infMult * ageMult;
    const residualExp = residualBase * infMult * ageMult;  // 회원권·차량비

    const visTax  = hiddenKeys.has('소득세')      ? 0 : Math.abs(taxVal);
    const visHI   = hiddenKeys.has('건보료')      ? 0 : Math.abs(hiVal);
    const visMed  = hiddenKeys.has('의료비')      ? 0 : medicalExp;
    const visLiv  = hiddenKeys.has('생활비')      ? 0 : livingExp;
    const visLei  = hiddenKeys.has('여가/취미')   ? 0 : leisureExp;
    const visFam  = hiddenKeys.has('자녀/부모지원') ? 0 : familyExp;
    const visIns  = hiddenKeys.has('보험료')      ? 0 : insExp;
    const visOth  = hiddenKeys.has('기타')        ? 0 : otherExp;

    const expense = residualExp + visLiv + visMed + visLei + visFam + visIns + visOth
                  + visDebt + visRent + visTax + visHI;

    return {{
      age: aNum,
      srcMap, stackTotal, totalIncome,
      contribMap, taxVal, hiVal,
      livingExp, medicalExp, leisureExp, familyExp, insExp, otherExp, residualExp,
      fixedExp,
      visDebt, visRent, rentExp,
      expense,
      surplus: totalIncome - expense,
    }};
  }});
}}

// ─── SVG 설정 ───
const margin = {{ top: 24, right: 20, bottom: 16, left: 30 }};
function getWidth() {{
  return document.getElementById('chart-container').clientWidth - 40;
}}
{_get_height_js}

const svg = d3.select('#main-svg');
let g;

function initSvg() {{
  const W = getWidth();
  const H = getHeight();
  const totalH = H + margin.top + margin.bottom;
  svg.attr('viewBox', `0 0 ${{W}} ${{totalH}}`)
     .attr('height', totalH);
  svg.selectAll('*').remove();
  g = svg.append('g').attr('transform', `translate(${{margin.left}},${{margin.top}})`);
}}

// ─── 메인 그리기 ───
function draw() {{
  initSvg();
  const data = computeData();
  const W = getWidth() - margin.left - margin.right;
  const H = getHeight();

  // 호버 배경 (z-order 맨 아래 — 합계만 표시, 세부항목 없음)
  g.append('rect').attr('class', 'hover-overlay')
    .attr('width', W).attr('height', H)
    .attr('fill', 'transparent')
    .on('mousemove', function(event) {{ showTooltip(event, data, xScale); }})
    .on('mouseleave', hideTooltip);

  const ages = data.map(d => d.age);
  const srcKeys = RAW.income_sources;  // 항상 전체 키 (위치 변동 방지)
  const allContribKeys = [...new Set(RAW.contrib_items.map(c => c.label))];
  const colorMap = {{}};
  RAW.income_sources.forEach(k => {{ colorMap[k] = RAW.colors[k] || '#888'; }});
  colorMap['소득세']      = RAW.colors['소득세'] || '#cda0d8';
  colorMap['건보료']      = RAW.colors['건보료'] || '#86d0d8';
  colorMap['의료비']      = '#ef9a9a';
  colorMap['생활비']      = '#ef5350';
  colorMap['여가/취미']   = '#66bb6a';
  colorMap['자녀/부모지원'] = '#26c6da';
  colorMap['보험료']      = '#ffa726';
  colorMap['기타']        = '#b0bec5';
  allContribKeys.forEach(k => {{
    const base = k.replace('(납입)', '');
    colorMap[k] = RAW.colors[base] || '#aaa';
  }});
  colorMap['대출상환금'] = '#ff7043';
  colorMap['임차료']     = '#ab47bc';

  const xScale = d3.scaleLinear()
    .domain([d3.min(ages), d3.max(ages)])
    .range([0, W]);

  // y축 범위: 수입(양수) ↑ / 잉여부족·지출(음수) ↓
  let yMax = 0, yMin = 0;
  data.forEach(d => {{
    yMax = Math.max(yMax, d.stackTotal);
    // 가시 고정밴드 + 가시 기여금/세금/건보료 깊이
    const visDebtD = hiddenKeys.has('대출상환금') ? 0 : (RAW.debt_man || 0);
    const visCtbD  = allContribKeys.reduce((s, k) => hiddenKeys.has(k) ? s : s + Math.abs(d.contribMap[k] || 0), 0)
                   + (hiddenKeys.has('임차료')      ? 0 : d.rentExp)
                   + (hiddenKeys.has('소득세')      ? 0 : Math.abs(d.taxVal))
                   + (hiddenKeys.has('건보료')      ? 0 : Math.abs(d.hiVal))
                   + (hiddenKeys.has('의료비')      ? 0 : d.medicalExp)
                   + (hiddenKeys.has('생활비')      ? 0 : d.livingExp)
                   + (hiddenKeys.has('여가/취미')   ? 0 : d.leisureExp)
                   + (hiddenKeys.has('자녀/부모지원') ? 0 : d.familyExp)
                   + (hiddenKeys.has('보험료')      ? 0 : d.insExp)
                   + (hiddenKeys.has('기타')        ? 0 : d.otherExp);
    yMin = Math.min(yMin, -(visDebtD + visCtbD), d.surplus);
  }});
  yMax = yMax * 1.15 || 100;
  yMin = yMin * 1.2 || -50;

  const yScale = d3.scaleLinear().domain([yMin, yMax]).range([H, 0]);

  // 그리드
  g.selectAll('.grid').remove();
  g.append('g').attr('class', 'grid')
    .call(d3.axisLeft(yScale).ticks(6).tickSize(-W).tickFormat(''))
    .select('.domain').remove();

  // 축
  g.selectAll('.x-axis,.y-axis,.axis-label').remove();
  const tickAges = ages.filter(a => a % 5 === 0);
  g.append('g').attr('class', 'axis x-axis')
    .attr('transform', `translate(0,${{H}})`)
    .call(d3.axisBottom(xScale).tickValues(tickAges).tickSize(0).tickFormat(''))
    .select('.domain').attr('stroke', 'transparent');
  g.append('g').attr('class', 'axis y-axis')
    .call(d3.axisLeft(yScale).ticks(6).tickFormat(d => d + '만'));
  g.append('text').attr('class', 'axis-label')
    .attr('transform', 'rotate(-90)')
    .attr('y', -22).attr('x', -H / 2)
    .attr('text-anchor', 'middle').text('월 금액 (만원)');

  // 0선 + 나이 레이블
  g.selectAll('.zero-line,.zero-age-label').remove();
  g.append('line').attr('class', 'zero-line')
    .attr('x1', 0).attr('x2', W)
    .attr('y1', yScale(0)).attr('y2', yScale(0));
  const zeroY = yScale(0);
  tickAges.forEach(a => {{
    g.append('text').attr('class', 'zero-age-label')
      .attr('x', xScale(a))
      .attr('y', zeroY - 3)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', 'var(--axis-text)')
      .attr('opacity', 1.0)
      .attr('font-weight', '700')
      .text(a + '세');
  }});

  // ── 수입 세부항목 — 스택 채우기 영역 + 얇은 경계선 (상세보기 시만) ──
  g.selectAll('.source-line,.income-areas').remove();
  if (showDetail) {{
    const incAreaG = g.append('g').attr('class', 'income-areas');
    const stackData = data.map(d => {{
      const row = {{ age: d.age }};
      srcKeys.forEach(k => {{ row[k] = d.srcMap[k] || 0; }});
      return row;
    }});
    const stack = d3.stack().keys(srcKeys).order(d3.stackOrderNone).offset(d3.stackOffsetNone);
    const stacked = stack(stackData);
    const areaGen = d3.area()
      .x(d => xScale(d.data.age))
      .y0(d => yScale(d[0]))
      .y1(d => yScale(d[1]))
      .curve(d3.curveCatmullRom.alpha(0.5));
    const lineGenArea = d3.line()
      .x(d => xScale(d.data.age))
      .y(d => yScale(d[1]))
      .curve(d3.curveCatmullRom.alpha(0.5));
    stacked.forEach(layer => {{
      const isHidden = hiddenKeys.has(layer.key);
      const col = colorMap[layer.key] || '#aaa';
      const _ikey = layer.key;
      incAreaG.append('path')
        .datum(layer)
        .attr('fill', col)
        .attr('opacity', isHidden ? 0.02 : 0.18)
        .attr('d', areaGen)
        .on('mousemove', function(event) {{ showTooltip(event, data, xScale, _ikey); }})
        .on('mouseleave', hideTooltip);
      incAreaG.append('path')
        .datum(layer)
        .attr('class', 'source-line')
        .attr('stroke', col)
        .attr('opacity', isHidden ? 0.06 : 0.9)
        .attr('d', lineGenArea)
        .on('mousemove', function(event) {{ showTooltip(event, data, xScale, _ikey); }})
        .on('mouseleave', hideTooltip);
    }});
  }}

  // ── 지출 세부항목 — 음수 방향 스택 채우기 + 얇은 경계선 (상세보기 시만) ──
  g.selectAll('.ctb-neg-line,.contrib-areas,.fixed-band').remove();
  if (!showDetail) {{
    // 간략보기: 세부 채우기/선 없이 합계선만 사용
  }} else {{

  // 대출상환금: 독립 고정 밴드 (0 바로 아래, 계약금액이므로 물가 미반영)
  const rawDebtV = RAW.debt_man || 0;
  const debtV = hiddenKeys.has('대출상환금') ? 0 : rawDebtV;
  const rentBottom = -(debtV);   // 임차료는 ctbStack으로 이동

  if (rawDebtV > 0) {{
    const dy0 = yScale(0);
    const dy1 = yScale(-(rawDebtV));
    const isDebtHidden = hiddenKeys.has('대출상환금');
    g.append('rect').attr('class', 'fixed-band')
      .attr('x', 0).attr('y', dy0)
      .attr('width', W).attr('height', isDebtHidden ? 0 : dy1 - dy0)
      .attr('fill', '#ff7043').attr('opacity', isDebtHidden ? 0 : 0.10)
      .on('mousemove', function(event) {{ showTooltip(event, data, xScale, '대출상환금'); }})
      .on('mouseleave', hideTooltip);
    if (!isDebtHidden) {{
      g.append('line').attr('class', 'ctb-neg-line')
        .attr('x1', 0).attr('x2', W)
        .attr('y1', dy1).attr('y2', dy1)
        .attr('stroke', '#ff7043').attr('stroke-width', 1)
        .attr('stroke-dasharray', '4,3').attr('stroke-opacity', 0.85);
    }}
  }}

  // 기여금·세금·건보료: d3.stack (대출/임차료 아래부터 시작)
  // 세부 지출 스택: 납입·세금·건보료 → 의료비 → 나머지 생활지출
  const ctbStackKeys = ['임차료', ...allContribKeys, '소득세', '건보료', '의료비', '기타', '보험료', '자녀/부모지원', '여가/취미', '생활비'];
  const ctbBaseVal   = rentBottom;   // 대출상환금 하단에서 스택 시작
  const ctbStackData = data.map(d => {{
    const row = {{ age: d.age }};
    row['임차료'] = hiddenKeys.has('임차료') ? 0 : -d.rentExp;  // 물가상승 반영
    allContribKeys.forEach(k => {{ row[k] = d.contribMap[k] || 0; }});
    row['소득세']       = d.taxVal;
    row['건보료']       = d.hiVal;
    row['의료비']       = hiddenKeys.has('의료비')      ? 0 : -d.medicalExp;
    row['기타']         = hiddenKeys.has('기타')        ? 0 : -d.otherExp;
    row['보험료']       = hiddenKeys.has('보험료')      ? 0 : -d.insExp;
    row['자녀/부모지원'] = hiddenKeys.has('자녀/부모지원') ? 0 : -d.familyExp;
    row['여가/취미']    = hiddenKeys.has('여가/취미')   ? 0 : -d.leisureExp;
    row['생활비']       = hiddenKeys.has('생활비')      ? 0 : -d.livingExp;
    return row;
  }});

  // 기준선 오프셋: 모든 값에 ctbBaseVal을 더해 스택 시작위치를 고정밴드 하단으로 이동
  const ctbStackDataShifted = ctbStackData.map(row => {{
    const shifted = {{ age: row.age }};
    ctbStackKeys.forEach(k => {{ shifted[k] = (row[k] || 0); }});
    return shifted;
  }});

  if (ctbStackKeys.length > 0) {{
    // 커스텀 오프셋: ctbBaseVal 위치부터 음수 방향으로 쌓기
    const ctbStack = d3.stack()
      .keys(ctbStackKeys)
      .order(d3.stackOrderNone)
      .offset(function(series, order) {{
        // 먼저 stackOffsetNone 적용
        d3.stackOffsetNone(series, order);
        // 그 후 전체를 ctbBaseVal만큼 이동
        series.forEach(function(s) {{
          s.forEach(function(d) {{
            d[0] += ctbBaseVal;
            d[1] += ctbBaseVal;
          }});
        }});
      }});
    const ctbStacked = ctbStack(ctbStackDataShifted);

    const ctbAreaGen = d3.area()
      .x(d => xScale(d.data.age))
      .y0(d => yScale(d[0]))
      .y1(d => yScale(d[1]))
      .curve(d3.curveCatmullRom.alpha(0.5));
    const ctbLineGen = d3.line()
      .x(d => xScale(d.data.age))
      .y(d => yScale(d[1]))
      .curve(d3.curveCatmullRom.alpha(0.5));

    ctbStacked.forEach(layer => {{
      const col = colorMap[layer.key] || '#aaa';
      const hasVal = layer.some(pt => Math.abs(pt[1] - pt[0]) > 0.01);
      if (!hasVal) return;
      const isHidden = hiddenKeys.has(layer.key);
      const _ckey = layer.key;
      g.append('path')
        .datum(layer)
        .attr('class', 'contrib-areas')
        .attr('fill', col)
        .attr('opacity', isHidden ? 0.02 : 0.15)
        .attr('d', ctbAreaGen)
        .on('mousemove', function(event) {{ showTooltip(event, data, xScale, _ckey); }})
        .on('mouseleave', hideTooltip);
      if (!isHidden) {{
        g.append('path')
          .datum(layer)
          .attr('class', 'ctb-neg-line')
          .attr('stroke', col)
          .attr('d', ctbLineGen)
          .on('mousemove', function(event) {{ showTooltip(event, data, xScale, _ckey); }})
          .on('mouseleave', hideTooltip);
      }}
    }});
  }}
  }} // end showDetail (지출 세부)

  // ── 수입 합계선 — 중간 (2.5px) ──
  g.selectAll('.income-total-line,.income-dot').remove();
  const totalLine = d3.line()
    .x(d => xScale(d.age))
    .y(d => yScale(d.totalIncome))
    .curve(d3.curveCatmullRom.alpha(0.5));
  g.append('path').attr('class', 'income-total-line')
    .datum(data).attr('d', totalLine);

  // ── 지출 합계선 — 양수 점선만 (거울) ──
  g.selectAll('.expense-line,.expense-neg-line,.expense-mirror-line').remove();
  const expLineGen = d3.line()
    .x(d => xScale(d.age))
    .y(d => yScale(d.expense))
    .curve(d3.curveCatmullRom.alpha(0.5));
  g.append('path').attr('class', 'expense-mirror-line')
    .datum(data).attr('d', expLineGen);

  // ── 잉여/부족 굵은선 (3.5px) ──
  g.selectAll('.surplus-zone,.deficit-zone,.surplus-line').remove();
  const surplusLineGen = d3.line()
    .x(d => xScale(d.age))
    .y(d => yScale(d.surplus))
    .curve(d3.curveCatmullRom.alpha(0.5));
  g.append('path').attr('class', 'surplus-line')
    .datum(data).attr('d', surplusLineGen)
    .on('mousemove', function(event) {{ showTooltip(event, data, xScale); }})
    .on('mouseleave', hideTooltip);

  // 은퇴선 (드래그)
  g.selectAll('.retire-line,.retire-handle,.retire-label').remove();
  const rx = xScale(retireAge);
  g.append('line').attr('class', 'retire-line')
    .attr('x1', rx).attr('x2', rx)
    .attr('y1', 0).attr('y2', H);
  g.append('rect').attr('class', 'retire-handle')
    .attr('x', rx - 6).attr('y', 10)
    .attr('width', 12).attr('height', 24)
    .attr('rx', 4)
    .call(d3.drag()
      .on('drag', function(event) {{
        const clampedX = Math.max(0, Math.min(W, event.x));
        const newAge = Math.max(RAW.min_age ?? 50, Math.min(RAW.max_age ?? 95, Math.round(xScale.invert(clampedX))));
        if (newAge !== retireAge) {{
          retireAge = newAge;
          document.getElementById('retireSlider').value = retireAge;
          document.getElementById('retireVal').textContent = retireAge;
          scheduleDraw();
        }}
      }})
    );
  g.append('text').attr('class', 'retire-label')
    .attr('x', rx + 7).attr('y', 22)
    .text('은퇴 ' + retireAge + '세');

  updateStatusBar(data);
}}

// ─── 툴팁 ───
const tooltip = document.getElementById('tooltip');
let _ttShowAll  = false;   // 전체보기 토글 상태
let _ttLast     = null;    // 마지막 showTooltip 호출 인자
let _ttHideTimer = null;   // 지연 숨김 타이머

// 마우스가 툴팁 위로 이동하면 숨김 취소
tooltip.addEventListener('mouseenter', () => {{
  if (_ttHideTimer) {{ clearTimeout(_ttHideTimer); _ttHideTimer = null; }}
}});
tooltip.addEventListener('mouseleave', () => {{ tooltip.style.display = 'none'; }});

function showTooltip(event, data, xScale, hoverKey) {{
  if (_ttHideTimer) {{ clearTimeout(_ttHideTimer); _ttHideTimer = null; }}
  _ttLast = {{event, data, xScale, hoverKey}};
  _renderTooltip(event, data, xScale, hoverKey);
}}

function _renderTooltip(event, data, xScale, hoverKey) {{
  const [mx] = d3.pointer(event, g.node());
  const age = Math.round(xScale.invert(mx));
  const d = data.find(r => r.age === age);
  if (!d) return;

  const incomeKeys = new Set(RAW.income_sources);
  const isIncKey = hoverKey && incomeKeys.has(hoverKey);
  const isExpKey = hoverKey && !isIncKey;

  let html = `<div class="tt-age">${{age}}세</div>`;
  html += `<div class="tt-div"></div>`;

  if (_ttShowAll) {{
    // ── 전체보기: 모든 수입 항목
    const incEntries = Object.entries(d.srcMap).filter(([k, v]) => v > 0);
    incEntries.forEach(([k, v]) => {{
      html += `<div class="tt-row"><span class="tt-key">${{k}}</span><span class="tt-val">${{fmt(v)}}</span></div>`;
    }});
  }} else if (isIncKey) {{
    // ── 항목별: 호버된 수입 항목만
    const v = d.srcMap[hoverKey] || 0;
    if (v > 0) html += `<div class="tt-row"><span class="tt-key">${{hoverKey}}</span><span class="tt-val">${{fmt(v)}}</span></div>`;
  }}
  html += `<div class="tt-row"><span class="tt-key" style="font-weight:700">수입 합계</span><span class="tt-val" style="color:var(--tt-age)">${{fmt(d.totalIncome)}}</span></div>`;

  html += `<div class="tt-div"></div>`;
  if (_ttShowAll) {{
    // ── 전체보기: 모든 지출 항목
    if (!hiddenKeys.has('생활비')        && d.livingExp  > 0) html += `<div class="tt-row"><span class="tt-key">생활비</span><span class="tt-val tt-neg">${{fmt(d.livingExp)}}</span></div>`;
    if (!hiddenKeys.has('의료비')        && d.medicalExp > 0) html += `<div class="tt-row"><span class="tt-key">의료비 (×${{medicalMult(age).toFixed(1)}})</span><span class="tt-val tt-neg">${{fmt(d.medicalExp)}}</span></div>`;
    if (!hiddenKeys.has('여가/취미')     && d.leisureExp > 0) html += `<div class="tt-row"><span class="tt-key">여가/취미</span><span class="tt-val tt-neg">${{fmt(d.leisureExp)}}</span></div>`;
    if (!hiddenKeys.has('자녀/부모지원') && d.familyExp  > 0) html += `<div class="tt-row"><span class="tt-key">자녀/부모 지원</span><span class="tt-val tt-neg">${{fmt(d.familyExp)}}</span></div>`;
    if (!hiddenKeys.has('보험료')        && d.insExp     > 0) html += `<div class="tt-row"><span class="tt-key">보험료</span><span class="tt-val tt-neg">${{fmt(d.insExp)}}</span></div>`;
    if (!hiddenKeys.has('기타')          && d.otherExp   > 0) html += `<div class="tt-row"><span class="tt-key">기타</span><span class="tt-val tt-neg">${{fmt(d.otherExp)}}</span></div>`;
    if (RAW.debt_man > 0 && !hiddenKeys.has('대출상환금'))    html += `<div class="tt-row"><span class="tt-key">대출 월상환금</span><span class="tt-val tt-neg">${{fmt(RAW.debt_man)}}</span></div>`;
    if (RAW.rent_man > 0 && !hiddenKeys.has('임차료'))        html += `<div class="tt-row"><span class="tt-key">월세 임차료</span><span class="tt-val tt-neg">${{fmt(d.rentExp)}}</span></div>`;
    const contribs = Object.entries(d.contribMap).filter(([k, v]) => v !== 0 && !hiddenKeys.has(k));
    if (d.taxVal && !hiddenKeys.has('소득세')) html += `<div class="tt-row"><span class="tt-key">소득세</span><span class="tt-val tt-neg">${{fmt(Math.abs(d.taxVal))}}</span></div>`;
    if (d.hiVal  && !hiddenKeys.has('건보료')) html += `<div class="tt-row"><span class="tt-key">건보료</span><span class="tt-val tt-neg">${{fmt(Math.abs(d.hiVal))}}</span></div>`;
    contribs.forEach(([k, v]) => {{
      html += `<div class="tt-row"><span class="tt-key">${{k}}</span><span class="tt-val tt-neg">${{fmt(Math.abs(v))}}</span></div>`;
    }});
  }} else if (isExpKey) {{
    // ── 항목별: 호버된 지출 항목만
    switch (hoverKey) {{
      case '생활비':        if (d.livingExp  > 0) html += `<div class="tt-row"><span class="tt-key">생활비</span><span class="tt-val tt-neg">${{fmt(d.livingExp)}}</span></div>`; break;
      case '의료비':        if (d.medicalExp > 0) html += `<div class="tt-row"><span class="tt-key">의료비 (×${{medicalMult(age).toFixed(1)}})</span><span class="tt-val tt-neg">${{fmt(d.medicalExp)}}</span></div>`; break;
      case '여가/취미':     if (d.leisureExp > 0) html += `<div class="tt-row"><span class="tt-key">여가/취미</span><span class="tt-val tt-neg">${{fmt(d.leisureExp)}}</span></div>`; break;
      case '자녀/부모지원': if (d.familyExp  > 0) html += `<div class="tt-row"><span class="tt-key">자녀/부모 지원</span><span class="tt-val tt-neg">${{fmt(d.familyExp)}}</span></div>`; break;
      case '보험료':        if (d.insExp     > 0) html += `<div class="tt-row"><span class="tt-key">보험료</span><span class="tt-val tt-neg">${{fmt(d.insExp)}}</span></div>`; break;
      case '기타':          if (d.otherExp   > 0) html += `<div class="tt-row"><span class="tt-key">기타</span><span class="tt-val tt-neg">${{fmt(d.otherExp)}}</span></div>`; break;
      case '대출상환금':    if (RAW.debt_man > 0) html += `<div class="tt-row"><span class="tt-key">대출 월상환금</span><span class="tt-val tt-neg">${{fmt(RAW.debt_man)}}</span></div>`; break;
      case '임차료':        if (d.rentExp    > 0) html += `<div class="tt-row"><span class="tt-key">월세 임차료</span><span class="tt-val tt-neg">${{fmt(d.rentExp)}}</span></div>`; break;
      case '소득세':        if (d.taxVal)         html += `<div class="tt-row"><span class="tt-key">소득세</span><span class="tt-val tt-neg">${{fmt(Math.abs(d.taxVal))}}</span></div>`; break;
      case '건보료':        if (d.hiVal)          html += `<div class="tt-row"><span class="tt-key">건보료</span><span class="tt-val tt-neg">${{fmt(Math.abs(d.hiVal))}}</span></div>`; break;
      default: {{
        const cv = d.contribMap[hoverKey];
        if (cv) html += `<div class="tt-row"><span class="tt-key">${{hoverKey}}</span><span class="tt-val tt-neg">${{fmt(Math.abs(cv))}}</span></div>`;
      }}
    }}
  }}
  html += `<div class="tt-row"><span class="tt-key" style="font-weight:700">지출 합계</span><span class="tt-val tt-neg">${{fmt(d.expense)}}</span></div>`;
  html += `<div class="tt-row"><span class="tt-key">잉여/부족</span><span class="tt-val ${{d.surplus >= 0 ? 'tt-pos' : 'tt-neg'}}">${{fmtSign(d.surplus)}}</span></div>`;

  // 토글 버튼
  html += `<button class="tt-toggle" onclick="toggleTTAll()">${{_ttShowAll ? '📌 항목별 보기' : '📋 전체 보기'}}</button>`;

  tooltip.innerHTML = html;
  tooltip.style.display = 'block';
  tooltip.style.left = '-9999px';
  tooltip.style.top  = '-9999px';
  const ttW = tooltip.offsetWidth;
  const ttH = tooltip.offsetHeight;
  // 수평: 오른쪽 공간 부족하면 왼쪽으로 플립
  const spaceRight = window.innerWidth - event.clientX;
  if (spaceRight < ttW + 24) {{
    tooltip.style.left = Math.max(4, event.clientX - ttW - 12) + 'px';
  }} else {{
    tooltip.style.left = (event.clientX + 16) + 'px';
  }}
  // 수직: 아래로 삐져나오면 위로 플립
  let top = event.clientY - 10;
  if (top + ttH > window.innerHeight - 8) {{
    top = event.clientY - ttH - 10;
  }}
  tooltip.style.top = Math.max(4, top) + 'px';
}}

function toggleTTAll() {{
  _ttShowAll = !_ttShowAll;
  if (_ttLast) _renderTooltip(_ttLast.event, _ttLast.data, _ttLast.xScale, _ttLast.hoverKey);
}}

function hideTooltip() {{
  _ttHideTimer = setTimeout(() => {{ tooltip.style.display = 'none'; }}, 180);
}}

// ─── 상태바 ───
function updateStatusBar(data) {{
  const d = data.find(r => r.age === retireAge) || data[0];
  if (!d) return;
  document.getElementById('sb-retire').textContent = retireAge + '세';
  document.getElementById('sb-infl').textContent = inflRate.toFixed(1) + '%';
  document.getElementById('sb-income').textContent = fmt(d.totalIncome);
  document.getElementById('sb-expense').textContent = fmt(d.expense);
  const s = d.totalIncome - d.expense;
  const sb = document.getElementById('sb-surplus');
  sb.textContent = fmtSign(s);
  sb.style.color = s >= 0 ? 'var(--tt-pos)' : 'var(--tt-neg)';
}}

// ─── 범례 ───
function buildLegend() {{
  const legendEl = document.getElementById('legend');
  legendEl.innerHTML = '';

  // ── 합계선 고정 범례 (클릭 불가) ──
  const fixedLines = [
    {{ label: '잉여/부족', color: cssVar('--sur-line'), dashPx: [8,5], opacity: 1,    width: 2 }},
    {{ label: '수입 합계', color: cssVar('--inc-line'), dashPx: null,  opacity: 1,    width: 2 }},
    {{ label: '지출 합계', color: cssVar('--exp-line'), dashPx: [5,4], opacity: 0.45, width: 2 }},
  ];
  fixedLines.forEach(item => {{
    const div = document.createElement('div');
    div.className = 'legend-item';
    div.style.cursor = 'default';
    const sw = document.createElement('div');
    sw.style.flexShrink = '0';
    sw.style.alignSelf = 'center';
    sw.style.width = '24px';
    sw.style.height = item.width + 'px';
    sw.style.borderRadius = '1px';
    sw.style.opacity = item.opacity;
    if (item.dashPx) {{
      const [on, off] = item.dashPx;
      sw.style.background = `repeating-linear-gradient(to right,${{item.color}} 0,${{item.color}} ${{on}}px,transparent ${{on}}px,transparent ${{on+off}}px)`;
    }} else {{
      sw.style.background = item.color;
    }}
    div.appendChild(sw);
    const txt = document.createElement('span');
    txt.textContent = item.label;
    div.appendChild(txt);
    legendEl.appendChild(div);
  }});

  // 구분선 (상세보기에서만 표시)
  const sep = document.createElement('div');
  sep.className = 'leg-detail';
  sep.style.cssText = 'width:100%;border-top:1px solid var(--border);margin:2px 0 1px;flex-basis:100%;';
  legendEl.appendChild(sep);

  // ── 세부항목 (클릭 토글, 상세보기 전용) ──
  const _legFixed = [];
  if (RAW.debt_man > 0) _legFixed.push('대출상환금');
  if (RAW.rent_man > 0) _legFixed.push('임차료');
  const _contribLabels = [...new Set((RAW.contrib_items || []).map(c => c.label))];
  const colors = Object.assign({{}}, RAW.colors, {{
    '대출상환금': '#ff7043', '임차료': '#ab47bc',
    '의료비': '#ef9a9a', '생활비': '#ef5350',
    '여가/취미': '#66bb6a', '자녀/부모지원': '#26c6da',
    '보험료': '#ffa726', '기타': '#b0bec5',
  }});
  _contribLabels.forEach(k => {{
    if (!colors[k]) colors[k] = RAW.colors[k.replace('(납입)', '')] || '#aaa';
  }});

  function addLegendLabel(text) {{
    const lbl = document.createElement('div');
    lbl.className = 'leg-detail';
    lbl.style.cssText = 'width:100%;font-size:0.68rem;color:var(--text-muted);font-weight:600;padding:2px 0 1px;flex-basis:100%;';
    lbl.textContent = text;
    legendEl.appendChild(lbl);
  }}
  function addLegendItem(k) {{
    const div = document.createElement('div');
    div.className = 'legend-item leg-detail' + (hiddenKeys.has(k) ? ' hidden' : '');
    div.innerHTML = `<div class="legend-swatch" style="background:${{colors[k] || '#aaa'}}"></div>${{k}}`;
    div.addEventListener('click', () => {{
      if (hiddenKeys.has(k)) hiddenKeys.delete(k);
      else hiddenKeys.add(k);
      div.classList.toggle('hidden');
      draw();
    }});
    legendEl.appendChild(div);
  }}

  // 수입 세부항목
  addLegendLabel('▸ 수입');
  RAW.income_sources.forEach(k => addLegendItem(k));

  // 구분선 (상세보기에서만 표시)
  const sep2 = document.createElement('div');
  sep2.className = 'leg-detail';
  sep2.style.cssText = 'width:100%;border-top:1px solid var(--border);margin:2px 0 1px;flex-basis:100%;';
  legendEl.appendChild(sep2);

  // 지출 세부항목
  addLegendLabel('▸ 지출');
  const _expItems = [
    ...(RAW.living_man    > 0 ? ['생활비']       : []),
    ...(RAW.medical_man   > 0 ? ['의료비']       : []),
    ...(RAW.leisure_man   > 0 ? ['여가/취미']    : []),
    ...(RAW.family_man    > 0 ? ['자녀/부모지원'] : []),
    ...(RAW.insurance_man > 0 ? ['보험료']       : []),
    ...(RAW.other_man     > 0 ? ['기타']         : []),
  ];
  ['소득세', '건보료', ..._expItems, ..._contribLabels, ..._legFixed].forEach(k => addLegendItem(k));
}}

// ─── 이벤트 리스너 (RAF 쓰로틀로 과도한 draw 방지) ───
let _rafPending = false;
function scheduleDraw() {{
  if (!_rafPending) {{
    _rafPending = true;
    requestAnimationFrame(function() {{
      _rafPending = false;
      draw();
    }});
  }}
}}
document.getElementById('retireSlider').addEventListener('input', function() {{
  retireAge = +this.value;
  document.getElementById('retireVal').textContent = retireAge;
  scheduleDraw();
}});
document.getElementById('inflSlider').addEventListener('input', function() {{
  inflRate = +this.value;
  document.getElementById('inflVal').textContent = inflRate.toFixed(1);
  scheduleDraw();
}});
document.querySelectorAll('.sr-input').forEach((el, i) => {{
  el.addEventListener('change', function() {{
    spendRates[i] = Math.max(0.1, Math.min(1.5, +this.value / 100));
    scheduleDraw();
  }});
}});

// 시스템 다크/라이트 모드 변경 감지 → 재드로우
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {{
  draw();
}});

// 리사이즈 — window resize + ResizeObserver 병행으로 iframe 너비 변화 감지
let resizeTimer;
function _scheduleDraw() {{
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {{ draw(); }}, 150);
}}
window.addEventListener('resize', _scheduleDraw);
if (window.ResizeObserver) {{
  new ResizeObserver(_scheduleDraw).observe(document.getElementById('chart-container'));
}}

// ─── 초기화 ───
buildLegend();
function initAndDraw() {{
  if (getWidth() > 0) {{
    draw();  // draw() 내부에서 initSvg() 호출하므로 별도 호출 불필요
    requestAnimationFrame(function() {{
      if (typeof reportHeight === 'function') reportHeight();
    }});
  }} else {{
    requestAnimationFrame(initAndDraw);
  }}
}}
initAndDraw();
{_resize_report_js}
</script>
</body>
</html>"""
