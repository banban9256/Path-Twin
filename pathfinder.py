import sqlite3
import os
import networkx as nx

DB_PATH = os.path.join(os.path.dirname(__file__), "goahead.db")

# ─── 속도 계수 (m/min 기준, 이동시간 계산용) ───
BASE_SPEED = 80  # 보행자 기본 속도 약 80m/min (4.8km/h)

SPEED_FACTOR = {
    "normal": 1.0,
    "목발": 0.5,
    "휠체어": 0.3,
    "유아차": 0.7,
    "시각장애_보조": 0.6,
}

# ─── 엣지별 패널티 계수 ───
# 반환값: (이동시간 계수, 추가 페널티 점수)
def _slope_penalty(slope_type, profile):
    factors = {
        "normal":       {"평지": 1.0, "오르막": 1.3, "내리막": 1.1},
        "목발":         {"평지": 1.0, "오르막": 4.0, "내리막": 1.5},
        "휠체어":       {"평지": 1.0, "오르막": 8.0, "내리막": 2.0},
        "유아차":       {"평지": 1.0, "오르막": 2.0, "내리막": 1.3},
        "시각장애_보조": {"평지": 1.0, "오르막": 1.5, "내리막": 1.2},
    }
    return factors.get(profile, factors["normal"]).get(slope_type, 1.0)


def _stairs_penalty(stairs_count, profile):
    if stairs_count == 0:
        return 1.0, 0
    p = profile
    if p == "휠체어":
        return float("inf"), float("inf")  # 완전 차단
    if p == "목발":
        return 1.0, stairs_count * 100
    if p == "유아차":
        return 1.0, stairs_count * 50
    if p == "시각장애_보조":
        return 1.0, stairs_count * 30
    return 1.0 + stairs_count * 0.1, stairs_count * 10  # normal


def _crosswalk_penalty(crosswalk, profile):
    if not crosswalk:
        return 0
    p = profile
    if p == "시각장애_보조":
        return 15  # 신호 확인 필요
    if p == "휠체어":
        return 5
    if p == "유아차":
        return 8
    return 3


def _width_penalty(sidebar_width, profile):
    factors = {
        "normal":       {"좁음": 1.2, "보통": 1.0, "넓음": 1.0},
        "휠체어":       {"좁음": 3.0, "보통": 1.2, "넓음": 1.0},
        "유아차":       {"좁음": 10.0, "보통": 1.0, "넓음": 1.0},
        "목발":         {"좁음": 1.5, "보통": 1.0, "넓음": 1.0},
        "시각장애_보조": {"좁음": 2.0, "보통": 1.0, "넓음": 1.0},
    }
    return factors.get(profile, factors["normal"]).get(sidebar_width, 1.0)


def _curb_penalty(curb, profile):
    if not curb:
        return 0
    if profile == "휠체어":
        return 20
    if profile == "유아차":
        return 20
    if profile == "목발":
        return 5
    return 2


def _confidence_penalty(confidence):
    return {
        "직접조사": 0,
        "가상데이터": 3,
        "사용자 신고": 5,
    }.get(confidence, 0)


# ─── 메인 가중치 함수 ───
def compute_edge_weight(edge_data, profile="normal"):
    """
    엣지 데이터(dict)와 사용자 프로필을 받아 최종 가중치(점수)를 반환.
    반환: (weight, breakdown_dict)
    """
    dist = edge_data["distance_m"]
    speed_factor = SPEED_FACTOR.get(profile, 1.0)

    # 이동시간 = 거리 / 속도 (분)
    travel_time = dist / (BASE_SPEED * speed_factor)

    # 경사 페널티 (이동시간에 곱해짐)
    slope_factor = _slope_penalty(edge_data["slope_type"], profile)

    # 계단 페널티
    stairs_time_factor, stairs_flat_penalty = _stairs_penalty(
        edge_data["stairs_count"], profile
    )

    # 횡단보도 페널티
    crosswalk_p = _crosswalk_penalty(edge_data["crosswalk"], profile)

    # 보도 폭 페널티
    width_factor = _width_penalty(edge_data["sidewalk_width"], profile)

    # 턱 페널티
    curb_p = _curb_penalty(edge_data["curb"], profile)

    # 신뢰도 페널티
    conf_p = _confidence_penalty(edge_data["confidence"])

    # 최종 가중치
    base = travel_time * slope_factor * stairs_time_factor * width_factor
    penalty = crosswalk_p + curb_p + conf_p + stairs_flat_penalty
    weight = base + penalty

    breakdown = {
        "travel_time_min": round(travel_time, 2),
        "slope_factor": slope_factor,
        "stairs_time_factor": stairs_time_factor,
        "width_factor": width_factor,
        "crosswalk_penalty": crosswalk_p,
        "curb_penalty": curb_p,
        "confidence_penalty": conf_p,
        "stairs_flat_penalty": stairs_flat_penalty,
        "total_weight": round(weight, 2),
    }

    return weight, breakdown


# ─── 그래프 빌드 ───
def build_graph(profile="normal"):
    """DB에서 엣지를 읽어 NetworkX 그래프构建. 무한 가중치 엣지는 제외."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM edge")
    edges = cur.fetchall()
    conn.close()

    G = nx.DiGraph()

    # 노드 먼저 추가 (위도/경도)
    conn2 = sqlite3.connect(DB_PATH)
    conn2.row_factory = sqlite3.Row
    cur2 = conn2.cursor()
    cur2.execute("SELECT * FROM node")
    for row in cur2.fetchall():
        G.add_node(row["node_id"],
                   name=row["name"],
                   type=row["type"],
                   latitude=row["latitude"],
                   longitude=row["longitude"])
    conn2.close()

    for e in edges:
        edge_data = dict(e)
        weight, breakdown = compute_edge_weight(edge_data, profile)
        if weight == float("inf"):
            continue  # 접근 불가 엣지 제외
        G.add_edge(
            e["start_node"], e["end_node"],
            weight=weight,
            **edge_data,
            breakdown=breakdown,
        )
        # 양방향 보도 추가 (계단은 방향 다를 수 있으나 단순화)
        G.add_edge(
            e["end_node"], e["start_node"],
            weight=weight,
            **edge_data,
            breakdown=breakdown,
        )

    return G


# ─── 경로 탐색 ───
def find_shortest_path(start, end, profile="normal"):
    """
    다익스트라 최단경로 탐색.
    반환: (path_list, total_weight, detail_list)
    """
    G = build_graph(profile)
    try:
        path = nx.dijkstra_path(G, start, end, weight="weight")
    except nx.NetworkXNoPath:
        return None, float("inf"), []
    except nx.NodeNotFound as ex:
        return None, float("inf"), [str(ex)]

    total_weight = nx.dijkstra_path_length(G, start, end, weight="weight")

    details = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        ed = G[u][v]
        details.append({
            "from": u,
            "to": v,
            "from_name": G.nodes[u].get("name", ""),
            "to_name": G.nodes[v].get("name", ""),
            **ed["breakdown"],
        })

    return path, total_weight, details


def find_top_k_paths(start, end, profile="normal", k=3):
    """상위 k개 경로 반환 (Yen's K-shortest paths)"""
    G = build_graph(profile)
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
            details = []
            for j in range(len(path) - 1):
                u, v = path[j], path[j + 1]
                ed = G[u][v]
                details.append({
                    "from": u, "to": v,
                    "from_name": G.nodes[u].get("name", ""),
                    "to_name": G.nodes[v].get("name", ""),
                    **ed["breakdown"],
                })
            results.append((path, tw, details))
        return results
    except nx.NetworkXNoPath:
        return []


# ─── 점수 해석 ───
def score_to_accessibility(total_weight):
    """가중치를 0~100 접근성 점수로 환산 (낮을수록 좋음)"""
    if total_weight == float("inf"):
        return 0
    # 가중치가 0이면 만점, 60(약 1시간) 이상이면 0점
    score = max(0, 100 * (1 - total_weight / 60))
    return round(score, 1)


# ─── CLI ───
if __name__ == "__main__":
    profiles = ["normal", "목발", "휠체어", "유아차", "시각장애_보조"]
    routes = [("N001", "N010", "정문->엘리베이터동"),
              ("N001", "N020", "정문->후문 (전체)")]

    for start, end, label in routes:
        print(f"\n\n{'#'*60}")
        print(f"  ROUTE: {label}  ({start} -> {end})")
        print(f"{'#'*60}")
        for prof in profiles:
            print(f"\n  --- Profile: {prof} ---")
            path, total, details = find_shortest_path(start, end, prof)
            if path is None:
                print("    [X] 경로를 찾을 수 없습니다.")
                continue
            print(f"    Path: {' -> '.join(path)}")
            print(f"    Weight: {total:.2f}  |  Score: {score_to_accessibility(total)}/100")
            for d in details:
                print(f"      {d['from']}({d['from_name']}) -> {d['to']}({d['to_name']})  "
                      f"w={d['total_weight']:.2f}  "
                      f"slope={d['slope_factor']}x  "
                      f"stairs={d['stairs_time_factor']}x  "
                      f"cw=+{d['crosswalk_penalty']}  "
                      f"curb=+{d['curb_penalty']}")
