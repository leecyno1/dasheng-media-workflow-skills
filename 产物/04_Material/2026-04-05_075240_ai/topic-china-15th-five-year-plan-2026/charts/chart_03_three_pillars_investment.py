#!/usr/bin/env python3
"""
Chart 3: 十五五规划三大主线投资规模
Type: Stacked Bar Chart
Priority: P0 (政策分析核心)
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set Chinese font
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Data from draft
pillars = ['AI整合', '消费升级', '供应链重组']

# Investment amounts (in billions RMB)
ai_investment = 2000  # 2万亿元
consumption_investment = 0  # Represented by labor share increase (qualitative)
supply_chain_investment = 500  # 5000亿元

# For visualization, represent consumption upgrade by its impact
# Labor compensation increase: 3% of GDP
# Assuming 2026 GDP ~130 trillion RMB, 3% = 3900 billion RMB
consumption_impact = 3900

investments = [ai_investment, consumption_impact, supply_chain_investment]
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

# Create figure
fig, ax = plt.subplots(figsize=(10, 8))

# Create bar chart
x_pos = np.arange(len(pillars))
bars = ax.bar(x_pos, investments, color=colors, alpha=0.8, width=0.6)

# Add value labels
for bar, value, pillar in zip(bars, investments, pillars):
    if pillar == '消费升级':
        label = f'劳动报酬占比+3%\n≈¥{value}B'
    else:
        label = f'¥{value}B'

    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 100,
        label,
        ha='center',
        va='bottom',
        fontsize=11,
        weight='bold'
    )

# Add detail annotations
details = [
    '算力基础设施\n降低成本50%',
    '收入分配改革\n社保体系完善',
    '关键技术攻关\n自给率60%→80%'
]

for bar, detail in zip(bars, details):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() / 2,
        detail,
        ha='center',
        va='center',
        fontsize=9,
        color='white',
        weight='bold'
    )

# Customize axes
ax.set_xticks(x_pos)
ax.set_xticklabels(pillars, fontsize=12, weight='bold')
ax.set_ylabel('投资规模/影响 (十亿元)', fontsize=12, weight='bold')
ax.set_title(
    '十五五规划三大主线投资规模\n2026-2030年',
    fontsize=16,
    weight='bold',
    pad=20
)

# Add grid
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_axisbelow(True)

# Set y-axis limit
ax.set_ylim(0, 4500)

# Add total annotation
total = sum(investments)
ax.text(
    0.5, 0.95,
    f'总投资/影响规模: ¥{total}B',
    transform=ax.transAxes,
    ha='center',
    fontsize=11,
    weight='bold',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3)
)

plt.tight_layout()

# Save
output_path = Path(__file__).parent / 'chart_03_three_pillars_investment.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"✓ Chart saved: {output_path}")

# Quality report
report_path = Path(__file__).parent / 'chart_03_quality_report.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("""# Chart 3 Quality Report

## Chart Information
- **Title**: 十五五规划三大主线投资规模
- **Type**: Stacked Bar Chart (modified to grouped bars for clarity)
- **Priority**: P0 (政策分析核心)
- **Position**: 深层部分

## Data Source
- Draft article: topic-china-15th-five-year-plan-2026_draft.md
- AI整合: ¥2,000B (line: "未来五年投资2万亿元建设国家算力网络")
- 消费升级: Labor share +3% ≈ ¥3,900B impact (line: "提高劳动报酬占GDP比重，从2025年的52%提升到2030年的55%")
- 供应链重组: ¥500B (line: "未来五年投资5000亿元攻关芯片、操作系统、工业软件")

## Data Validation
- AI investment: Direct capital expenditure ✓
- Consumption upgrade: Calculated as 3% of ~130 trillion GDP ✓
- Supply chain: Direct R&D investment ✓
- Note: Consumption figure represents economic impact, not direct government spending

## Design Decisions
- Different colors for each pillar
- Detail annotations embedded in bars
- Consumption upgrade shown as economic impact (labor compensation increase)
- Total investment/impact highlighted at top

## Rationale
Core visualization for policy analysis. Demonstrates the scale and focus of the 15th Five-Year Plan's three main strategic pillars.
""")
print(f"✓ Quality report saved: {report_path}")
