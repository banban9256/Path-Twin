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

# ─── 캐시 ───
_cached_nodes = None
_cached_edges = None


def _load_data():
    global _cached_nodes, _cached_edges
    if _cached_nodes is not None:
        return _cached_nodes, _cached_edges

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM node")
    _cached_nodes = [dict(row) for row in cur.fetchall()]

    cur.execute("SELECT * FROM edge")
    _cached_edges = [dict(row) for row in cur.fetchall()]

    conn.close()
    return _cached_nodes, _cached_edges


def clear_cache():
    global _cached_nodes, _cached_edges
    _cached_nodes = None
    _cached_edges = None


# ─── 차단 판정 (계단만 차단) ───
def _is_blocked(edge, profile):
    stairs = edge["stairs_count"]
    if profile == "휠체어" and stairs > 0:
        return True
    if profile == "유아차" and stairs > 0:
        return True
    return False


# ─── 가중치 딕셔너리 ───
WALK_SPEED = 80.0  # m/min
ELEVATOR_COST = 0.5  # min per floor

STAIR_COST_PER_STEP = {
    "일반": 0.025,
    "휠체어": float("inf"),
    "목발": 0.065,
    "유아차": float("inf"),
    "짐": 0.035,
}

STEP_HEIGHT_COST = {
    "일반":   {"없음": 0.0,  "미니": 0.05, "중간": 0.15},
    "휠체어":  {"없음": 0.0,  "미니": 0.15, "중간": 0.40},
    "목발":   {"없음": 0.0,  "미니": 0.12, "중간": 0.35},
    "유아차":  {"없음": 0.0,  "미니": 0.20, "중간": 0.50},
    "짐":     {"없음": 0.0,  "미니": 0.05, "중간": 0.15},
}

DOOR_COST = {
    "일반": {
        "없음": 0.0,
        "밀고당기관문 1번": 0.10,
        "밀고당기관문 2번": 0.20,
        "밀고당기관문 1번 + 자동문 1번": 0.05,
    },
    "휠체어": {
        "없음": 0.0,
        "밀고당기관문 1번": 0.30,
        "밀고당기관문 2번": 0.50,
        "밀고당기관문 1번 + 자동문 1번": 0.10,
    },
    "목발": {
        "없음": 0.0,
        "밀고당기관문 1번": 0.15,
        "밀고당기관문 2번": 0.30,
        "밀고당기관문 1번 + 자동문 1번": 0.08,
    },
    "유아차": {
        "없음": 0.0,
        "밀고당기관문 1번": 0.12,
        "밀고당기관문 2번": 0.25,
        "밀고당기관문 1번 + 자동문 1번": 0.06,
    },
    "짐": {
        "없음": 0.0,
        "밀고당기관문 1번": 0.12,
        "밀고당기관문 2번": 0.25,
        "밀고당기관문 1번 + 자동문 1번": 0.06,
    },
}

COMFORT_MULTIPLIER = 2.5


# ─── 가중치 계산 ───
def _compute_weight(edge, profile, mode):
    dist = edge["distance_m"]
    stairs = edge["stairs_count"]
    step = edge["step_height"]
    door = edge["door_type"]
    etype = edge["edge_type"]

    if etype == "엘리베이터":
        base = ELEVATOR_COST
    elif stairs > 0:
        base = stairs * STAIR_COST_PER_STEP[profile]
    else:
        base = dist / WALK_SPEED

    comfort = COMFORT_MULTIPLIER if mode == "편하게" else 1.0
    step_p = STEP_HEIGHT_COST[profile].get(step, 0.0)
    door_p = DOOR_COST[profile].get(door, 0.0)

    return base + (step_p + door_p) * comfort


# ─── 그래프 빌드 (캐시에서 weight만 재계산) ───
def build_graph(profile="일반", mode="빠른도착"):
    nodes, edges = _load_data()
    G = nx.DiGraph()

    for node in nodes:
        G.add_node(node["node_id"], name=node["name"], type=node["type"])

    for edge in edges:
        w = _compute_weight(edge, profile, mode)
        if w == float("inf"):
            continue
        attrs = {k: v for k, v in edge.items()
                 if k not in ("edge_id", "start_node", "end_node")}
        G.add_edge(edge["start_node"], edge["end_node"], weight=w, **attrs)
        G.add_edge(edge["end_node"], edge["start_node"], weight=w, **attrs)

    return G


# ─── 빈 결과 템플릿 ───
_EMPTY_SUMMARY = {
    "path_length": 0,
    "total_distance_m": 0,
    "total_stairs": 0,
    "total_weight": float("inf"),
}


# ─── 경로 탐색 ───
def find_shortest_path(start, end, profile="일반", mode="빠른도착"):
    G = build_graph(profile, mode)

    if start not in G or end not in G:
        return None, float("inf"), [], dict(_EMPTY_SUMMARY)

    try:
        path = nx.dijkstra_path(G, start, end, weight="weight")
    except nx.NetworkXNoPath:
        return None, float("inf"), [], dict(_EMPTY_SUMMARY)

    total_weight = nx.path_weight(G, path, weight="weight")

    details = []
    total_distance = 0.0
    total_stairs = 0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        ed = G[u][v]
        total_distance += ed.get("distance_m", 0)
        total_stairs += ed.get("stairs_count", 0)
        details.append({
            "from": u,
            "to": v,
            "edge_type": ed.get("edge_type", ""),
            "distance_m": ed.get("distance_m", 0),
            "stairs_count": ed.get("stairs_count", 0),
            "step_height": ed.get("step_height", ""),
            "door_type": ed.get("door_type", ""),
            "obstacle_info": ed.get("obstacle_info", ""),
            "weight": round(ed["weight"], 4),
        })

    summary = {
        "path_length": len(path),
        "total_distance_m": round(total_distance, 2),
        "total_stairs": total_stairs,
        "total_weight": round(total_weight, 4),
    }
    return path, total_weight, details, summary


def find_top_k_paths(start, end, profile="일반", mode="빠른도착", k=3):
    G = build_graph(profile, mode)

    if start not in G or end not in G:
        return []

    try:
        results = []
        for i, path in enumerate(nx.shortest_simple_paths(G, start, end, weight="weight")):
            if i >= k:
                break
            tw = nx.path_weight(G, path, weight="weight")
            total_dist = sum(G[path[j]][path[j + 1]].get("distance_m", 0)
                             for j in range(len(path) - 1))
            total_stairs = sum(G[path[j]][path[j + 1]].get("stairs_count", 0)
                               for j in range(len(path) - 1))
            details = []
            for j in range(len(path) - 1):
                u, v = path[j], path[j + 1]
                ed = G[u][v]
                details.append({
                    "from": u, "to": v,
                    "edge_type": ed.get("edge_type", ""),
                    "distance_m": ed.get("distance_m", 0),
                    "stairs_count": ed.get("stairs_count", 0),
                    "step_height": ed.get("step_height", ""),
                    "door_type": ed.get("door_type", ""),
                    "obstacle_info": ed.get("obstacle_info", ""),
                    "weight": round(ed["weight"], 4),
                })
            results.append({
                "path": path,
                "total_weight": round(tw, 4),
                "details": details,
                "summary": {
                    "path_length": len(path),
                    "total_distance_m": round(total_dist, 2),
                    "total_stairs": total_stairs,
                    "total_weight": round(tw, 4),
                },
            })
        return results
    except nx.NetworkXNoPath:
        return []


# ─── 유틸리티 ───
def get_all_nodes():
    nodes, _ = _load_data()
    return [{"node_id": n["node_id"], "name": n["name"], "type": n["type"]}
            for n in nodes]


def get_all_edges():
    _, edges = _load_data()
    return [dict(e) for e in edges]


# ─── CLI ───
if __name__ == "__main__":
    nodes = get_all_nodes()
    print(f"=== Nodes ({len(nodes)}) ===")
    for n in nodes:
        print(f"  {n['node_id']} ({n['type']})")

    test_routes = [
        ("서관_시작노드", "3층_열람실_입구"),
        ("동관_시작노드", "3층_열람실_입구"),
        ("주차장쪽_시작노드", "3층_열람실_입구"),
        ("쪽길_시작노드(개구멍)", "3층_열람실_입구"),
    ]

    for start, end in test_routes:
        print(f"\n{'='*60}")
        print(f"  {start}  ->  {end}")
        print(f"{'='*60}")
        for profile in PROFILES:
            for mode in MODES:
                path, tw, details, summary = find_shortest_path(start, end, profile, mode)
                label = f"[{PROFILE_LABELS[profile]}] [{mode}]"
                if path is None:
                    print(f"  {label}: 경로 없음")
                else:
                    print(f"  {label}: weight={tw:.4f}  "
                          f"dist={summary['total_distance_m']}m  "
                          f"stairs={summary['total_stairs']}칸  "
                          f"nodes={summary['path_length']}")
                    print(f"    {' -> '.join(path)}")
