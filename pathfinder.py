import sqlite3
import os
import networkx as nx

DB_PATH = os.path.join(os.path.dirname(__file__), "goahead.db")

PROFILES = ["일반", "휠체어", "목발", "유아차", "짐"]
MODES = ["빠른도착", "편하게"]

PROFILE_LABELS = {
    "일반": "일반 보행자",
    "휠체어": "휠체어 사용자",
    "목발": "목발 사용자",
    "유아차": "유아차 이용자",
    "짐": "무거운 짐 소지자",
}

STEP_HEIGHT_RANK = {"없음": 0, "미니": 1, "중간": 2, "높음": 3}


def _is_blocked(edge, profile):
    obs = edge.get("obstacle_info", "")
    if "사용중지" in obs:
        return True
    stairs = edge["stairs_count"]
    step = STEP_HEIGHT_RANK.get(edge.get("step_height", "없음"), 0)
    door = edge.get("door_type", "없음")

    if profile == "휠체어":
        if stairs > 0:
            return True
        if step >= 2:
            return True
        if door == "밀고당기는문":
            return True
    elif profile == "유아차":
        if stairs > 0:
            return True
        if step >= 1:
            return True
    return False


def _compute_weight(edge, profile, mode):
    dist = edge["distance_m"]
    stairs = edge["stairs_count"]
    step = STEP_HEIGHT_RANK.get(edge.get("step_height", "없음"), 0)
    door = edge.get("door_type", "없음")

    if mode == "빠른도착":
        return _weight_fast(dist, stairs, step, door, profile)
    else:
        return _weight_comfort(dist, stairs, step, door, profile)


def _weight_fast(dist, stairs, step, door, profile):
    if profile == "일반":
        w = dist + stairs * 1 + step * 2
        if door == "밀고당기는문":
            w += 3
        return w
    if profile == "휠체어":
        w = dist
        if door == "밀고당기는문":
            w += 50
        return w
    if profile == "목발":
        w = dist + stairs * 5 + step * 8
        if door == "밀고당기는문":
            w += 10
        return w
    if profile == "유아차":
        w = dist + step * 15
        if door == "밀고당기는문":
            w += 25
        return w
    if profile == "짐":
        w = dist + stairs * 3 + step * 5
        if door == "밀고당기는문":
            w += 20
        return w
    return dist


def _weight_comfort(dist, stairs, step, door, profile):
    if profile == "일반":
        w = dist + stairs * 8 + step * 5
        if door == "밀고당기는문":
            w += 10
        return w
    if profile == "휠체어":
        w = dist
        if door == "밀고당기는문":
            w += 80
        return w
    if profile == "목발":
        w = dist + stairs * 30 + step * 40
        if door == "밀고당기는문":
            w += 35
        return w
    if profile == "유아차":
        w = dist + step * 60
        if door == "밀고당기는문":
            w += 50
        return w
    if profile == "짐":
        w = dist + stairs * 15 + step * 20
        if door == "밀고당기는문":
            w += 35
        return w
    return dist


def build_graph(profile="일반", mode="빠른도착"):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM node")
    nodes = cur.fetchall()

    cur.execute("SELECT * FROM edge")
    edges = cur.fetchall()
    conn.close()

    G = nx.DiGraph()

    for row in nodes:
        G.add_node(row["node_id"], name=row["name"], type=row["type"])

    for e in edges:
        ed = dict(e)
        if _is_blocked(ed, profile):
            continue
        w = _compute_weight(ed, profile, mode)
        G.add_edge(
            ed["start_node"], ed["end_node"],
            weight=w,
            distance_m=ed["distance_m"],
            stairs_count=ed["stairs_count"],
            step_height=ed["step_height"],
            door_type=ed["door_type"],
            obstacle_info=ed["obstacle_info"],
        )
        G.add_edge(
            ed["end_node"], ed["start_node"],
            weight=w,
            distance_m=ed["distance_m"],
            stairs_count=ed["stairs_count"],
            step_height=ed["step_height"],
            door_type=ed["door_type"],
            obstacle_info=ed["obstacle_info"],
        )

    return G


def find_shortest_path(start, end, profile="일반", mode="빠른도착"):
    G = build_graph(profile, mode)
    try:
        path = nx.dijkstra_path(G, start, end, weight="weight")
    except nx.NetworkXNoPath:
        return None, float("inf"), [], {"path_length": 0, "total_distance_m": 0, "total_stairs": 0, "total_weight": float("inf")}
    except nx.NodeNotFound as ex:
        return None, float("inf"), [str(ex)], {"path_length": 0, "total_distance_m": 0, "total_stairs": 0, "total_weight": float("inf")}

    total_weight = nx.dijkstra_path_length(G, start, end, weight="weight")

    details = []
    total_distance = 0
    total_stairs = 0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        ed = G[u][v]
        total_distance += ed["distance_m"]
        total_stairs += ed["stairs_count"]
        details.append({
            "from": u,
            "to": v,
            "from_name": G.nodes[u].get("name", ""),
            "to_name": G.nodes[v].get("name", ""),
            "distance_m": ed["distance_m"],
            "stairs_count": ed["stairs_count"],
            "step_height": ed["step_height"],
            "door_type": ed["door_type"],
            "obstacle_info": ed["obstacle_info"],
            "weight": round(ed["weight"], 2),
        })

    summary = {
        "path_length": len(path),
        "total_distance_m": round(total_distance, 2),
        "total_stairs": total_stairs,
        "total_weight": round(total_weight, 2),
    }
    return path, total_weight, details, summary


def find_top_k_paths(start, end, profile="일반", mode="빠른도착", k=3):
    G = build_graph(profile, mode)
    try:
        paths_gen = nx.shortest_simple_paths(G, start, end, weight="weight")
        results = []
        for i, path in enumerate(paths_gen):
            if i >= k:
                break
            tw = sum(
                G[path[j]][path[j + 1]]["weight"]
                for j in range(len(path) - 1)
            )
            total_dist = sum(
                G[path[j]][path[j + 1]]["distance_m"]
                for j in range(len(path) - 1)
            )
            total_stairs = sum(
                G[path[j]][path[j + 1]]["stairs_count"]
                for j in range(len(path) - 1)
            )
            details = []
            for j in range(len(path) - 1):
                u, v = path[j], path[j + 1]
                ed = G[u][v]
                details.append({
                    "from": u, "to": v,
                    "from_name": G.nodes[u].get("name", ""),
                    "to_name": G.nodes[v].get("name", ""),
                    "distance_m": ed["distance_m"],
                    "stairs_count": ed["stairs_count"],
                    "step_height": ed["step_height"],
                    "door_type": ed["door_type"],
                    "obstacle_info": ed["obstacle_info"],
                    "weight": round(ed["weight"], 2),
                })
            results.append({
                "path": path,
                "total_weight": round(tw, 2),
                "details": details,
                "summary": {
                    "path_length": len(path),
                    "total_distance_m": round(total_dist, 2),
                    "total_stairs": total_stairs,
                    "total_weight": round(tw, 2),
                },
            })
        return results
    except nx.NetworkXNoPath:
        return []


def get_all_nodes():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT node_id, name, type FROM node ORDER BY node_id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_all_edges():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM edge ORDER BY edge_id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


if __name__ == "__main__":
    nodes = get_all_nodes()
    print("=== Nodes ===")
    for n in nodes:
        print(f"  {n['node_id']} ({n['type']})")

    print("\n=== Profile/Mode Simulation ===")

    test_routes = [
        ("서관_시작노드", "서관_엘리베이터"),
        ("서관_시작노드", "서관_쪽계단앞"),
        ("동관_시작노드", "동관_엘리베이터"),
        ("동관_주차장쪽계단", "열람실_입구(경로1_중간쪽계단)"),
        ("동관_주차장쪽계단", "열람실_입구(경로3_엘리베이터)"),
        ("동관_쪽길", "열람실_입구(경로5_1층계단)"),
    ]

    for start, end in test_routes:
        print(f"\n{'='*60}")
        print(f"  {start} -> {end}")
        print(f"{'='*60}")
        for profile in PROFILES:
            for mode in MODES:
                path, tw, details, summary = find_shortest_path(start, end, profile, mode)
                label = f"[{PROFILE_LABELS[profile]}] [{mode}]"
                if path is None:
                    print(f"  {label}: 경로 없음")
                else:
                    print(f"  {label}: weight={tw:.1f} dist={summary['total_distance_m']}m "
                          f"stairs={summary['total_stairs']}개 path={len(path)}개 노드")
                    print(f"    {' -> '.join(path)}")
