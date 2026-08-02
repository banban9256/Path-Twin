import sqlite3
import os
import networkx as nx

# 데이터베이스 경로를 프로젝트 루트 디렉토리의 goahead.db로 설정
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "goahead.db")

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


# ─── 가중치 매트릭스 (독립 변수화) ───
WALK_SPEEDS = {
    "일반": 80.0,
    "휠체어": 55.0,
    "목발": 40.0,
    "유아차": 55.0,
    "짐": 60.0,
}

ELEVATOR_COST = 0.5  # min per floor

STAIR_WEIGHT_MATRIX = {
    "일반": {
        "빠른도착": 1.0,
        "편하게": 2.5
    },
    "목발": {
        "빠른도착": 3.0,
        "편하게": float("inf")
    },
    "짐": {
        "빠른도착": 2.0,
        "편하게": 4.0
    },
    "휠체어": {
        "빠른도착": float("inf"),
        "편하게": float("inf")
    },
    "유아차": {
        "빠른도착": float("inf"),
        "편하게": float("inf")
    }
}

ELEVATOR_WAIT_MATRIX = {
    "일반": {
        "빠른도착": 3.0,  # 대기 시간 페널티 적용 (어지간하면 계단 선호)
        "편하게": 0.2
    },
    "목발": {
        "빠른도착": 0.8,
        "편하게": 0.2
    },
    "짐": {
        "빠른도착": 1.5,
        "편하게": 0.2
    },
    "휠체어": {
        "빠른도착": 0.5,
        "편하게": 0.5
    },
    "유아차": {
        "빠른도착": 0.5,
        "편하게": 0.5
    }
}

STEP_WEIGHT_MATRIX = {
    "일반":   {"없음": 0.0,  "미니": 0.05, "중간": 0.15},
    "휠체어":  {"없음": 0.0,  "미니": float("inf"), "중간": float("inf")},
    "목발":   {"없음": 0.0,  "미니": 0.12, "중간": 0.35},
    "유아차":  {"없음": 0.0,  "미니": float("inf"), "중간": float("inf")},
    "짐":     {"없음": 0.0,  "미니": 0.05, "중간": 0.15},
}

DOOR_WEIGHT_MATRIX = {
    "일반": {
        "없음": 0.0,
        "밀고당기관문 1번": 0.10,
        "밀고당기관문 2번": 0.20,
        "밀고당기관문 1번 + 자동문 1번": 0.05,
        "회전문": 0.10,
        "자동문": 0.0,
        "밀고 당기는 문": 0.10
    },
    "휠체어": {
        "없음": 0.0,
        "밀고당기관문 1번": 3.0,
        "밀고당기관문 2번": 5.0,
        "밀고당기관문 1번 + 자동문 1번": 1.0,
        "회전문": float("inf"),
        "자동문": 1.0,
        "밀고 당기는 문": 3.0
    },
    "목발": {
        "없음": 0.0,
        "밀고당기관문 1번": 0.15,
        "밀고당기관문 2번": 0.30,
        "밀고당기관문 1번 + 자동문 1번": 0.08,
        "회전문": 0.50,
        "자동문": 0.08,
        "밀고 당기는 문": 0.15
    },
    "유아차": {
        "없음": 0.0,
        "밀고당기관문 1번": 3.0,
        "밀고당기관문 2번": 5.0,
        "밀고당기관문 1번 + 자동문 1번": 1.0,
        "회전문": float("inf"),
        "자동문": 1.0,
        "밀고 당기는 문": 3.0
    },
    "짐": {
        "없음": 0.0,
        "밀고당기관문 1번": 0.12,
        "밀고당기관문 2번": 0.25,
        "밀고당기관문 1번 + 자동문 1번": 0.06,
        "회전문": 0.20,
        "자동문": 0.06,
        "밀고 당기는 문": 0.12
    },
}

COMFORT_MULTIPLIER = 150.0


# ─── 가중치 계산 ───
def _compute_weight(edge, profile, mode):
    start = edge.get("start_node", "")
    end = edge.get("end_node", "")

    # 루프 방지: 시작 노드와 끝 노드가 동일한 불필요한 왕복 엣지의 비용은 무한대로 처리
    if start == end:
        return float("inf")

    dist = edge["distance_m"]
    stairs = edge["stairs_count"]
    step = edge["step_height"]
    door = edge["door_type"]
    etype = edge["edge_type"]
    obstacle = edge.get("obstacle_info", "")

    # 열람실 긴계단 식별
    is_long_stair = (
        {start, end} == {"열람실_긴계단_아래(동관쪽길)", "3층_열람실_입구"} or
        "가장 긴 계단" in obstacle
    )

    # 1. 엘리베이터인 경우 가중치 계산
    if etype == "엘리베이터":
        # 엘리베이터 이용 대기 비용 + 탑승 비용
        wait_cost = ELEVATOR_WAIT_MATRIX[profile][mode]
        base = wait_cost + ELEVATOR_COST

    # 2. 계단이 있는 경우 가중치 계산
    elif stairs > 0:
        # 목발 사용자 빠른 모드: 계단은 최대 2칸까지만 허용, 그 이상은 우회
        if profile == "목발" and mode == "빠른도착" and stairs > 2:
            return float("inf")

        # 계단 가중치 룩업
        stair_weight = STAIR_WEIGHT_MATRIX[profile][mode]
        if stair_weight == float("inf"):
            return float("inf")

        base = stairs * stair_weight

        # 열람실 긴계단 추가 페널티 부여 (편하게 모드에서만 적용)
        if is_long_stair and mode == "편하게":
            base += 500.0

    # 3. 평지인 경우
    else:
        # 거리 * 거리비용 (거리비용 = 1.0 / 보행속도)
        speed = WALK_SPEEDS.get(profile, 80.0)
        base = dist / speed

        # 편하게 모드일 때 구름다리 -> 엘리베이터 연계를 위해 계단앞으로 빠지는 우회 복도에 페널티 부여
        if mode == "편하게" and {start, end} == {"서관_2층_계단앞", "서관_2층_엘리베이터앞"}:
            base += 200.0

    # 턱 및 문 통과 가중치
    step_weight = STEP_WEIGHT_MATRIX[profile].get(step, 0.0)
    door_weight = DOOR_WEIGHT_MATRIX[profile].get(door, 0.0)

    # 턱이나 문 통과가 불가능한 경우 차단
    if step_weight == float("inf") or door_weight == float("inf"):
        return float("inf")

    comfort = COMFORT_MULTIPLIER if mode == "편하게" else 1.0

    return base + (step_weight + door_weight) * comfort


# ─── 그래프 빌드 (캐시에서 weight만 재계산) ───
def build_graph(profile="일반", mode="빠른도착"):
    nodes, edges = _load_data()
    G = nx.DiGraph()

    for node in nodes:
        G.add_node(node["node_id"], name=node["name"], type=node["type"])

    # 1. 기존 데이터베이스 간선 추가 및 특정 데이터 덮어쓰기
    for edge in edges:
        start = edge["start_node"]
        end = edge["end_node"]

        # 주차장 계단위 <-> 중간쪽계단위 간선 동일 층 평지화 (수직 계단 오류 교정 및 연계 복원)
        if {start, end} == {"주차장_계단위", "중간쪽계단_위"}:
            edge["stairs_count"] = 0
            edge["edge_type"] = "외부보행로"

        # 쪽길 및 열람실 외부 계단 데이터 덮어쓰기
        if {start, end} == {"쪽계단_아래", "3층_쪽계단위"}:
            edge["stairs_count"] = 51
        elif {start, end} == {"중간쪽계단_위", "3층_쪽계단위"}:
            edge["stairs_count"] = 24
        
        # 서관 내부/외부 계단 및 직접 통로 데이터 덮어쓰기
        elif {start, end} == {"서관_시작노드", "서관_1층_문앞(중앙)"}:
            edge["stairs_count"] = 3
            edge["distance_m"] = 4.5
        elif {start, end} == {"서관_시작노드", "서관_1층_문앞(장애인)"}:
            edge["distance_m"] = 8.0
        elif {start, end} == {"서관_1층_계단앞", "서관_2층_계단앞"}:
            edge["stairs_count"] = 24
        elif {start, end} == {"서관_2층_계단앞", "서관_3층_계단앞"}:
            edge["stairs_count"] = 24

        # 동관 내부/외부 계단 및 직접 통로 데이터 덮어쓰기
        elif {start, end} == {"동관_시작노드", "동관_1층_문앞(중앙)"}:
            edge["stairs_count"] = 2
            edge["distance_m"] = 4.5
        elif {start, end} == {"동관_1층_계단앞", "동관_2층_계단앞"}:
            edge["stairs_count"] = 24
        elif {start, end} == {"동관_2층_계단앞", "동관_3층_계단앞"}:
            edge["stairs_count"] = 24
        elif {start, end} == {"동관_3층_계단앞", "동관_4층_계단앞"}:
            edge["stairs_count"] = 23

        w = _compute_weight(edge, profile, mode)
        if w == float("inf"):
            continue
        attrs = {k: v for k, v in edge.items()
                 if k not in ("edge_id", "start_node", "end_node")}
        G.add_edge(edge["start_node"], edge["end_node"], weight=w, **attrs)
        G.add_edge(edge["end_node"], edge["start_node"], weight=w, **attrs)

    # 2. 쪽길 입구 평지 우회 및 서관 우회 엣지 수동 주입
    bypass_edges = [
        # 쪽길 동관/서관 우회로
        {
            "start_node": "동관_시작노드",
            "end_node": "쪽길_시작노드(개구멍)",
            "distance_m": 25.48,
            "stairs_count": 0,
            "step_height": "없음",
            "door_type": "없음",
            "edge_type": "외부보행로",
            "obstacle_info": "동관 쪽길 우회로"
        },
        {
            "start_node": "서관_시작노드",
            "end_node": "쪽길_시작노드(개구멍)",
            "distance_m": 150.0,
            "stairs_count": 0,
            "step_height": "없음",
            "door_type": "없음",
            "edge_type": "외부보행로",
            "obstacle_info": "서관 쪽길 우회로"
        },
        # 신규 서관 우회 경로 데이터 반영 (방안 A)
        # 서관 시작노드 → 1층 열람실 계단(서관_1층_계단앞)
        # 거리: 150.0
        {
            "start_node": "서관_시작노드",
            "end_node": "서관_1층_계단앞",
            "distance_m": 150.0,
            "stairs_count": 0,
            "step_height": "없음",
            "door_type": "없음",
            "edge_type": "외부보행로",
            "obstacle_info": "서관 1층 우회로"
        },
        # 1층 열람실 계단(서관_1층_계단앞) → 2층 열람실 계단(서관_2층_계단앞) (계단: 27칸)
        # 기본 24칸을 우회 시 27칸으로 덮어씀
        {
            "start_node": "서관_1층_계단앞",
            "end_node": "서관_2층_계단앞",
            "distance_m": 0.0,
            "stairs_count": 27,
            "step_height": "미니",
            "door_type": "없음",
            "edge_type": "내부계단",
            "obstacle_info": "서관 중앙 계단(우회)"
        },
        # 2층 열람실 계단(서관_2층_계단앞) → 2층 엘리베이터(서관_2층_엘리베이터앞)
        # 거리: 27.63 + 10.97 + 3.15 + 17.61 = 59.36
        {
            "start_node": "서관_2층_계단앞",
            "end_node": "서관_2층_엘리베이터앞",
            "distance_m": 59.36,
            "stairs_count": 0,
            "step_height": "없음",
            "door_type": "없음",
            "edge_type": "실내복도",
            "obstacle_info": "서관 2층 우회 복도"
        },
        # 중앙 쪽계단 방향성/층수 정합성 엣지 (쪽계단_아래 <-> 중간쪽계단_위)
        # 계단 수: 23칸
        {
            "start_node": "쪽계단_아래",
            "end_node": "중간쪽계단_위",
            "distance_m": 12.44,
            "stairs_count": 23,
            "step_height": "없음",
            "door_type": "없음",
            "edge_type": "외부계단",
            "obstacle_info": "중앙 쪽계단"
        }
    ]

    for edge in bypass_edges:
        w = _compute_weight(edge, profile, mode)
        if w == float("inf"):
            continue
        attrs = {k: v for k, v in edge.items()
                 if k not in ("start_node", "end_node")}
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
        fallback = find_fallback_path(start, end, profile, mode)
        if fallback:
            return fallback["path"], fallback["total_weight"], fallback["details"], fallback["summary"]
        return None, float("inf"), [], dict(_EMPTY_SUMMARY)

    try:
        path = nx.dijkstra_path(G, start, end, weight="weight")
    except nx.NetworkXNoPath:
        fallback = find_fallback_path(start, end, profile, mode)
        if fallback:
            return fallback["path"], fallback["total_weight"], fallback["details"], fallback["summary"]
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


def find_fallback_path(start, end, profile="일반", mode="빠른도착"):
    # Step 1: 일반 조건으로 가장 가까운 엘리베이터 노드 찾기
    G_general = build_graph(profile="일반", mode="빠른도착")
    
    # 만약 profile이 교통약자(휠체어, 유아차, 목발)라면 Fallback 탐색에서도 계단을 완전 차단
    # (목발의 빠른도착 모드 계단 허용 조건은 최대 2칸 이하인 경우만 적용)
    if profile in ("휠체어", "유아차", "목발"):
        edges_to_remove = []
        for u, v, d in G_general.edges(data=True):
            stairs = d.get("stairs_count", 0)
            if stairs > 0:
                if profile == "목발" and mode == "빠른도착" and stairs <= 2:
                    continue
                edges_to_remove.append((u, v))
        G_general.remove_edges_from(edges_to_remove)
    
    # 그래프 상에 엘리베이터 타입의 노드 찾기
    elevator_nodes = [n for n, attr in G_general.nodes(data=True) if attr.get("type") == "엘리베이터"]
    
    if start not in G_general or not elevator_nodes:
        return None
        
    try:
        lengths, paths = nx.single_source_dijkstra(G_general, start, weight="weight")
    except Exception:
        return None
        
    # 엘리베이터 노드들 중 갈 수 있는 것들을 가중치 오름차순으로 정렬
    valid_elevators = []
    for ev in elevator_nodes:
        if ev in lengths and ev in paths:
            valid_elevators.append((lengths[ev], ev, paths[ev]))
            
    valid_elevators.sort(key=lambda x: x[0])
    
    # Step 2: 원래 조건으로 엘리베이터에서 목적지까지의 2차 경로 탐색
    G_limit = build_graph(profile=profile, mode=mode)
    
    if end not in G_limit:
        return None
        
    for dist, ev, path1 in valid_elevators:
        if ev not in G_limit:
            continue
        try:
            path2 = nx.dijkstra_path(G_limit, ev, end, weight="weight")
            # Step 3: 경로 성공 시 병합
            merged_path = path1[:-1] + path2
            
            details = []
            total_distance = 0.0
            total_stairs = 0
            total_weight = 0.0
            
            # 1차 경로 복원 (G_general 그래프)
            for i in range(len(path1) - 1):
                u, v = path1[i], path1[i + 1]
                ed = G_general[u][v]
                total_distance += ed.get("distance_m", 0)
                total_stairs += ed.get("stairs_count", 0)
                total_weight += ed["weight"]
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
                
            # 2차 경로 복원 (G_limit 그래프)
            for i in range(len(path2) - 1):
                u, v = path2[i], path2[i + 1]
                ed = G_limit[u][v]
                total_distance += ed.get("distance_m", 0)
                total_stairs += ed.get("stairs_count", 0)
                total_weight += ed["weight"]
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
                
            summary = {
                "path_length": len(merged_path),
                "total_distance_m": round(total_distance, 2),
                "total_stairs": total_stairs,
                "total_weight": round(total_weight, 4),
            }
            
            return {
                "path": merged_path,
                "total_weight": round(total_weight, 4),
                "details": details,
                "summary": summary
            }
        except nx.NetworkXNoPath:
            continue
            
    return None


def find_top_k_paths(start, end, profile="일반", mode="빠른도착", k=3):
    G = build_graph(profile, mode)

    if start not in G or end not in G:
        fallback = find_fallback_path(start, end, profile, mode)
        if fallback:
            return [fallback]
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
        fallback = find_fallback_path(start, end, profile, mode)
        if fallback:
            return [fallback]
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
