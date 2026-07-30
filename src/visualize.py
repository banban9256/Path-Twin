"""
그래프 시각화 - NetworkX + matplotlib
"""
import os
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathfinder import (
    build_graph, find_shortest_path, get_all_nodes,
    PROFILES, MODES, PROFILE_LABELS,
)

_FONT_PATH = r"C:\Windows\Fonts\malgun.ttf"
_fp = fm.FontProperties(fname=_FONT_PATH)
_fp_bold = fm.FontProperties(fname=_FONT_PATH, weight="bold")
plt.rcParams["axes.unicode_minus"] = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")


POS = {
    "서관_시작노드":              (0, 0),
    "서관_1층_문앞(중앙)":        (1, 0.5),
    "서관_1층_문앞(장애인)":       (0, 1),
    "서관_1층_로비":              (1, 1.5),
    "서관_1층_계단앞":            (2, 2),
    "서관_1층_엘리베이터앞":       (1, 2.5),
    "서관_2층_계단앞":            (2, 3.5),
    "서관_2층_엘리베이터앞":       (1, 3.5),
    "서관_3층_계단앞":            (2, 5),
    "서관_3층_엘리베이터앞":       (1, 5),
    "1층_중앙복도(연결통로)":      (3, 1.5),
    "동관_시작노드":              (5, 0),
    "동관_1층_문앞(중앙)":        (5.5, 0.5),
    "동관_1층_문앞(좌측장애인)":    (4.5, 1),
    "동관_1층_문앞(우측장애인)":    (6, 1),
    "동관_1층_로비":              (5.5, 1.5),
    "동관_1층_계단앞":            (6, 2),
    "주차장쪽_시작노드":           (7, 0),
    "주차장_계단위":              (7.5, 1.5),
    "중간쪽계단_위":              (8, 2.5),
    "열람실_긴계단_아래(동관쪽길)": (6.5, 3),
    "구름다리_입구":              (8.5, 3),
    "구름다리_출구(서관2층)":      (1, 4),
    "쪽길_시작노드(개구멍)":       (9, 1),
    "쪽계단_아래":                (9, 2),
    "3층_쪽계단위":               (9, 4),
    "3층_열람실_입구":             (5, 5),
}


def _draw_labels(G, pos, ax, font_size=6):
    for node, (x, y) in pos.items():
        if node in G.nodes():
            ax.text(x, y, node, fontsize=font_size, fontproperties=_fp_bold,
                    ha="center", va="center", color="#222")


def visualize_path(profile, mode, start, end, save_path=None):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    G = build_graph(profile, mode)
    path, tw, details, summary = find_shortest_path(start, end, profile, mode)

    fig, ax = plt.subplots(figsize=(20, 12))

    nx.draw_networkx_edges(G, POS, ax=ax, alpha=0.12, edge_color="gray",
                           arrows=True, arrowsize=6, width=0.5)

    if path and len(path) > 1:
        path_edges = list(zip(path[:-1], path[1:]))
        nx.draw_networkx_edges(G, POS, edgelist=path_edges, ax=ax,
                               edge_color="#e74c3c", width=3, alpha=0.9,
                               arrows=True, arrowsize=15)
        nx.draw_networkx_nodes(G, POS, nodelist=path, ax=ax,
                               node_color="#e74c3c", node_size=500, alpha=0.9)
        other = [n for n in G.nodes() if n not in set(path)]
    else:
        other = list(G.nodes())

    nx.draw_networkx_nodes(G, POS, nodelist=other, ax=ax,
                           node_color="#3498db", node_size=350, alpha=0.6)

    _draw_labels(G, POS, ax)

    label = PROFILE_LABELS.get(profile, profile)
    title_lines = [f"경삼관 경로 탐색  |  {label}  |  {mode}",
                   f"{start}  ->  {end}"]
    if path:
        title_lines.append(
            f"총 거리: {summary['total_distance_m']}m  |  "
            f"계단: {summary['total_stairs']}칸  |  "
            f"가중치: {summary['total_weight']:.4f}")
    else:
        title_lines.append("경로를 찾을 수 없습니다.")

    ax.set_title("\n".join(title_lines), fontproperties=_fp, fontsize=13, pad=15)
    ax.axis("off")
    plt.tight_layout()

    if save_path is None:
        safe = profile.replace(" ", "_")
        save_path = os.path.join(OUTPUT_DIR, f"path_{safe}_{mode}.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Saved: {save_path}")
    return save_path


def visualize_profile_comparison(start, end):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fig, axes = plt.subplots(1, len(PROFILES), figsize=(30, 8))

    for ax, profile in zip(axes, PROFILES):
        G = build_graph(profile, "빠른도착")
        path, tw, details, summary = find_shortest_path(start, end, profile, "빠른도착")

        nx.draw_networkx_edges(G, POS, ax=ax, alpha=0.1, edge_color="gray",
                               arrows=True, arrowsize=4, width=0.3)
        all_nodes_list = list(G.nodes())
        if path and len(path) > 1:
            path_edges = list(zip(path[:-1], path[1:]))
            nx.draw_networkx_edges(G, POS, edgelist=path_edges, ax=ax,
                                   edge_color="#e74c3c", width=2.5, alpha=0.9,
                                   arrows=True, arrowsize=10)
            nx.draw_networkx_nodes(G, POS, nodelist=path, ax=ax,
                                   node_color="#e74c3c", node_size=200)
            other = [n for n in all_nodes_list if n not in set(path)]
        else:
            other = all_nodes_list
        nx.draw_networkx_nodes(G, POS, nodelist=other, ax=ax,
                               node_color="#3498db", node_size=120, alpha=0.4)

        _draw_labels(G, POS, ax, font_size=4)

        label = PROFILE_LABELS.get(profile, profile)
        if path:
            title = (f"{label}\n"
                     f"거리 {summary['total_distance_m']}m | "
                     f"계단 {summary['total_stairs']}칸\n"
                     f"W={summary['total_weight']:.2f}")
        else:
            title = f"{label}\n경로 없음"
        ax.set_title(title, fontproperties=_fp, fontsize=10)
        ax.axis("off")

    plt.suptitle(f"프로필별 경로 비교 (빠른도착) | {start} -> {end}",
                 fontproperties=_fp, fontsize=14)
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "compare_profiles_fast.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Saved: {save_path}")
    return save_path


def visualize_mode_comparison(profile, start, end):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(24, 10))

    for ax, mode in zip(axes, MODES):
        G = build_graph(profile, mode)
        path, tw, details, summary = find_shortest_path(start, end, profile, mode)

        nx.draw_networkx_edges(G, POS, ax=ax, alpha=0.1, edge_color="gray",
                               arrows=True, arrowsize=4, width=0.3)
        all_nodes_list = list(G.nodes())
        if path and len(path) > 1:
            path_edges = list(zip(path[:-1], path[1:]))
            nx.draw_networkx_edges(G, POS, edgelist=path_edges, ax=ax,
                                   edge_color="#e74c3c", width=3, alpha=0.9,
                                   arrows=True, arrowsize=12)
            nx.draw_networkx_nodes(G, POS, nodelist=path, ax=ax,
                                   node_color="#e74c3c", node_size=300)
            other = [n for n in all_nodes_list if n not in set(path)]
        else:
            other = all_nodes_list
        nx.draw_networkx_nodes(G, POS, nodelist=other, ax=ax,
                               node_color="#3498db", node_size=200, alpha=0.5)

        _draw_labels(G, POS, ax, font_size=5)

        if path:
            title = (f"{mode}\n"
                     f"거리 {summary['total_distance_m']}m | "
                     f"계단 {summary['total_stairs']}칸\n"
                     f"W={summary['total_weight']:.2f}")
        else:
            title = f"{mode}\n경로 없음"
        ax.set_title(title, fontproperties=_fp, fontsize=11)
        ax.axis("off")

    label = PROFILE_LABELS.get(profile, profile)
    plt.suptitle(f"모드 비교 | {label} | {start} -> {end}",
                 fontproperties=_fp, fontsize=14)
    plt.tight_layout()
    safe = profile.replace(" ", "_")
    save_path = os.path.join(OUTPUT_DIR, f"compare_modes_{safe}.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Saved: {save_path}")
    return save_path


if __name__ == "__main__":
    start = "서관_시작노드"
    end = "3층_열람실_입구"

    print("=== 프로필별 경로 시각화 (빠른도착) ===")
    for p in PROFILES:
        visualize_path(p, "빠른도착", start, end)

    print("\n=== 프로필별 경로 비교 ===")
    visualize_profile_comparison(start, end)

    print("\n=== 모드 비교 (일반 보행자) ===")
    visualize_mode_comparison("일반", start, end)
