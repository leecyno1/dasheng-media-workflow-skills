#!/usr/bin/env python3
"""
Chart 1: 中国GDP增长目标历史对比（2010-2030）
Type: Line Chart
Priority: P0 (建立核心论点)
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set Chinese font
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Data from draft
periods = ['2010-2015', '2016-2020', '2021-2025', '2026-2030\n(十五五)']
growth_rates = [7.8, 6.5, 5.2, 4.75]  # Using midpoint for 2026-2030 (4.5-5%)
period_centers = [2012.5, 2018, 2023, 2028]

# Create figure
fig, ax = plt.subplots(figsize=(12, 7))

# Plot line
line = ax.plot(
    period_centers,
    growth_rates,
    marker='o',
    markersize=10,
    linewidth=2.5,
    color='#d62728',
    label='GDP增长目标'
)

# Add value labels
for x, y, period in zip(period_centers, growth_rates, periods):
    ax.annotate(
        f'{y}%',
        xy=(x, y),
        xytext=(0, 10),
        textcoords='offset points',
        ha='center',
        fontsize=11,
        weight='bold',
        color='#d62728'
    )

# Add key annotations
ax.annotate(
    '供给侧改革',
    xy=(2018, 6.5),
    xytext=(2018, 7.5),
    ha='center',
    fontsize=10,
    arrowprops=dict(arrowstyle='->', color='gray', lw=1.5),
    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3)
)

ax.annotate(
    '十五五开局\n结构性转型',
    xy=(2028, 4.75),
    xytext=(2028, 6),
    ha='center',
    fontsize=10,
    arrowprops=dict(arrowstyle='->', color='gray', lw=1.5),
    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.3)
)

# Add shaded area for historical vs forecast
ax.axvspan(2010, 2025, alpha=0.1, color='gray', label='历史数据')
ax.axvspan(2025, 2030, alpha=0.1, color='blue', label='预测数据')

# Customize axes
ax.set_xlabel('时期', fontsize=12, weight='bold')
ax.set_ylabel('GDP增长目标 (%)', fontsize=12, weight='bold')
ax.set_title(
    '中国GDP增长目标历史对比（2010-2030）\n从速度优先到质量优先',
    fontsize=16,
    weight='bold',
    pad=20
)

# Set x-axis ticks
ax.set_xticks(period_centers)
ax.set_xticklabels(periods, fontsize=10)

# Add grid
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_axisbelow(True)

# Set y-axis range
ax.set_ylim(4, 9)

# Add legend
ax.legend(loc='upper right', fontsize=10)

plt.tight_layout()

# Save
output_path = Path(__file__).parent / 'chart_01_gdp_growth_history.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"✓ Chart saved: {output_path}")

# Quality report
report_path = Path(__file__).parent / 'chart_01_quality_report.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("""# Chart 1 Quality Report

## Chart Information
- **Title**: 中国GDP增长目标历史对比（2010-2030）
- **Type**: Line Chart
- **Priority**: P0 (建立核心论点)
- **Position**: 开头段落后

## Data Source
- Draft article: topic-china-15th-five-year-plan-2026_draft.md
- 2010-2015: 7.8% (line: "2010-2015年，中国经济增长的主要驱动力是投资")
- 2016-2020: 6.5% (line: "年均6.5%")
- 2021-2025: 5.2% (line: "年均5.2%")
- 2026-2030: 4.5%-5% (line: "4.5%-5%的GDP增长目标")

## Data Validation
- Consistent downward trend ✓
- 2026-2030 uses midpoint (4.75%) for visualization
- Key policy milestones annotated (2016 supply-side reform, 2026 15th FYP)

## Design Decisions
- Red line emphasizes declining trend
- Shaded areas distinguish historical vs forecast data
- Annotations highlight key turning points
- Clear visual narrative: "从速度到质量"

## Rationale
Establishes the core argument that the lower growth target is a strategic choice, not a forced slowdown. Visual evidence for "从速度优先到结构完整性优先".
""")
print(f"✓ Quality report saved: {report_path}")
