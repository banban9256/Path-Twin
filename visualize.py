"""
그래프 시각화 - NetworkX + matplotlib
경삼관 내부 도면 기반 그래프 시각화
"""
import os
import sqlite3
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from pathfinder import (
    build_graph, find_shortest_path, get_all_nodes, get_all_edges,
    PROFILES, MODES, PROFILE_LABELS,
)

matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "goahead.db")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")


def get_manual_positions():
    """경삼관 구조에 따른 수동 좌표 배치 (x=좌우, y=상하)"""
    return {
        "서관_시작노드":          (0, 0),
        "서관_중앙입구":          (1, 1),
        "서관_쪽계단앞":          (2, 2),
        "서관_왼쪽장애인통로":     (0, 2),
        "서관_엘리베이터":        (1, 3),
        "서관_통로":              (3, 2.5),
        "서관_1층_계단":          (1, 4),
        "서관_2층_대학행정팀":    (0.5, 5),
        "서관_2층_계단":          (1, 5),
        "서관_2층_엘리베이터":    (1.5, 5),
        "서관_2층_열람실계단":    (2, 5),
        "서관_3층_계단":          (1, 6),
        "서관_3층_엘리베이터":    (1.5, 6),
        "서관_3층_열람실":        (2, 6),
        "서관_4층_휴게실(사용중지)": (1, 7),
        "서관_1층_열람실계단":    (2, 4),
        "동관_시작노드":          (4, 0),
        "동관_중앙입구":          (5, 1),
        "동관_쪽계단앞":          (6, 2),
        "동관_오른쪽장애인통로":   (4, 2),
        "동관_쪽길":              (7, 1),
        "동관_계단쪽복도":        (5, 3),
        "동관_엘리베이터":        (5, 4),
        "동관_1층_계단":          (5, 5),
        "동관_2층_계단":          (5, 6),
        "동관_3층_계단":          (5, 7),
        "동관_2층_자료실1":       (4.5, 6),
        "동관_3층_자료실2":       (4.5, 7),
        "동관_4층_북카페":        (4.5, 8),
        "동관_주차장쪽계단":      (6, 4),
        "열람실_입구(경로1_중간쪽계단)": (7, 5),
        "열람실_입구(경로2_구름다리)":   (7.5, 5.5),
        "열람실_입구(경로3_엘리베이터)": (8, 5),
        "열람실_입구(경로4_서쪽계단)":   (7, 6),
        "열람실_입구(경로5_1층계단)":   (7.5, 6.5),
        "꼼지락":                  (4.5, 2.5),
    }


def visualize_path(profile, mode, start, end, save_path=None):
    """개별 프로필+모드 경로 시각화"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    G = build_graph(profile, mode)
    pos = get_manual_positions()

    fig, ax = plt.subplots(1, 1, figsize=(18, 12))

    path, tw, details, summary = find_shortest_path(start, end, profile, mode)

    all_edges = list(G.edges())
    all_nodes_list = list(G.nodes())

    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.12, edge_color="gray",
                           arrows=True, arrowsize=6, width=0.5)

    path_edges = []
    if path and len(path) > 1:
        path_edges = list(zip(path[:-1], path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, ax=ax,
                               edge_color="#e74c3c", width=3, alpha=0.9,
                               arrows=True, arrowsize=15)
        nx.draw_networkx_nodes(G, pos, nodelist=path, ax=ax,
                               node_color="#e74c3c", node_size=500, alpha=0.9)
        path_set = set(path)
        other = [n for n in all_nodes_list if n not in path_set]
    else:
        other = all_nodes_list

    nx.draw_networkx_nodes(G, pos, nodelist=other, ax=ax,
                           node_color="#3498db", node_size=350, alpha=0.6)

    labels = {n: n for n in all_nodes_list}
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=6,
                            font_weight="bold")

    label = PROFILE_LABELS.get(profile, profile)
    title_lines = [
        f"경삼관 경로 탐색  |  {label}  |  {mode}",
        f"{start}  ->  {end}",
    ]
    if path:
        title_lines.append(
            f"총 거리: {summary['total_distance_m']}m  |  "
            f"계단: {summary['total_stairs']}칸  |  "
            f"가중치: {summary['total_weight']:.1f}"
        )
    else:
        title_lines.append("경로를 찾을 수 없습니다.")

    ax.set_title("\n".join(title_lines), fontsize=13, pad=15)
    ax.axis("off")
    plt.tight_layout()

    if save_path is None:
        safe_profile = profile.replace(" ", "_")
        save_path = os.path.join(OUTPUT_DIR, f"path_{safe_profile}_{mode}.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Saved: {save_path}")
    return save_path


def visualize_profile_comparison(start, end):
    """프로필별 경로 비교 (빠른도착 모드)"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pos = get_manual_positions()

    fig, axes = plt.subplots(1, len(PROFILES), figsize=(30, 8))

    for ax, profile in zip(axes, PROFILES):
        G = build_graph(profile, "빠른도착")
        path, tw, details, summary = find_shortest_path(start, end, profile, "빠른도착")

        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.1, edge_color="gray",
                               arrows=True, arrowsize=4, width=0.3)

        all_nodes_list = list(G.nodes())
        if path and len(path) > 1:
            path_edges = list(zip(path[:-1], path[1:]))
            nx.draw_networkx_edges(G, pos, edgelist=path_edges, ax=ax,
                                   edge_color="#e74c3c", width=2.5, alpha=0.9,
                                   arrows=True, arrowsize=10)
            nx.draw_networkx_nodes(G, pos, nodelist=path, ax=ax,
                                   node_color="#e74c3c", node_size=200)
            path_set = set(path)
            other = [n for n in all_nodes_list if n not in path_set]
        else:
            other = all_nodes_list

        nx.draw_networkx_nodes(G, pos, nodelist=other, ax=ax,
                               node_color="#3498db", node_size=120, alpha=0.4)

        label = PROFILE_LABELS.get(profile, profile)
        if path:
            title = (f"{label}\n"
                     f"거리 {summary['total_distance_m']}m | "
                     f"계단 {summary['total_stairs']}칸\n"
                     f"W={summary['total_weight']:.1f}")
        else:
            title = f"{label}\n경로 없음"
        ax.set_title(title, fontsize=10)
        ax.axis("off")

    plt.suptitle(f"프로필별 경로 비교 (빠른도착) | {start} -> {end}", fontsize=14)
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "compare_profiles_fast.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Saved: {save_path}")
    return save_path


def visualize_mode_comparison(profile, start, end):
    """모드별 경로 비교 (빠른도착 vs 편하게)"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pos = get_manual_positions()

    fig, axes = plt.subplots(1, 2, figsize=(24, 10))

    for ax, mode in zip(axes, MODES):
        G = build_graph(profile, mode)
        path, tw, details, summary = find_shortest_path(start, end, profile, mode)

        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.1, edge_color="gray",
                               arrows=True, arrowsize=4, width=0.3)

        all_nodes_list = list(G.nodes())
        if path and len(path) > 1:
            path_edges = list(zip(path[:-1], path[1:]))
            nx.draw_networkx_edges(G, pos, edgelist=path_edges, ax=ax,
                                   edge_color="#e74c3c", width=3, alpha=0.9,
                                   arrows=True, arrowsize=12)
            nx.draw_networkx_nodes(G, pos, nodelist=path, ax=ax,
                                   node_color="#e74c3c", node_size=300)
            path_set = set(path)
            other = [n for n in all_nodes_list if n not in path_set]
        else:
            other = all_nodes_list

        nx.draw_networkx_nodes(G, pos, nodelist=other, ax=ax,
                               node_color="#3498db", node_size=200, alpha=0.5)

        label = PROFILE_LABELS.get(profile, profile)
        if path:
            title = (f"{mode}\n"
                     f"거리 {summary['total_distance_m']}m | "
                     f"계단 {summary['total_stairs']}칸\n"
                     f"W={summary['total_weight']:.1f}")
        else:
            title = f"{mode}\n경로 없음"
        ax.set_title(title, fontsize=11)
        ax.axis("off")

    plt.suptitle(f"모드 비교 | {label} | {start} -> {end}", fontsize=14)
    plt.tight_layout()
    safe_profile = profile.replace(" ", "_")
    save_path = os.path.join(OUTPUT_DIR, f"compare_modes_{safe_profile}.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Saved: {save_path}")
    return save_path


if __name__ == "__main__":
    start = "서관_시작노드"
    end = "서관_3층_열람실"

    print("=== 프로필별 경로 시각화 (빠른도착) ===")
    for p in PROFILES:
        visualize_path(p, "빠른도착", start, end)

    print("\n=== 프로필별 경로 비교 ===")
    visualize_profile_comparison(start, end)

    print("\n=== 모드 비교 (일반 보행자) ===")
    visualize_mode_comparison("일반", start, end)

    print("\n=== 전체 그래프 (일반, 빠른도착) ===")
    visualize_path("일반", "빠른도착", start, end,
                   save_path=os.path.join(OUTPUT_DIR, "graph_overview.png"))
