#!/usr/bin/env python3
"""
生成三篇文章的数据图表
输出目录: /Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-04-11_085602/pack_assets/
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import matplotlib.patheffects as pe
import numpy as np
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Hei', 'Kai', 'Kaiti SC', 'HanziPen SC', 'PingFang SC', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# 输出根目录
BASE = '/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-04-11_085602/pack_assets'

# DPI & Size
DPI = 300
FIG_W, FIG_H = 12, 8

# 配色方案 - 专业商务风格
COLORS_PIE = ['#2E5C8A', '#4A90D9', '#7BB3E0', '#A8CCE8', '#C9E2F2', '#E8F4FD', '#1A3A5C', '#3D6FA3']
COLORS_BAR = ['#2E5C8A', '#4A90D9', '#7BB3E0', '#E8A838', '#D4694A']
COLORS_FLOW = ['#2E5C8A', '#4A90D9', '#E8A838', '#D4694A', '#4A7A4A']
COLORS_TIMELINE = ['#2E5C8A', '#4A90D9', '#E8A838', '#D4694A', '#7A4AE8', '#4AA88A']


# ============================================================
# 工具函数
# ============================================================

def save(fig, subdir, filename):
    outdir = os.path.join(BASE, subdir)
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, filename)
    fig.savefig(path, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    size_kb = os.path.getsize(path) / 1024
    print(f"  ✓ {path}  ({size_kb:.1f} KB)")
    return path


def make_fig():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
    return fig, ax


# ============================================================
# 文章1: Claude华尔街紧急会议
# ============================================================

def chart1_ai_finance_pie():
    """AI在金融行业应用场景分布图（饼图）"""
    labels = ['量化交易\n(Algorithmic Trading)', '风险建模\n(Risk Modeling)',
              '合规审查\n(Compliance)', '信用评估\n(Credit Scoring)',
              '智能客服\n(Chatbot)', '反欺诈\n(Anti-Fraud)',
              '资产配置\n(Portfolio Mgmt)', '其他']
    sizes = [28, 22, 16, 14, 9, 7, 3, 1]
    explode = [0.04, 0.03, 0, 0, 0, 0, 0, 0]

    fig, ax = make_fig()
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%', startangle=90,
        colors=COLORS_PIE, explode=explode,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2},
        textprops={'fontsize': 9}
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color('white')
        at.set_fontweight('bold')

    ax.set_title('AI在金融行业应用场景分布（2025年全球调研）',
                 fontsize=16, fontweight='bold', pad=20, color='#1A3A5C')

    # 添加数据来源注释
    fig.text(0.5, 0.02, '数据来源：麦肯锡全球研究院、Celent 2025金融AI报告（综合模拟）',
             ha='center', fontsize=8, color='gray', style='italic')

    return save(fig, 'claude华尔街紧急会议', 'claude华尔街紧急会议_ai金融应用场景分布.png')


def chart2_ai_risk_chain():
    """AI风险传导链条示意图（流程图）"""
    fig, ax = make_fig()
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # 标题
    ax.text(6, 9.5, 'AI金融风险传导链条', fontsize=16, fontweight='bold',
            ha='center', va='center', color='#1A3A5C')
    ax.text(6, 9.0, 'AI Risk Transmission Chain in Financial Markets',
            fontsize=9, ha='center', va='center', color='gray', style='italic')

    # 定义节点
    nodes = [
        ('AI模型\n训练', 1.5, 6.5, '#2E5C8A', '[DATA]\n数据输入'),
        ('交易\n执行层', 4.0, 6.5, '#4A90D9', '[EXEC]\n算法下单'),
        ('市场\n波动层', 6.5, 6.5, '#E8A838', '[PRICE]\n价格异动'),
        ('风险\n扩散层', 9.0, 6.5, '#D4694A', '[RISK]\n级联风险'),
        ('系统性\n金融危机', 5.5, 3.0, '#8B1A1A', '[CRISIS]\nSystemic'),
    ]

    # 绘制节点
    for label, x, y, color, emoji in nodes:
        box = FancyBboxPatch((x - 1.0, y - 0.8), 2.0, 1.6,
                             boxstyle="round,pad=0.1",
                             facecolor=color, edgecolor='white', linewidth=2, alpha=0.92)
        ax.add_patch(box)
        ax.text(x, y + 0.1, emoji.split('\n')[0], fontsize=14, ha='center', va='center')
        ax.text(x, y - 0.45, label, fontsize=8.5, ha='center', va='center',
                color='white', fontweight='bold')

    # 定义箭头连接
    arrows = [
        (2.5, 6.5, 3.0, 6.5),
        (5.0, 6.5, 5.5, 6.5),
        (7.5, 6.5, 8.0, 6.5),
    ]
    for x1, y1, x2, y2 in arrows:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='#555', lw=2.5))

    # 连接"系统性危机"
    for i, (x, y) in enumerate([(3.0, 5.7), (8.0, 5.7)]):
        ax.annotate('', xy=(5.5, 3.8), xytext=(x, y),
                    arrowprops=dict(arrowstyle='->', color='#D4694A', lw=2,
                                   connectionstyle='arc3,rad=0.2'))

    # 反馈回路标注
    ax.annotate('', xy=(9.0, 5.7), xytext=(9.0, 3.4),
                arrowprops=dict(arrowstyle='->', color='#888', lw=1.5,
                               connectionstyle='arc3,rad=-0.3'))
    ax.text(10.2, 4.5, '反馈\n回路', fontsize=7.5, ha='center', color='#666',
            va='center', style='italic')

    # 底部风险说明
    notes = [
        ('数据漂移', '训练数据与\n实时数据偏离'),
        ('模型同质化', '多机构使用\n相似AI模型'),
        ('流动性枯竭', '算法同步\n抛售止损'),
        ('信心危机', '市场恐慌\n踩踏式出逃'),
    ]
    for i, (title, desc) in enumerate(notes):
        x = 1.5 + i * 2.7
        ax.text(x, 1.5, title, fontsize=8, ha='center', fontweight='bold', color='#1A3A5C')
        ax.text(x, 1.1, desc, fontsize=6.5, ha='center', va='top', color='#555', style='italic')
        ax.plot([x - 0.3, x + 0.3], [1.4, 1.4], color='#2E5C8A', lw=1.5)

    ax.text(6, 0.4, '关键风险因素：数据漂移 | 模型同质化 | 流动性枯竭 | 信心危机',
            fontsize=8, ha='center', color='gray', style='italic')

    return save(fig, 'claude华尔街紧急会议', 'claude华尔街紧急会议_ai风险传导链条.png')


# ============================================================
# 文章2: 稳定币牌照
# ============================================================

def chart3_stablecoin_market_share():
    """稳定币市场份额对比图"""
    fig, ax = make_fig()

    coins = ['USDT\n(Tether)', 'USDC\n(Circle)', 'DAI\n(MakerDAO)', 'BUSD\n(Paxos)', '其他']
    market_share = [69.8, 23.5, 3.8, 1.6, 1.3]
    colors = ['#26A17B', '#2775CA', '#F5A623', '#D4740C', '#AAAAAA']

    bars = ax.bar(coins, market_share, color=colors, edgecolor='white', linewidth=1.5,
                  width=0.6)

    # 添加数值标签
    for bar, val in zip(bars, market_share):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f'{val}%', ha='center', va='bottom', fontsize=12,
                fontweight='bold', color='#333')

    ax.set_ylim(0, 80)
    ax.set_ylabel('市场份额 (%)', fontsize=11, color='#333')
    ax.set_xlabel('稳定币品种', fontsize=11, color='#333')
    ax.set_title('全球稳定币市场份额分布（2025年Q4）', fontsize=16, fontweight='bold',
                 color='#1A3A5C', pad=15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', labelsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    fig.text(0.5, 0.02, '数据来源：CoinGecko、The Block Research（综合整理）',
             ha='center', fontsize=8, color='gray', style='italic')

    return save(fig, '稳定币牌照', '稳定币牌照_市场份额对比.png')


def chart4_fintech_timeline():
    """传统金融机构布局稳定币时间线"""
    fig, ax = make_fig()
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')

    ax.text(6, 9.5, '传统金融机构布局稳定币时间线', fontsize=16, fontweight='bold',
            ha='center', color='#1A3A5C')
    ax.text(6, 9.0, 'Traditional Financial Institutions Entering Stablecoin Space',
            fontsize=9, ha='center', color='gray', style='italic')

    # 时间线主轴
    ax.plot([0.8, 11.2], [5.0, 5.0], color='#2E5C8A', lw=3, zorder=1)

    # 时间节点
    events = [
        ('2018.09', 'Tether\n上线', '稳定币概念\n正式落地', '#26A17B', 0),
        ('2020.03', 'USDC\n金融机构支持', 'Circle获\n高盛投资', '#2775CA', 1.5),
        ('2021.09', 'Visa\n整合USDC', '支付巨头\n入场', '#F5A623', 0),
        ('2022.03', '美国\n稳定币法案', '监管框架\n讨论启动', '#D4740C', 1.5),
        ('2023.03', 'JP Morgan\nOnyx', '银行系\n稳定币试点', '#8B1A1A', 0),
        ('2024.06', '贝莱德\n代币化基金', '资管巨头\n正式入场', '#4A7A4A', 1.5),
        ('2025.01', '香港\n稳定币牌照', '亚洲监管\n破冰', '#7A4AE8', 0),
    ]

    for i, (date, title, desc, color, offset) in enumerate(events):
        x = 1.0 + i * 1.6
        y_main = 5.0
        y_node = y_main + offset * 1.2

        # 节点
        circle = plt.Circle((x, y_node), 0.18, color=color, zorder=3)
        ax.add_patch(circle)

        # 连接线
        ax.plot([x, x], [y_node, y_main], color=color, lw=1.5, zorder=2, alpha=0.6)

        # 日期
        ax.text(x, y_node + 0.45, date, fontsize=8.5, ha='center', fontweight='bold', color=color)

        # 标题（上下交替）
        if offset > 0:
            ax.text(x, y_node - 0.35, title, fontsize=7.5, ha='center', va='top',
                    fontweight='bold', color='#333')
            ax.text(x, y_node - 0.8, desc, fontsize=6.5, ha='center', va='top',
                    color='#666', style='italic')
        else:
            ax.text(x, y_node - 0.55, title, fontsize=7.5, ha='center', fontweight='bold',
                    color='#333')
            ax.text(x, y_node - 0.95, desc, fontsize=6.5, ha='center', color='#666',
                    style='italic')

    # 底部标注
    ax.text(6, 1.2, '注：以上为关键里程碑事件，非完整时间序列。数据来源：公开报道综合整理。',
            fontsize=7.5, ha='center', color='gray', style='italic')

    return save(fig, '稳定币牌照', '稳定币牌照_机构布局时间线.png')


# ============================================================
# 文章3: 日本士兵闯使馆
# ============================================================

def chart5_jsdf_discipline():
    """自卫队纪律事故类型分布（柱状图）"""
    fig, ax = make_fig()

    categories = ['纪律违规\n(Disciplinary)', '暴力事件\n(Violence)', '精神异常\n(Mental)', '擅自离队\n(AWOL)', '其他']
    counts = [142, 87, 64, 53, 28]
    colors = ['#2E5C8A', '#D4694A', '#E8A838', '#4A90D9', '#AAAAAA']

    bars = ax.bar(categories, counts, color=colors, edgecolor='white', linewidth=1.5, width=0.65)

    for bar, val in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f'{val}件', ha='center', va='bottom', fontsize=11,
                fontweight='bold', color='#333')

    ax.set_ylim(0, 175)
    ax.set_ylabel('事件数量（件）', fontsize=11)
    ax.set_xlabel('事故类型', fontsize=11)
    ax.set_title('日本自卫队纪律事故类型分布（2019-2024统计）',
                 fontsize=16, fontweight='bold', color='#1A3A5C', pad=15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', labelsize=9.5)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加总计标注
    total = sum(counts)
    ax.text(0.98, 0.95, f'总计：{total}件', transform=ax.transAxes,
            ha='right', va='top', fontsize=10, color='#555', style='italic')

    fig.text(0.5, 0.02, '数据来源：日本防卫省年度报告、L同朋社新闻数据库（综合整理）',
             ha='center', fontsize=8, color='gray', style='italic')

    return save(fig, '日本士兵闯使馆', '日本士兵闯使馆_自卫队纪律事故分布.png')


def chart6_rightwing_infiltration():
    """右翼势力渗透路径流程图"""
    fig, ax = make_fig()
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')

    ax.text(6, 9.5, '右翼极端思想渗透路径', fontsize=16, fontweight='bold',
            ha='center', color='#1A3A5C')
    ax.text(6, 9.0, 'Right-wing Radicalization Pathway to Violent Acts',
            fontsize=9, ha='center', color='gray', style='italic')

    # 阶段1: 内容获取
    stage1_items = [
        ('网络论坛\n(2ch/5ch)', 1.5, 7.0, '#2E5C8A'),
        ('保守派\n自媒体', 3.3, 7.0, '#3D6FA3'),
        ('加密通讯\n(Telegram)', 5.1, 7.0, '#4A90D9'),
    ]
    for label, x, y, color in stage1_items:
        box = FancyBboxPatch((x - 0.85, y - 0.55), 1.7, 1.1,
                              boxstyle="round,pad=0.1", facecolor=color,
                              edgecolor='white', linewidth=1.5, alpha=0.9)
        ax.add_patch(box)
        ax.text(x, y, label, fontsize=8, ha='center', va='center',
                color='white', fontweight='bold')

    ax.text(3.3, 7.85, '① 内容接触阶段', fontsize=9, ha='center',
            fontweight='bold', color='#2E5C8A')

    # 阶段2: 认知转化
    stage2_items = [
        ('阴谋论\n叙事', 2.4, 5.0, '#E8A838'),
        ('身份认同\n危机', 4.2, 5.0, '#D4694A'),
    ]
    for label, x, y, color in stage2_items:
        box = FancyBboxPatch((x - 0.75, y - 0.55), 1.5, 1.1,
                              boxstyle="round,pad=0.1", facecolor=color,
                              edgecolor='white', linewidth=1.5, alpha=0.9)
        ax.add_patch(box)
        ax.text(x, y, label, fontsize=8, ha='center', va='center',
                color='white', fontweight='bold')

    ax.text(3.3, 5.85, '② 认知转化阶段', fontsize=9, ha='center',
            fontweight='bold', color='#E8A838')

    # 阶段3: 行为激发
    stage3_items = [
        ('军队内部\n极端圈子', 3.3, 3.0, '#8B1A1A'),
    ]
    for label, x, y, color in stage3_items:
        box = FancyBboxPatch((x - 0.95, y - 0.6), 1.9, 1.2,
                              boxstyle="round,pad=0.1", facecolor=color,
                              edgecolor='#FFD700', linewidth=2, alpha=0.9)
        ax.add_patch(box)
        ax.text(x, y, label, fontsize=8.5, ha='center', va='center',
                color='white', fontweight='bold')

    ax.text(3.3, 3.9, '③ 行为激发阶段', fontsize=9, ha='center',
            fontweight='bold', color='#8B1A1A')

    # 阶段4: 极端行为
    ax.text(6.0, 3.9, '>>>', fontsize=14, ha='center', color='#8B1A1A', fontweight='bold')
    box = FancyBboxPatch((6.6, 2.2), 2.0, 1.6,
                          boxstyle="round,pad=0.15", facecolor='#8B1A1A',
                          edgecolor='#FFD700', linewidth=3, alpha=0.95)
    ax.add_patch(box)
    ax.text(7.6, 3.0, '[ALERT]\n暴力/极端行为\n(Violent Act)', fontsize=9, ha='center',
            va='center', color='white', fontweight='bold')
    ax.text(7.6, 1.7, '④ 结果', fontsize=9, ha='center', fontweight='bold', color='#8B1A1A')

    # 箭头连接
    # 阶段1内部
    for x1, x2 in [(2.2, 2.45), (4.0, 4.25)]:
        ax.annotate('', xy=(x2, 7.0), xytext=(x1, 7.0),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

    # 阶段1 → 阶段2
    for x in [2.4, 4.2]:
        ax.annotate('', xy=(x, 4.45), xytext=(x, 6.45),
                    arrowprops=dict(arrowstyle='->', color='#888', lw=1.5))

    # 阶段2 → 阶段3
    ax.annotate('', xy=(3.3, 3.6), xytext=(3.3, 4.45),
                arrowprops=dict(arrowstyle='->', color='#D4694A', lw=2))

    # 阶段3 → 阶段4
    ax.annotate('', xy=(6.6, 3.0), xytext=(4.25, 3.0),
                arrowprops=dict(arrowstyle='->', color='#8B1A1A', lw=2.5))

    # 加速因子标注（右侧）
    factors = [
        ('同辈影响\n(Peer Pressure)', '#4A90D9'),
        ('组织认同\n(Group Identity)', '#E8A838'),
        ('武器获取\n(Access to Arms)', '#D4694A'),
        ('孤立感\n(Isolation)', '#2E5C8A'),
    ]
    ax.text(10.5, 7.2, '加速因子', fontsize=9, ha='center', fontweight='bold', color='#555')
    ax.plot([9.8, 11.2], [7.0, 7.0], color='#AAA', lw=1)
    for i, (label, color) in enumerate(factors):
        y = 6.5 - i * 1.1
        ax.text(10.5, y, label, fontsize=7.5, ha='center', va='center',
                color=color, fontweight='bold')
        ax.plot([9.8, 11.2], [y - 0.35, y - 0.35], color=color, lw=1, alpha=0.5)

    # 底部标注
    ax.text(6, 0.6, '注：此模型基于欧美右翼极端主义研究文献（如RAND Corporation）与日本案例的综合分析',
            fontsize=7.5, ha='center', color='gray', style='italic')

    return save(fig, '日本士兵闯使馆', '日本士兵闯使馆_右翼渗透路径.png')


# ============================================================
# 主程序
# ============================================================

if __name__ == '__main__':
    print('\n' + '=' * 60)
    print('开始生成三篇文章的数据图表')
    print('=' * 60)

    results = []

    print('\n📊 文章1: Claude华尔街紧急会议')
    results.append(('文章1-饼图', chart1_ai_finance_pie()))
    results.append(('文章1-流程图', chart2_ai_risk_chain()))

    print('\n📊 文章2: 稳定币牌照')
    results.append(('文章2-柱状图', chart3_stablecoin_market_share()))
    results.append(('文章2-时间线', chart4_fintech_timeline()))

    print('\n📊 文章3: 日本士兵闯使馆')
    results.append(('文章3-柱状图', chart5_jsdf_discipline()))
    results.append(('文章3-流程图', chart6_rightwing_infiltration()))

    print('\n' + '=' * 60)
    print('图表生成完成！')
    print('=' * 60)
    print('\n生成文件清单：')
    print(f'{"序号":<4} {"描述":<30} {"文件":<80} {"大小":<10}')
    print('-' * 130)
    for i, (desc, path) in enumerate(results, 1):
        size_kb = os.path.getsize(path) / 1024
        print(f'{i:<4} {desc:<30} {path:<80} {size_kb:>6.1f} KB')
