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
    obstacle = edge.get("obstacle_info", "")
    start = edge.get("start_node", "")
    end = edge.get("end_node", "")

    # 열람실 긴계단 식별
    is_long_stair = (
        {start, end} == {"열람실_긴계단_아래(동관쪽길)", "3층_열람실_입구"} or
        "가장 긴 계단" in obstacle
    )

    if etype == "엘리베이터":
        base = ELEVATOR_COST
    elif stairs > 0:
        is_low_center_stair = "중앙 낮은 계단" in obstacle
        is_side_road_stair = (
            "쪽길" in start or "쪽길" in end or
            "쪽계단" in start or "쪽계단" in end or
            "쪽길" in obstacle or "쪽계단" in obstacle
        )

        # 쪽길입구 계단 간선 예외 처리
        if is_side_road_stair:
            if profile in ("휠체어", "유아차", "목발"):
                return float("inf")
            else:
                # 일반 사용자 및 무거운 짐 소지자는 기본 가중치 적용
                base = stairs * STAIR_COST_PER_STEP[profile]
        else:
            # 휠체어 & 유아차는 모든 계단 진입 불가
            if profile in ("휠체어", "유아차"):
                return float("inf")

            # 목발 사용자
            elif profile == "목발":
                if mode == "편하게":
                    # 편하게 선택 시 휠체어와 동일 (계단 절대 불가)
                    return float("inf")
                else: # 빠른도착 선택 시
                    # 완만한 '중앙 낮은 계단'만 예외 허용, 일반 계단은 절대 불가
                    if is_low_center_stair:
                        base = 50.0 * (5.0 ** stairs)
                    else:
                        return float("inf")

            # 무거운 짐 소지자
            elif profile == "짐":
                if mode == "편하게":
                    # 엘리베이터 우회를 최우선 유도하기 위해 페널티 극대화 (5000.0)
                    base = 5000.0 + stairs * STAIR_COST_PER_STEP[profile]
                else:
                    # 빠르게 갈 때는 기본 가중치 적용
                    base = stairs * STAIR_COST_PER_STEP[profile]
            else:
                if mode == "편하게":
                    # 일반 보행자도 '편하게' 갈 때는 피로도 페널티 가산 (3000.0)
                    base = 3000.0 + stairs * STAIR_COST_PER_STEP[profile]
                else:
                    base = stairs * STAIR_COST_PER_STEP[profile]

        # 열람실 긴계단 추가 페널티 부여 (구름다리 선호)
        if is_long_stair:
            base += 500.0
    else:
        base = dist / WALK_SPEED

        # 편하게 모드일 때 구름다리 -> 엘리베이터 연계를 위해 계단앞으로 빠지는 우회 복도에 페널티 부여
        if mode == "편하게" and {start, end} == {"서관_2층_계단앞", "서관_2층_엘리베이터앞"}:
            base += 200.0

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

        # 교통약자(휠체어, 유아차, 목발)는 모든 계단 간선 원천 차단 (Hard Block)
        if profile in ("휠체어", "유아차", "목발") and edge.get("stairs_count", 0) > 0:
            continue

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
        if profile in ("휠체어", "유아차", "목발") and edge.get("stairs_count", 0) > 0:
            continue

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
    if profile in ("휠체어", "유아차", "목발"):
        edges_to_remove = [(u, v) for u, v, d in G_general.edges(data=True) if d.get("stairs_count", 0) > 0]
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
