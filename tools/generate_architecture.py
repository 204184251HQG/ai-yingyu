"""generate_architecture.py — 生成报告所需「功能架构图」 PNG。

输出: docs/architecture.png（300 DPI，1800×1080）
依赖: matplotlib（已随 PyInstaller 同包安装，无需额外）
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "architecture.png"

# 清新蓝绿配色（与软件 UI 主色保持一致）
C_PRIMARY = "#0d9488"
C_PRIMARY_DARK = "#0f766e"
C_PRIMARY_LIGHT = "#ccfbf1"
C_BLUE = "#2563eb"
C_BLUE_LIGHT = "#dbeafe"
C_ORANGE = "#ea580c"
C_ORANGE_LIGHT = "#ffedd5"
C_PURPLE = "#7c3aed"
C_PURPLE_LIGHT = "#ede9fe"
C_GREEN = "#16a34a"
C_GREEN_LIGHT = "#dcfce7"
C_RED = "#dc2626"
C_RED_LIGHT = "#fee2e2"
C_YELLOW = "#eab308"
C_YELLOW_LIGHT = "#fef9c3"
C_GRAY = "#64748b"
C_GRAY_LIGHT = "#f1f5f9"
C_TEXT = "#0f172a"

# 中文字体优先级：Windows 自带 + Linux/macOS 兜底
plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei", "SimHei", "Arial Unicode MS", "PingFang SC", "DejaVu Sans"
]
plt.rcParams["axes.unicode_minus"] = False


def box(ax, x, y, w, h, lines, fc, ec, title_fs=12, body_fs=10):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.6",
        linewidth=1.6, fc=fc, ec=ec,
    )
    ax.add_patch(rect)
    if isinstance(lines, str):
        lines = [lines]
    cy = y + h - 0.55
    for k, line in enumerate(lines):
        if k == 0:
            ax.text(x + w / 2, cy, line, ha="center", va="top",
                    fontsize=title_fs, fontweight="bold", color=C_TEXT)
        else:
            ax.text(x + w / 2, cy, line, ha="center", va="top",
                    fontsize=body_fs, color="#334155")
        cy -= (title_fs * 0.13 + 0.18) if k == 0 else (body_fs * 0.12 + 0.10)


def arrow(ax, x1, y1, x2, y2, color=C_GRAY):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=color,
                        lw=1.3, mutation_scale=14),
    )


def main():
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.set_aspect("equal")
    ax.axis("off")

    # 标题
    ax.text(50, 58, "词途 · AI 英语单词学习闯关系统  ──  功能架构",
            ha="center", va="center", fontsize=18, fontweight="bold",
            color=C_PRIMARY_DARK)

    # ── L1：主应用 ──
    box(ax, 35, 50, 30, 4.4,
        ["YingyuApp · 主应用", "CustomTkinter GUI · 底部 7 Tab 导航"],
        fc=C_PRIMARY_LIGHT, ec=C_PRIMARY, title_fs=13, body_fs=10)

    # ── L2：5 个核心功能页 + 2 个辅助页 ──
    pages = [
        # (x, y, w, h, lines, fc, ec)
        ( 1.5, 38, 17, 7.5,
          ["首页",
           "学段筛选 (小/初/高)",
           "主题卡片 + Tip"],
          C_BLUE_LIGHT, C_BLUE),
        (20.5, 38, 17, 7.5,
          ["闯关答题",
           "看词选义 / 看义选词",
           "听音辨词 / 拼写"],
          C_ORANGE_LIGHT, C_ORANGE),
        (39.5, 38, 17, 7.5,
          ["AI 助手",
           "主题/难度/词性预测",
           "构词法分析"],
          C_PURPLE_LIGHT, C_PURPLE),
        (58.5, 38, 17, 7.5,
          ["句型分析",
           "陈述/疑问/感叹/祈使",
           "SVM + 6 维特征"],
          C_GREEN_LIGHT, C_GREEN),
        (77.5, 38, 21, 7.5,
          ["工具箱",
           "年级词汇 / 构词分析",
           "学习统计 / 速查词表"],
          C_RED_LIGHT, C_RED),
    ]
    for spec in pages:
        box(ax, *spec[:4], spec[4], fc=spec[5], ec=spec[6],
            title_fs=12, body_fs=9.5)

    # ── L2.5：辅助 2 页 ──
    box(ax, 26, 26, 22, 7.5,
        ["词库管理",
         "搜索 + 分页",
         "增/删自定义单词"],
        fc=C_YELLOW_LIGHT, ec=C_YELLOW, title_fs=12, body_fs=9.5)
    box(ax, 52, 26, 22, 7.5,
        ["关于页",
         "5 个模型信息",
         "预训练机制说明"],
        fc=C_PRIMARY_LIGHT, ec=C_PRIMARY, title_fs=12, body_fs=9.5)

    # ── L3：数据层 ──
    box(ax, 8, 6, 84, 14,
        ["数据层（本地 · 零联网 · 零账号）",
         "词库  data/wordbank/{primary, middle, high}.json   ——  4997 词全量",
         "模型  yy_topic / yy_diff / yy_grade / yy_sentence / yy_ensemble.pkl   ——  5 个预训练模型",
         "运行时  yingyu_records.json （学习记录）   ·   yingyu_custom_words.json （自定义单词）",
         "语音  System.Speech (Windows .NET) · 长期 PowerShell 后端 · 抢占式播放"],
        fc=C_GRAY_LIGHT, ec=C_GRAY, title_fs=12.5, body_fs=10)

    # ── 连线：L1 → L2（5 页） ──
    for cx in (10, 29, 48, 67, 88):
        arrow(ax, 50, 50, cx, 45.5)

    # L1 / L2 → L2.5（2 页）
    arrow(ax, 50, 50, 37, 33.5)
    arrow(ax, 50, 50, 63, 33.5)

    # L2 / L2.5 → 数据层
    for cx in (10, 29, 48, 67, 88):
        arrow(ax, cx, 38, cx, 20)
    arrow(ax, 37, 26, 37, 20)
    arrow(ax, 63, 26, 63, 20)

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[OK] 已生成架构图：{OUT.relative_to(ROOT)}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    sys.exit(main() or 0)
