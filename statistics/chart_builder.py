"""
Statistics chart builder — Matplotlib figures embedded into Kivy widgets.
"""
from __future__ import annotations
from typing import Optional
import io


def _get_fig(width: float = 6, height: float = 3.5):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_alpha(0)
    ax.set_facecolor("#252536")
    for spine in ax.spines.values():
        spine.set_color("#3E3E5A")
    ax.tick_params(colors="#9E9EBF", labelsize=8)
    ax.title.set_color("#E8E8FF")
    ax.xaxis.label.set_color("#9E9EBF")
    ax.yaxis.label.set_color("#9E9EBF")
    return fig, ax


def bar_chart_png(
    labels: list[str], values: list[float],
    title: str = "", xlabel: str = "", ylabel: str = "",
    color: str = "#7C4DFF", width: float = 6, height: float = 3.5,
) -> bytes:
    fig, ax = _get_fig(width, height)
    bars = ax.bar(labels, values, color=color, width=0.6, zorder=2)
    ax.set_title(title, fontsize=11, pad=8)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.yaxis.grid(True, color="#3E3E5A", linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    # Value labels on top of bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(round(val, 1)), ha="center", va="bottom",
                color="#E8E8FF", fontsize=7)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0); data = buf.read()
    import matplotlib.pyplot as plt; plt.close(fig)
    return data


def dual_bar_chart_png(
    labels: list[str], values1: list[float], values2: list[float],
    label1: str = "Done", label2: str = "Overdue",
    title: str = "", xlabel: str = "", ylabel: str = "",
    color1: str = "#4CAF50", color2: str = "#F44336",
    width: float = 6, height: float = 3.5,
) -> bytes:
    import numpy as np
    fig, ax = _get_fig(width, height)
    
    x = np.arange(len(labels))
    bar_width = 0.35
    
    bars1 = ax.bar(x - bar_width/2, values1, bar_width, label=label1, color=color1, zorder=2)
    bars2 = ax.bar(x + bar_width/2, values2, bar_width, label=label2, color=color2, zorder=2)
    
    ax.set_title(title, fontsize=11, pad=8)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(facecolor="#252536", edgecolor="#3E3E5A", labelcolor="#E8E8FF", fontsize=8)
    ax.yaxis.grid(True, color="#3E3E5A", linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0); data = buf.read()
    import matplotlib.pyplot as plt; plt.close(fig)
    return data


def line_chart_png(
    dates: list[str], values: list[float],
    title: str = "", ylabel: str = "",
    color: str = "#7C4DFF", width: float = 6, height: float = 3.5,
) -> bytes:
    import matplotlib.pyplot as plt
    fig, ax = _get_fig(width, height)
    ax.plot(dates, values, color=color, linewidth=2, marker="o",
            markersize=4, zorder=2)
    ax.fill_between(dates, values, alpha=0.15, color=color)
    ax.set_title(title, fontsize=11, pad=8)
    ax.set_ylabel(ylabel)
    ax.yaxis.grid(True, color="#3E3E5A", linewidth=0.5, zorder=0)
    plt.xticks(rotation=45, ha="right", fontsize=7)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0); data = buf.read()
    plt.close(fig); return data


def pie_chart_png(
    labels: list[str], values: list[float],
    title: str = "", width: float = 5, height: float = 4,
) -> bytes:
    import matplotlib.pyplot as plt
    PALETTE = ["#7C4DFF","#FFB300","#42A5F5","#66BB6A","#EF5350",
               "#AB47BC","#26C6DA","#EC407A","#26A69A","#8D6E63"]
    colours = [PALETTE[i % len(PALETTE)] for i in range(len(labels))]
    fig, ax = _get_fig(width, height)
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, autopct="%1.0f%%",
        colors=colours, startangle=140,
        wedgeprops=dict(edgecolor="#1E1E2E", linewidth=1.5),
        pctdistance=0.8,
    )
    for t in texts: t.set_color("#9E9EBF"); t.set_fontsize(8)
    for a in autotexts: a.set_color("#E8E8FF"); a.set_fontsize(7)
    ax.set_title(title, fontsize=11, pad=8, color="#E8E8FF")
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                                     facecolor="#252536")
    buf.seek(0); data = buf.read()
    plt.close(fig); return data


def horizontal_bar_png(
    labels: list[str], values: list[float],
    title: str = "", xlabel: str = "",
    width: float = 6, height: float = 3.5,
) -> bytes:
    import matplotlib.pyplot as plt
    PALETTE = ["#7C4DFF","#FFB300","#42A5F5","#66BB6A","#EF5350",
               "#AB47BC","#26C6DA","#EC407A","#26A69A","#8D6E63"]
    colours = [PALETTE[i % len(PALETTE)] for i in range(len(labels))]
    fig, ax = _get_fig(width, height)
    bars = ax.barh(labels, values, color=colours, height=0.6)
    ax.set_title(title, fontsize=11, pad=8); ax.set_xlabel(xlabel)
    ax.xaxis.grid(True, color="#3E3E5A", linewidth=0.5)
    ax.set_axisbelow(True)
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                str(round(val, 1)), va="center", color="#E8E8FF", fontsize=7)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                                     facecolor="#252536")
    buf.seek(0); data = buf.read()
    plt.close(fig); return data
