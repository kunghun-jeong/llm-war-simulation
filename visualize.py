"""
visualize.py - 결과 시각화
토너먼트 결과 및 자료구조 분석을 그래프로 출력
"""

import json
import glob
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

MODEL_NAMES = {
    "llama": "Llama 3.1",
    "gemma": "Gemma 3",
    "qwen":  "Qwen 2.5",
}
COLORS = {
    "llama": "#ef5350",
    "gemma": "#42a5f5",
    "qwen":  "#66bb6a",
}


def load_latest_result() -> dict:
    files = sorted(glob.glob("results/tournament_*.json"))
    if not files:
        print("결과 파일이 없습니다. tournament.py를 먼저 실행하세요.")
        return {}
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


def plot_all(data: dict):
    if not data:
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("LLM 전투 토너먼트 분석 결과", fontsize=16, fontweight="bold")

    teams = ["llama", "gemma", "qwen"]
    names = [MODEL_NAMES[t] for t in teams]

    # ── 1. 승리 횟수 바 차트 ─────────────────────
    ax1 = axes[0]
    wins = [data["wins"].get(t, 0) for t in teams]
    bars = ax1.bar(names, wins,
                   color=[COLORS[t] for t in teams], width=0.5, edgecolor="white")
    ax1.set_title("팀별 승리 횟수", fontweight="bold")
    ax1.set_ylabel("승리 수")
    ax1.set_ylim(0, max(wins) + 2)
    for bar, w in zip(bars, wins):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 str(w), ha="center", fontweight="bold")

    # ── 2. 누적 HP 바 차트 ───────────────────────
    ax2 = axes[1]
    hps = [data["total_hp"].get(t, 0) for t in teams]
    bars2 = ax2.bar(names, hps,
                    color=[COLORS[t] for t in teams], width=0.5, edgecolor="white")
    ax2.set_title("누적 잔여 HP", fontweight="bold")
    ax2.set_ylabel("합산 HP")
    for bar, h in zip(bars2, hps):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                 str(h), ha="center", fontsize=9)

    # ── 3. 자료구조 사용 분포 (스택 바) ──────────
    ax3 = axes[2]
    ds_ops  = data.get("ds_ops", {})
    ds_types = sorted({ds for t in teams for ds in ds_ops.get(t, {})})
    x       = np.arange(len(teams))
    bottom  = np.zeros(len(teams))
    cmap    = plt.cm.Set3(np.linspace(0, 1, len(ds_types)))

    for i, ds in enumerate(ds_types):
        vals = [ds_ops.get(t, {}).get(ds, 0) for t in teams]
        ax3.bar(x, vals, bottom=bottom,
                label=ds, color=cmap[i], width=0.5, edgecolor="white")
        bottom += np.array(vals)

    ax3.set_xticks(x)
    ax3.set_xticklabels(names)
    ax3.set_title("자료구조 연산 분포", fontweight="bold")
    ax3.set_ylabel("연산 횟수")
    ax3.legend(loc="upper right", fontsize=7)

    plt.tight_layout()
    os.makedirs("results", exist_ok=True)
    out = "results/tournament_analysis.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"  📊 그래프 저장: {out}")
    plt.show()


if __name__ == "__main__":
    data = load_latest_result()
    plot_all(data)
