"""
상세 인터랙티브 차트 HTML 생성기
D3.js v7 기반 standalone HTML 반환
"""
import json


def generate_detail_html(data: dict) -> str:
    """data dict → 완전한 standalone HTML string"""
    data_json = json.dumps(data, ensure_ascii=False, default=str)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>은퇴 시나리오 상세 분석</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  :root {{
    --bg:          #ffffff;
    --bg-panel:    #f4f6f8;
    --border:      #dde1e7;
    --text:        #1a1a2e;
    --text-muted:  #666;
    --h1-color:    #1565c0;
    --val-color:   #e65100;
    --input-bg:    #ffffff;
    --input-bdr:   #ccc;
    --grid-line:   #e8eaed;
    --axis-text:   #555;
    --zero-line:   #888;
    --tt-bg:       rgba(255,255,255,0.97);
    --tt-border:   #dde1e7;
    --tt-age:      #1565c0;
    --tt-key:      #777;
    --tt-pos:      #2e7d32;
    --tt-neg:      #c62828;
    --sb-bg:       #f4f6f8;
    --sb-border:   #dde1e7;
    --retire-clr:  #e65100;
    --inc-line:    #1565c0;
    --exp-line:    #c62828;
    --def-fill:    rgba(198,40,40,0.10);
    --dot-fill:    #1565c0;
    --dot-stroke:  #0d47a1;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg:          #0f1117;
      --bg-panel:    #161b22;
      --border:      #30363d;
      --text:        #e0e0e0;
      --text-muted:  #888;
      --h1-color:    #90caf9;
      --val-color:   #ff6f00;
      --input-bg:    #21262d;
      --input-bdr:   #30363d;
      --grid-line:   #2a2a3a;
      --axis-text:   #aaa;
      --zero-line:   #555;
      --tt-bg:       rgba(20,24,34,0.96);
      --tt-border:   #30363d;
      --tt-age:      #90caf9;
      --tt-key:      #aaa;
      --tt-pos:      #a5d6a7;
      --tt-neg:      #ef9a9a;
      --sb-bg:       #161b22;
      --sb-border:   #30363d;
      --retire-clr:  #ff6f00;
      --inc-line:    #5c9cdd;
      --exp-line:    #ef5350;
      --def-fill:    rgba(229,57,53,0.12);
      --dot-fill:    #5c9cdd;
      --dot-stroke:  #1565c0;
    }}
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', 'Apple SD Gothic Neo', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }}
  h1 {{
    font-size: 1.2rem;
    font-weight: 600;
    padding: 14px 20px 4px;
    color: var(--h1-color);
  }}
  .subtitle {{
    font-size: 0.78rem;
    color: var(--text-muted);
    padding: 0 20px 10px;
  }}

  /* ─── 컨트롤 패널 ─── */
  .controls {{
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    padding: 10px 20px 14px;
    background: var(--bg-panel);
    border-bottom: 1px solid var(--border);
  }}
  .ctrl-group {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 140px;
  }}
  .ctrl-group label {{
    font-size: 0.72rem;
    color: var(--text-muted);
    font-weight: 500;
  }}
  .ctrl-group input[type=range] {{
    width: 160px;
    accent-color: var(--retire-clr);
    cursor: pointer;
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
    padding: 10px 20px 0;
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

  .area-path {{ cursor: pointer; }}
  .income-total-line {{
    fill: none;
    stroke: var(--inc-line);
    stroke-width: 2.5px;
  }}
  .expense-line {{
    fill: none;
    stroke: var(--exp-line);
    stroke-width: 2px;
    stroke-dasharray: 8,4;
  }}
  .zero-line {{
    stroke: var(--zero-line);
    stroke-width: 2.5px;
  }}
  .retire-line {{
    stroke: var(--retire-clr);
    stroke-width: 2.5px;
    stroke-dasharray: 7,4;
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
  .deficit-zone {{
    fill: var(--def-fill);
    pointer-events: none;
  }}
  .income-dot {{
    fill: var(--dot-fill);
    stroke: var(--dot-stroke);
    stroke-width: 1px;
  }}

  /* ─── 범례 ─── */
  #legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px 14px;
    padding: 8px 20px 12px;
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
  .legend-swatch {{
    width: 12px;
    height: 12px;
    border-radius: 2px;
    flex-shrink: 0;
  }}

  /* ─── 툴팁 ─── */
  #tooltip {{
    position: fixed;
    pointer-events: none;
    background: var(--tt-bg);
    border: 1px solid var(--tt-border);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.78rem;
    line-height: 1.7;
    max-width: 260px;
    display: none;
    z-index: 999;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  }}
  #tooltip .tt-age {{
    font-weight: 700;
    color: var(--tt-age);
    margin-bottom: 4px;
    font-size: 0.85rem;
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

<h1>📊 은퇴 시나리오 — 상세 인터랙티브 분석</h1>
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
        <label>은퇴~64세</label>
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
        <label>80세+</label>
        <input type="number" class="sr-input" id="sr4" min="10" max="150" step="5" value="60">
      </div>
    </div>
  </div>
</div>

<div id="chart-container">
  <svg id="main-svg"></svg>
</div>
<div id="legend"></div>
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
  RAW.spending_rates['80plus'],
];
let hiddenKeys = new Set();

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
  return spendRates[4];
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

  return ages.map(age => {{
    const aNum = +age;
    const srcMap = {{}};   // 스택용: 항상 실제 값 (위치 고정)
    const srcRaw = income[age] || {{}};
    for (const [k, v] of Object.entries(srcRaw)) {{
      if (k === '근로소득') {{
        // 전 나이 범위에 월급여 고정, retireAge 이후 0
        srcMap[k] = aNum >= retireAge ? 0 : salaryMan;
      }} else if (retDepSet.has(k) && aNum < retireAge) {{
        // 은퇴연령 의존 연금: retireAge 이전 미개시
        srcMap[k] = 0;
      }} else if (infLinked[k]) {{
        // 물가 연동 연금(국민연금 등): 기준금액 × (1+inflRate/100)^(나이-개시나이)
        const {{start_age, base_man}} = infLinked[k];
        srcMap[k] = base_man * Math.pow(1 + inflRate / 100, Math.max(0, aNum - start_age));
      }} else {{
        srcMap[k] = v || 0;
      }}
    }}
    // 근로소득이 income[age]에 없는 나이(원래 은퇴 후)에도 표시
    if (salaryMan > 0 && !('근로소득' in srcRaw)) {{
      srcMap['근로소득'] = aNum >= retireAge ? 0 : salaryMan;
    }}
    // stackTotal: 스케일 고정용 (항상 전체)
    const stackTotal = Object.values(srcMap).reduce((a, b) => a + b, 0);
    // totalIncome: 파란 합계선 (hiddenKeys 제외)
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

    const yrs = Math.max(0, aNum - retireAge);
    const infMult  = Math.pow(1 + inflRate / 100, yrs);
    const ageMult  = expMult(aNum);
    const expense  = baseExp * infMult * ageMult;

    return {{
      age: aNum,
      srcMap, stackTotal, totalIncome,
      contribMap, taxVal, hiVal,
      expense,
      surplus: totalIncome - expense,
    }};
  }});
}}

// ─── SVG 설정 ───
const margin = {{ top: 30, right: 30, bottom: 60, left: 60 }};
function getWidth() {{
  return document.getElementById('chart-container').clientWidth - 40;
}}
function getHeight() {{ return 380; }}

const svg = d3.select('#main-svg');
let g;

function initSvg() {{
  const W = getWidth();
  const H = getHeight();
  svg.attr('viewBox', `0 0 ${{W}} ${{H + margin.top + margin.bottom}}`);
  svg.selectAll('*').remove();
  g = svg.append('g').attr('transform', `translate(${{margin.left}},${{margin.top}})`);
}}

// ─── 메인 그리기 ───
function draw() {{
  const data = computeData();
  const W = getWidth() - margin.left - margin.right;
  const H = getHeight();

  const ages = data.map(d => d.age);
  const srcKeys = RAW.income_sources;  // 항상 전체 키 (위치 변동 방지)
  const allContribKeys = [...new Set(RAW.contrib_items.map(c => c.label))];
  const colorMap = {{}};
  RAW.income_sources.forEach(k => {{ colorMap[k] = RAW.colors[k] || '#888'; }});
  colorMap['소득세'] = RAW.colors['소득세'] || '#cda0d8';
  colorMap['건보료'] = RAW.colors['건보료'] || '#86d0d8';
  allContribKeys.forEach(k => {{
    const base = k.replace('(납입)', '');
    colorMap[k] = RAW.colors[base] || '#aaa';
  }});

  const xScale = d3.scaleLinear()
    .domain([d3.min(ages), d3.max(ages)])
    .range([0, W]);

  let yMax = 0, yMin = 0;
  data.forEach(d => {{
    yMax = Math.max(yMax, d.stackTotal, d.expense);  // 스케일은 항상 전체 기준
    const contribSum = Object.values(d.contribMap).reduce((a, b) => a + b, 0)
                     + d.taxVal + d.hiVal;
    yMin = Math.min(yMin, contribSum);
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
    .call(d3.axisBottom(xScale).tickValues(tickAges).tickFormat(d => d + '세'));
  g.append('g').attr('class', 'axis y-axis')
    .call(d3.axisLeft(yScale).ticks(6).tickFormat(d => d + '만'));
  g.append('text').attr('class', 'axis-label')
    .attr('transform', 'rotate(-90)')
    .attr('y', -50).attr('x', -H / 2)
    .attr('text-anchor', 'middle').text('월 금액 (만원)');

  // 0선
  g.selectAll('.zero-line').remove();
  g.append('line').attr('class', 'zero-line')
    .attr('x1', 0).attr('x2', W)
    .attr('y1', yScale(0)).attr('y2', yScale(0));

  // 수입 스택 영역
  g.selectAll('.income-areas').remove();
  const incAreaG = g.append('g').attr('class', 'income-areas');

  const stackData = data.map(d => {{
    const row = {{ age: d.age }};
    srcKeys.forEach(k => {{ row[k] = d.srcMap[k] || 0; }});  // 항상 실제 값
    return row;
  }});
  const stack = d3.stack().keys(srcKeys).order(d3.stackOrderNone).offset(d3.stackOffsetNone);
  const stacked = stack(stackData);

  const areaGen = d3.area()
    .x(d => xScale(d.data.age))
    .y0(d => yScale(d[0]))
    .y1(d => yScale(d[1]))
    .curve(d3.curveCatmullRom.alpha(0.5));

  stacked.forEach(layer => {{
    const isHidden = hiddenKeys.has(layer.key);
    incAreaG.append('path')
      .datum(layer)
      .attr('class', 'area-path')
      .attr('fill', colorMap[layer.key] || '#aaa')
      .attr('opacity', isHidden ? 0.08 : 0.7)  // 숨김 = 투명, 위치는 유지
      .attr('d', areaGen)
      .on('mousemove', function(event) {{ showTooltip(event, data, xScale); }})
      .on('mouseleave', hideTooltip);
  }});

  // 납입/세금 영역
  g.selectAll('.contrib-areas').remove();
  const ctbAreaG = g.append('g').attr('class', 'contrib-areas');

  const ctbKeys = allContribKeys.concat(['소득세', '건보료']);
  const ctbStackData = data.map(d => {{
    const row = {{ age: d.age }};
    allContribKeys.forEach(k => {{ row[k] = d.contribMap[k] || 0; }});
    row['소득세'] = d.taxVal;
    row['건보료'] = d.hiVal;
    return row;
  }});

  const ctbStack = d3.stack().keys(ctbKeys).order(d3.stackOrderNone).offset(d3.stackOffsetNone);
  const ctbStacked = ctbStack(ctbStackData);

  const ctbAreaGen = d3.area()
    .x(d => xScale(d.data.age))
    .y0(d => yScale(Math.min(0, d[0])))
    .y1(d => yScale(Math.min(0, d[1])))
    .curve(d3.curveCatmullRom.alpha(0.5));

  ctbStacked.forEach(layer => {{
    ctbAreaG.append('path')
      .datum(layer)
      .attr('class', 'area-path')
      .attr('fill', colorMap[layer.key] || '#aaa')
      .attr('opacity', 0.6)
      .attr('d', ctbAreaGen);
  }});

  // 수입 합계선
  g.selectAll('.income-total-line,.income-dot').remove();
  const totalLine = d3.line()
    .x(d => xScale(d.age))
    .y(d => yScale(d.totalIncome))
    .curve(d3.curveCatmullRom.alpha(0.5));
  g.append('path').attr('class', 'income-total-line')
    .datum(data).attr('d', totalLine);
  g.selectAll('.income-dot').data(data).enter()
    .append('circle').attr('class', 'income-dot')
    .attr('r', 3)
    .attr('cx', d => xScale(d.age))
    .attr('cy', d => yScale(d.totalIncome));

  // 지출선
  g.selectAll('.expense-line').remove();
  const expLine = d3.line()
    .x(d => xScale(d.age))
    .y(d => yScale(d.expense))
    .curve(d3.curveCatmullRom.alpha(0.5));
  g.append('path').attr('class', 'expense-line')
    .datum(data).attr('d', expLine);

  // 적자 구간 하이라이트
  g.selectAll('.deficit-zone').remove();
  const defArea = d3.area()
    .x(d => xScale(d.age))
    .y0(d => yScale(Math.max(0, Math.min(d.totalIncome, d.expense))))
    .y1(d => d.expense > d.totalIncome ? yScale(d.totalIncome) : yScale(d.expense))
    .curve(d3.curveCatmullRom.alpha(0.5));
  if (data.some(d => d.expense > d.totalIncome)) {{
    g.append('path').attr('class', 'deficit-zone')
      .datum(data).attr('d', defArea);
  }}

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
          draw();
        }}
      }})
    );
  g.append('text').attr('class', 'retire-label')
    .attr('x', rx + 7).attr('y', 22)
    .text('은퇴 ' + retireAge + '세');

  // 호버 오버레이
  g.selectAll('.hover-overlay').remove();
  g.append('rect').attr('class', 'hover-overlay')
    .attr('width', W).attr('height', H)
    .attr('fill', 'transparent')
    .on('mousemove', function(event) {{ showTooltip(event, data, xScale); }})
    .on('mouseleave', hideTooltip);

  updateStatusBar(data);
}}

// ─── 툴팁 ───
const tooltip = document.getElementById('tooltip');
function showTooltip(event, data, xScale) {{
  const [mx] = d3.pointer(event, g.node());
  const age = Math.round(xScale.invert(mx));
  const d = data.find(r => r.age === age);
  if (!d) return;

  let html = `<div class="tt-age">${{age}}세</div>`;
  const incEntries = Object.entries(d.srcMap).filter(([k, v]) => v > 0);
  if (incEntries.length) {{
    html += `<div class="tt-div"></div>`;
    incEntries.forEach(([k, v]) => {{
      html += `<div class="tt-row"><span class="tt-key">${{k}}</span><span class="tt-val">${{fmt(v)}}</span></div>`;
    }});
    html += `<div class="tt-row"><span class="tt-key" style="font-weight:700">수입 합계</span><span class="tt-val" style="color:var(--tt-age)">${{fmt(d.totalIncome)}}</span></div>`;
  }}
  html += `<div class="tt-div"></div>`;
  html += `<div class="tt-row"><span class="tt-key">월 지출</span><span class="tt-val tt-neg">${{fmt(d.expense)}}</span></div>`;
  const surplus = d.totalIncome - d.expense;
  html += `<div class="tt-row"><span class="tt-key">잉여/부족</span><span class="tt-val ${{surplus >= 0 ? 'tt-pos' : 'tt-neg'}}">${{fmtSign(surplus)}}</span></div>`;

  const contribs = Object.entries(d.contribMap).filter(([k, v]) => v !== 0);
  if (contribs.length || d.taxVal || d.hiVal) {{
    html += `<div class="tt-div"></div>`;
    contribs.forEach(([k, v]) => {{
      html += `<div class="tt-row"><span class="tt-key">${{k}}</span><span class="tt-val tt-neg">${{fmt(v)}}</span></div>`;
    }});
    if (d.taxVal) html += `<div class="tt-row"><span class="tt-key">소득세</span><span class="tt-val tt-neg">${{fmt(d.taxVal)}}</span></div>`;
    if (d.hiVal)  html += `<div class="tt-row"><span class="tt-key">건보료</span><span class="tt-val tt-neg">${{fmt(d.hiVal)}}</span></div>`;
  }}

  tooltip.innerHTML = html;
  tooltip.style.display = 'block';
  tooltip.style.left = (event.clientX + 16) + 'px';
  tooltip.style.top  = (event.clientY - 10) + 'px';
}}
function hideTooltip() {{
  tooltip.style.display = 'none';
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
  const keys = [...RAW.income_sources, '소득세', '건보료'];
  const colors = Object.assign({{}}, RAW.colors);
  keys.forEach(k => {{
    const div = document.createElement('div');
    div.className = 'legend-item' + (hiddenKeys.has(k) ? ' hidden' : '');
    div.innerHTML = `<div class="legend-swatch" style="background:${{colors[k] || '#aaa'}}"></div>${{k}}`;
    div.addEventListener('click', () => {{
      if (hiddenKeys.has(k)) hiddenKeys.delete(k);
      else hiddenKeys.add(k);
      div.classList.toggle('hidden');
      draw();
    }});
    legendEl.appendChild(div);
  }});
}}

// ─── 이벤트 리스너 ───
document.getElementById('retireSlider').addEventListener('input', function() {{
  retireAge = +this.value;
  document.getElementById('retireVal').textContent = retireAge;
  draw();
}});
document.getElementById('inflSlider').addEventListener('input', function() {{
  inflRate = +this.value;
  document.getElementById('inflVal').textContent = inflRate.toFixed(1);
  draw();
}});
document.querySelectorAll('.sr-input').forEach((el, i) => {{
  el.addEventListener('change', function() {{
    spendRates[i] = Math.max(0.1, Math.min(1.5, +this.value / 100));
    draw();
  }});
}});

// 시스템 다크/라이트 모드 변경 감지 → 재드로우
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {{
  draw();
}});

// 리사이즈
let resizeTimer;
window.addEventListener('resize', () => {{
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {{ initSvg(); draw(); }}, 150);
}});

// ─── 초기화 ───
initSvg();
buildLegend();
draw();
</script>
</body>
</html>"""
