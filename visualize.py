"""
그래프 시각화 - NetworkX + matplotlib
"""
import os
import sqlite3
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from pathfinder import build_graph, find_shortest_path, score_to_accessibility

matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "goahead.db")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")


def get_node_positions():
    """DB에서 위경도 좌표 추출"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT node_id, latitude, longitude, name FROM node")
    pos = {}
    labels = {}
    for row in cur.fetchall():
        pos[row["node_id"]] = (row["longitude"], row["latitude"])
        labels[row["node_id"]] = f"{row['node_id']}\n{row['name']}"
    conn.close()
    return pos, labels


def visualize_all(profile="normal", save_path=None):
    """전체 그래프 + 최단경로 표시"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    G = build_graph(profile)
    pos, labels = get_node_positions()

    fig, ax = plt.subplots(1, 1, figsize=(16, 12))

    # 전체 엣지 (연한 회색)
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.15, edge_color="gray",
                           arrows=True, arrowsize=8, width=0.5)

    # 최단경로 (N001 -> N010)
    path, total, details = find_shortest_path("N001", "N010", profile)
    if path and len(path) > 1:
        path_edges = list(zip(path[:-1], path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, ax=ax,
                               edge_color="red", width=3, alpha=0.9,
                               arrows=True, arrowsize=15)
        # 경로상의 노드 강조
        nx.draw_networkx_nodes(G, pos, nodelist=path, ax=ax,
                               node_color="red", node_size=600, alpha=0.9)
    else:
        nx.draw_networkx_nodes(G, pos, ax=ax,
                               node_color="lightblue", node_size=400)

    # 나머지 노드
    other_nodes = [n for n in G.nodes() if n not in (path or [])]
    nx.draw_networkx_nodes(G, pos, nodelist=other_nodes, ax=ax,
                           node_color="lightblue", node_size=400, alpha=0.7)
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=7)

    score = score_to_accessibility(total) if path else 0
    ax.set_title(
        f"GoAhead 경로 시시뮬레이션\n"
        f"Profile: {profile}  |  N001 -> N010\n"
        f"Weight: {total:.2f}  |  Score: {score}/100",
        fontsize=14,
    )
    ax.axis("off")
    plt.tight_layout()

    if save_path is None:
        save_path = os.path.join(OUTPUT_DIR, f"graph_{profile}.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Saved: {save_path}")
    return save_path


def compare_profiles():
    """프로필별 경로 비교 시각화"""
    profiles = ["normal", "목발", "휠체어", "유아차", "시각장애_보조"]
    fig, axes = plt.subplots(1, len(profiles), figsize=(28, 6))

    pos, labels = get_node_positions()

    for ax, prof in zip(axes, profiles):
        G = build_graph(prof)
        path, total, _ = find_shortest_path("N001", "N010", prof)
        score = score_to_accessibility(total) if path else 0

        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.1, edge_color="gray",
                               arrows=True, arrowsize=5, width=0.3)

        if path and len(path) > 1:
            path_edges = list(zip(path[:-1], path[1:]))
            nx.draw_networkx_edges(G, pos, edgelist=path_edges, ax=ax,
                                   edge_color="red", width=2.5, alpha=0.9,
                                   arrows=True, arrowsize=10)
            nx.draw_networkx_nodes(G, pos, nodelist=path, ax=ax,
                                   node_color="red", node_size=300)
        else:
            nx.draw_networkx_nodes(G, pos, ax=ax,
                                   node_color="lightblue", node_size=200)

        other = [n for n in G.nodes() if n not in (path or [])]
        nx.draw_networkx_nodes(G, pos, nodelist=other, ax=ax,
                               node_color="lightblue", node_size=200, alpha=0.5)

        status = "X" if total == float("inf") else f"W={total:.1f}"
        ax.set_title(f"{prof}\n{status} | Score={score}", fontsize=10)
        ax.axis("off")

    plt.suptitle("프로별 최단경로 비교 (N001 -> N010)", fontsize=14)
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "compare_profiles.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Saved: {save_path}")


if __name__ == "__main__":
    profiles = ["normal", "목발", "휠체어", "유아차", "시각장애_보조"]
    for p in profiles:
        visualize_all(p)
    compare_profiles()
