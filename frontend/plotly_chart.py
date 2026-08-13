"""
Plotly 기반 은퇴 시나리오 차트
- 수입 세부항목: 누적합 + fill='tonexty' 로 D3 스택 채우기 재현
- hover: customdata로 실제(비누적) 값 표시
"""
import plotly.graph_objects as go

_INCOME_PALETTE = [
    '#5BA4CF', '#F0A500', '#E05C5C', '#3DB87A', '#8B6CE8',
    '#E0B84A', '#D06CB0', '#3CBDE0', '#B07840', '#70B870',
]

_EXPENSE_COLORS = {
    '생활비':   '#FF6680',
    '대출상환': '#FF7043',
    '임차료':   '#AB47BC',
    '소득세':   '#CE93D8',
    '건강보험': '#4DD0E1',
}

_SP = dict(shape='spline', smoothing=0.5)


def _hex_to_rgb(h: str) -> tuple:
    h = h.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return f'rgba({r},{g},{b},{alpha})'


def compute_data(data: dict, retire_age: int, infl_rate: float, spending_rates: list) -> list:
    income_raw    = data['income']
    contrib_items = data.get('contrib_items', [])
    tax           = data.get('tax', {})
    hi            = data.get('health_ins', {})
    base_exp      = data.get('base_expense_man', 0)
    salary_man    = data.get('salary_man', 0)
    ret_dep_set   = set(data.get('ret_dep_pensions', []))
    inf_linked    = data.get('inf_linked_pensions', {})
    debt_man      = data.get('debt_man', 0)
    rent_man      = data.get('rent_man', 0)
    living_base   = base_exp - debt_man - rent_man

    def sr(age):
        if age < 65: return spending_rates[0]
        if age < 70: return spending_rates[1]
        if age < 75: return spending_rates[2]
        if age < 80: return spending_rates[3]
        if age < 85: return spending_rates[4] if len(spending_rates) > 4 else spending_rates[-1]
        return spending_rates[5] if len(spending_rates) > 5 else spending_rates[-1]

    rows = []
    for age in data['ages']:
        src_raw = income_raw.get(age, {})
        src_map = {}
        for k, v in src_raw.items():
            if k == '근로소득':
                src_map[k] = 0 if age >= retire_age else salary_man
            elif k in ret_dep_set and age < retire_age:
                src_map[k] = 0
            elif k in inf_linked:
                info = inf_linked[k]
                src_map[k] = info['base_man'] * (1 + infl_rate / 100) ** max(0, age - info['start_age'])
            else:
                src_map[k] = v or 0
        if salary_man > 0 and '근로소득' not in src_raw:
            src_map['근로소득'] = 0 if age >= retire_age else salary_man

        total_income = sum(src_map.values())
        inf_mult     = (1 + infl_rate / 100) ** max(0, age - retire_age)
        living_exp   = living_base * inf_mult * sr(age)
        expense      = living_exp + debt_man + rent_man

        contrib_map = {}
        for ci in contrib_items:
            if age < ci.get('until_age', 999):
                is_emp_cut = ci.get('is_employment', False) and age >= retire_age
                contrib_map[ci['label']] = 0 if is_emp_cut else ci.get('amount_man', 0)

        rows.append({
            'age':          age,
            'src_map':      src_map,
            'total_income': round(total_income, 1),
            'expense':      round(expense, 1),
            'surplus':      round(total_income - expense, 1),
            'tax_val':      round(tax.get(age, 0), 1),
            'hi_val':       round(hi.get(age, 0), 1),
            'contrib_map':  contrib_map,
            'living_exp':   round(living_exp, 1),
            'debt_man':     round(debt_man, 1),
            'rent_man':     round(rent_man, 1),
        })
    return rows


def build_figure(data: dict, rows: list, retire_age: int, show_detail: bool = False) -> go.Figure:
    ages           = [r['age'] for r in rows]
    n              = len(ages)
    income_sources = data.get('income_sources', [])
    income_colors  = {
        src: _INCOME_PALETTE[i % len(_INCOME_PALETTE)]
        for i, src in enumerate(income_sources)
    }

    fig = go.Figure()

    if show_detail:
        # ── 수입 세부항목: 누적합 stacked area (tonexty) ──
        inc_cum = [0.0] * n
        first   = True
        for src in income_sources:
            vals = [r['src_map'].get(src, 0) for r in rows]
            if not any(v > 0 for v in vals):
                continue
            new_cum = [c + v for c, v in zip(inc_cum, vals)]
            clr = income_colors.get(src, '#aaa')
            # 값이 0인 포인트는 툴팁에서 제외
            ht = [f'{src}: %{{customdata:.0f}}만<extra></extra>' if v > 0.01
                  else '<extra></extra>' for v in vals]
            fig.add_trace(go.Scatter(
                x=ages, y=new_cum,
                name=src,
                customdata=vals,
                line=dict(color=clr, width=1, **_SP),
                fill='tozeroy' if first else 'tonexty',
                fillcolor=_rgba(clr, 0.18),
                hovertemplate=ht,
            ))
            inc_cum = new_cum
            first   = False

        # ── 지출 세부항목: 누적합 (음수 방향) stacked area ──
        exp_defs = [
            ('대출상환', [r['debt_man']   for r in rows], _EXPENSE_COLORS['대출상환']),
            ('임차료',   [r['rent_man']   for r in rows], _EXPENSE_COLORS['임차료']),
            ('생활비',   [r['living_exp'] for r in rows], _EXPENSE_COLORS['생활비']),
            ('소득세',   [r['tax_val']    for r in rows], _EXPENSE_COLORS['소득세']),
            ('건강보험', [r['hi_val']     for r in rows], _EXPENSE_COLORS['건강보험']),
        ]
        contrib_labels = list(rows[0]['contrib_map'].keys()) if rows else []
        for ci_label in contrib_labels:
            base_name = ci_label.replace('(납입)', '')
            clr = income_colors.get(base_name, '#8899AA')
            vals = [abs(r['contrib_map'].get(ci_label, 0)) for r in rows]
            exp_defs.append((ci_label, vals, clr))

        exp_cum = [0.0] * n
        first_e = True
        for label, base_vals, clr in exp_defs:
            if not any(v > 0 for v in base_vals):
                continue
            new_cum = [c - v for c, v in zip(exp_cum, base_vals)]
            # 값이 0인 포인트는 툴팁에서 제외
            ht = [f'{label}: %{{customdata:.0f}}만<extra></extra>' if v > 0.01
                  else '<extra></extra>' for v in base_vals]
            fig.add_trace(go.Scatter(
                x=ages, y=new_cum,
                name=label,
                customdata=base_vals,
                line=dict(color=clr, width=1, **_SP),
                fill='tozeroy' if first_e else 'tonexty',
                fillcolor=_rgba(clr, 0.15),
                hovertemplate=ht,
            ))
            exp_cum = new_cum
            first_e = False

    # ── 수입 합계: 2px 실선 ──
    fig.add_trace(go.Scatter(
        x=ages, y=[r['total_income'] for r in rows],
        name='수입 합계',
        line=dict(color='#00AAFF', width=2, **_SP),
        hovertemplate='수입합계: <b>%{y:.0f}만</b><extra></extra>',
    ))

    # ── 지출 합계: 점선 + 반투명 (참조선) ──
    fig.add_trace(go.Scatter(
        x=ages, y=[r['expense'] for r in rows],
        name='지출 합계',
        line=dict(color='#FF0077', width=1.5, dash='dash', **_SP),
        opacity=0.55,
        hovertemplate='지출합계: <b>%{y:.0f}만</b><extra></extra>',
    ))

    # ── 잉여/부족: 2px 점선 ──
    fig.add_trace(go.Scatter(
        x=ages, y=[r['surplus'] for r in rows],
        name='잉여/부족',
        line=dict(color='#7B2FFF', width=2, dash='dash', **_SP),
        hovertemplate='잉여/부족: <b>%{y:+.0f}만</b><extra></extra>',
    ))

    # ── 은퇴선 ──
    all_y = ([r['total_income'] for r in rows]
             + [r['surplus'] for r in rows]
             + ([exp_cum[i] for i in range(n)] if show_detail and rows else []))
    y_max = max(all_y) if all_y else 100
    y_min = min(all_y) if all_y else -50

    fig.add_shape(type='line',
        x0=retire_age, x1=retire_age,
        y0=y_min * 1.15, y1=y_max * 1.15,
        line=dict(color='#FF6600', width=1.5, dash='dash'),
    )
    fig.add_annotation(
        x=retire_age, y=y_max * 1.08,
        text=f'은퇴 {retire_age}세', showarrow=False,
        font=dict(color='#FF6600', size=11), xanchor='left',
    )

    fig.update_layout(
        height=420 if show_detail else 320,
        margin=dict(l=50, r=12, t=10, b=8),
        hovermode='x unified',
        yaxis=dict(
            ticksuffix='만', zeroline=True,
            zerolinecolor='rgba(160,160,190,0.5)', zerolinewidth=1,
            gridcolor='rgba(160,160,190,0.12)',
        ),
        xaxis=dict(ticksuffix='세', dtick=5, gridcolor='rgba(160,160,190,0.08)'),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.01, xanchor='right', x=1,
            font=dict(size=10), itemclick='toggle', itemdoubleclick='toggleothers',
            groupclick='toggleitem',
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="'Segoe UI','Apple SD Gothic Neo',sans-serif", size=11),
    )
    return fig
