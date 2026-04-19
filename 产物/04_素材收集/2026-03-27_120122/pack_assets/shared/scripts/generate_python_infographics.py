from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path("/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets")

plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang SC", "Heiti TC", "STHeiti", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False


def render_panel(topic: str, name: str, title: str, bullets: list[str], accent: str) -> None:
    target = ROOT / topic / "images" / "generated" / f"{name}.png"
    fig = plt.figure(figsize=(10, 14), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    fig.text(0.07, 0.93, title, fontsize=26, fontweight="bold", color="#111827")
    fig.patches.extend([
        plt.Rectangle((0.07, 0.89), 0.2, 0.012, transform=fig.transFigure, color=accent, figure=fig)
    ])
    y = 0.82
    for idx, bullet in enumerate(bullets, start=1):
        fig.text(0.08, y, f"{idx:02d}", fontsize=18, fontweight="bold", color=accent)
        fig.text(0.16, y, bullet, fontsize=17, color="#1f2937", wrap=True)
        y -= 0.12
    fig.text(0.08, 0.07, "Python infographic fallback", fontsize=12, color="#6b7280")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def main() -> None:
    render_panel(
        "reinflation",
        "oil_price_inflation_expectation_infographic",
        "再通胀传导链",
        [
            "地缘/关税/航运冲击先推升能源与输入成本",
            "价格扰动进入通胀预期，利率下行空间收窄",
            "债券、成长股与贵金属的定价框架随之变化",
        ],
        "#b45309",
    )
    render_panel(
        "reinflation",
        "fed_stagflation_signal_infographic",
        "Fed 信号不是单一通胀，而是更复杂的滞胀风险",
        [
            "不确定性上升",
            "通胀预测未回到舒服区间",
            "高通胀与慢增长可能同时出现",
        ],
        "#dc2626",
    )
    render_panel(
        "reinflation",
        "asset_repricing_map_infographic",
        "资产重估地图",
        [
            "长债更怕通胀预期重新抬头",
            "高估值资产更怕贴现率长期居高",
            "油和金都会被交易，但逻辑并不相同",
        ],
        "#1d4ed8",
    )
    render_panel(
        "takaichi",
        "coalition_right_shift_infographic",
        "日本执政轴心右移",
        [
            "旧联盟失稳后，权力重组转向更右的伙伴",
            "国家安全、修宪、防卫成为新动员主线",
            "联盟重组既是策略选择，也是社会情绪映射",
        ],
        "#7c3aed",
    )
    render_panel(
        "takaichi",
        "aging_labor_gap_infographic",
        "老龄化与劳动力缺口",
        [
            "人口下降与高龄化同步发生",
            "经济离不开外劳，但政治上又需要强硬回应",
            "这种结构矛盾为极右叙事提供了土壤",
        ],
        "#059669",
    )
    render_panel(
        "takaichi",
        "security_taiwan_impact_infographic",
        "安全姿态与区域波动",
        [
            "更强硬的安全姿态会抬高东亚摩擦频率",
            "对台海的公开表述会增加中日摩擦敏感度",
            "供应链、海运与风险资产都会感受到二阶影响",
        ],
        "#dc2626",
    )


if __name__ == "__main__":
    main()
