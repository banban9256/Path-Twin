from __future__ import annotations

import math
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS

from pathfinder import (
    MODES,
    PROFILES,
    PROFILE_LABELS,
    find_top_k_paths,
    get_all_nodes,
)

app = Flask(__name__)
CORS(app)

DESTINATION_NODE = "3층_열람실_입구"

START_LOCATIONS = [
    # 1층
    {"location_id": "kkumjirak", "label": "꼼지락", "floor": 1,
     "route_node_id": "서관_1층_계단앞"},
    {"location_id": "job_plus_center", "label": "대학 일자리 플러스센터", "floor": 1,
     "route_node_id": "서관_1층_로비"},
    {"location_id": "cafe", "label": "카페", "floor": 1,
     "route_node_id": "서관_1층_로비"},
    {"location_id": "copy_room", "label": "복사실", "floor": 1,
     "route_node_id": "동관_1층_계단앞"},
    {"location_id": "student_happiness_lounge", "label": "학생 행복 라운지", "floor": 1,
     "route_node_id": "서관_1층_로비"},
    {"location_id": "east_lobby", "label": "동관 로비", "floor": 1,
     "route_node_id": "동관_1층_로비"},
    {"location_id": "west_entrance", "label": "서관 입구", "floor": 1,
     "route_node_id": "서관_시작노드"},
    {"location_id": "east_entrance", "label": "동관 입구", "floor": 1,
     "route_node_id": "동관_시작노드"},
    {"location_id": "west_1f_elevator", "label": "서관 1층 엘리베이터 앞", "floor": 1,
     "route_node_id": "서관_1층_엘리베이터앞"},
    {"location_id": "central_corridor_1f", "label": "1층 중앙 연결통로", "floor": 1,
     "route_node_id": "1층_중앙복도(연결통로)"},
    {"location_id": "west_1f_stairs", "label": "서관 1층 계단 앞", "floor": 1,
     "route_node_id": "서관_1층_계단앞"},
    {"location_id": "east_1f_stairs", "label": "동관 1층 계단 앞", "floor": 1,
     "route_node_id": "동관_1층_계단앞"},

    # 2층
    {"location_id": "teaching_support_center", "label": "교수학습지원센터", "floor": 2,
     "route_node_id": "서관_2층_계단앞"},
    {"location_id": "university_admin_team", "label": "대학행정팀", "floor": 2,
     "route_node_id": "서관_2층_엘리베이터앞"},
    {"location_id": "central_library_room_1", "label": "중앙 도서관(자료실 1)", "floor": 2,
     "route_node_id": "서관_2층_엘리베이터앞"},
    {"location_id": "ipp_center", "label": "IPP센터", "floor": 2,
     "route_node_id": "서관_2층_계단앞"},
    {"location_id": "west_2f_stairs", "label": "서관 2층 계단 앞", "floor": 2,
     "route_node_id": "서관_2층_계단앞"},
    {"location_id": "west_2f_elevator", "label": "서관 2층 엘리베이터 앞", "floor": 2,
     "route_node_id": "서관_2층_엘리베이터앞"},
    {"location_id": "cloud_bridge_entrance", "label": "구름다리 입구", "floor": 2,
     "route_node_id": "구름다리_입구"},
    {"location_id": "reading_stairs_2f_entrance", "label": "2층 열람실 계단 입구", "floor": 2,
     "route_node_id": "구름다리_출구(서관2층)"},

    # 3층
    {"location_id": "central_library_room_2", "label": "중앙 도서관(자료실 2)", "floor": 3,
     "route_node_id": "서관_3층_엘리베이터앞"},
    {"location_id": "reading_room", "label": "열람실", "floor": 3,
     "route_node_id": "서관_3층_엘리베이터앞"},
    {"location_id": "seminar_room", "label": "세미나실", "floor": 3,
     "route_node_id": "서관_3층_계단앞"},
    {"location_id": "west_3f_stairs", "label": "서관 3층 계단 앞", "floor": 3,
     "route_node_id": "서관_3층_계단앞"},
    {"location_id": "west_3f_elevator", "label": "서관 3층 엘리베이터 앞", "floor": 3,
     "route_node_id": "서관_3층_엘리베이터앞"},
    {"location_id": "reading_stairs_3f_entrance", "label": "3층 열람실 계단 입구", "floor": 3,
     "route_node_id": "3층_쪽계단위"},

    # 4층 - 현재 CSV에는 4층 노드가 없어 가장 가까운 모델링 지점에 연결
    {"location_id": "book_cafe", "label": "북카페", "floor": 4,
     "route_node_id": "서관_3층_엘리베이터앞"},

    # 건물 외부·외곽
    {"location_id": "parking_stairs", "label": "주차장쪽 계단", "floor": "외부",
     "route_node_id": "주차장쪽_시작노드"},
    {"location_id": "side_road_entrance", "label": "쪽길 입구", "floor": "외부",
     "route_node_id": "쪽길_시작노드(개구멍)"},
]


NODE_LABELS = {
    "서관_시작노드": "서관 입구",
    "서관_1층_문앞(중앙)": "서관 중앙 출입문",
    "서관_1층_문앞(장애인)": "서관 장애인 통로",
    "서관_1층_로비": "학생 행복 라운지",
    "서관_1층_계단앞": "서관 1층 계단",
    "서관_1층_엘리베이터앞": "서관 1층 엘리베이터",
    "서관_2층_계단앞": "서관 2층 계단",
    "서관_2층_엘리베이터앞": "서관 2층 엘리베이터",
    "서관_3층_계단앞": "서관 3층 계단",
    "서관_3층_엘리베이터앞": "서관 3층 엘리베이터",
    "1층_중앙복도(연결통로)": "1층 중앙 연결통로",
    "동관_시작노드": "동관 입구",
    "동관_1층_문앞(중앙)": "동관 중앙 출입문",
    "동관_1층_문앞(좌측장애인)": "동관 장애인 통로 왼쪽",
    "동관_1층_문앞(우측장애인)": "동관 장애인 통로 오른쪽",
    "동관_1층_로비": "동관 로비",
    "동관_1층_계단앞": "동관 1층 계단",
    "주차장쪽_시작노드": "주차장 쪽 입구",
    "주차장_계단위": "주차장 쪽 계단",
    "중간쪽계단_위": "중간 쪽계단",
    "열람실_긴계단_아래(동관쪽길)": "열람실 긴계단 시작",
    "구름다리_입구": "구름다리 입구",
    "구름다리_출구(서관2층)": "2층 열람실 계단 입구",
    "쪽길_시작노드(개구멍)": "쪽길 입구",
    "쪽계단_아래": "쪽계단 아래",
    "3층_쪽계단위": "3층 열람실 계단 입구",
    "3층_열람실_입구": "3층 노트북 열람실",
}

PROFILE_SPEED_M_PER_MIN = {
    "일반": 80.0,
    "휠체어": 55.0,
    "목발": 40.0,
    "유아차": 55.0,
    "짐": 60.0,
}


def make_json_safe(value: Any) -> Any:
    """Flask JSON 응답에 넣을 수 없는 inf, nan 값을 제거합니다."""
    if isinstance(value, float) and not math.isfinite(value):
        return None

    if isinstance(value, dict):
        return {key: make_json_safe(item) for key, item in value.items()}

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    return value


def calculate_estimated_seconds(
    total_distance_m: float,
    total_stairs: int,
    profile: str,
) -> int:
    """
    발표용 예상 이동 시간입니다.

    거리 기반 보행 시간에 계단 통과 시간을 합산합니다.
    경로 순위 계산 자체는 기존 pathfinder.py의 실제 가중치를 사용합니다.
    """
    speed = PROFILE_SPEED_M_PER_MIN.get(profile, 80.0)
    walking_minutes = total_distance_m / speed

    stair_seconds_per_step = {
        "일반": 1.5,
        "휠체어": 0.0,
        "목발": 3.8,
        "유아차": 0.0,
        "짐": 2.2,
    }.get(profile, 1.5)

    stair_seconds = total_stairs * stair_seconds_per_step
    total_seconds = walking_minutes * 60 + stair_seconds

    return max(1, round(total_seconds))


def build_warnings(details: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []

    for detail in details:
        stairs_count = int(detail.get("stairs_count") or 0)
        step_height = str(detail.get("step_height") or "")
        door_type = str(detail.get("door_type") or "")
        obstacle_info = str(detail.get("obstacle_info") or "")

        if stairs_count > 0:
            warnings.append(
                f"{NODE_LABELS.get(detail['from'], detail['from'])}에서 "
                f"계단 {stairs_count}칸을 이용합니다."
            )

        if step_height == "미니":
            warnings.append(
                f"{NODE_LABELS.get(detail['to'], detail['to'])} 인근에 "
                "낮은 턱(턱 미니)이 있습니다."
            )

        if step_height == "중간":
            warnings.append(
                f"{NODE_LABELS.get(detail['to'], detail['to'])} 인근에 "
                "휠체어가 넘을 수 있지만 다소 높은 턱(턱 중간)이 있습니다."
            )

        if door_type and door_type != "없음":
            warnings.append(f"문 통과: {door_type}")

        if obstacle_info and obstacle_info != "없음":
            warnings.append(obstacle_info)

    # 중복 경고 제거
    return list(dict.fromkeys(warnings))


def build_recommendation_reason(
    route: dict[str, Any],
    profile: str,
    mode: str,
    route_index: int,
) -> str:
    summary = route["summary"]
    details = route["details"]

    uses_elevator = any(
        detail.get("edge_type") == "엘리베이터" for detail in details
    )
    step_levels = {
        str(detail.get("step_height") or "")
        for detail in details
        if detail.get("step_height") not in ("", "없음", None)
    }

    parts = [
        f"{PROFILE_LABELS.get(profile, profile)}의 이동 조건과 "
        f"'{mode}' 기준을 적용한 {route_index + 1}순위 경로입니다.",
        f"총 이동 거리는 {summary['total_distance_m']}m이며 "
        f"계단은 {summary['total_stairs']}칸 포함됩니다.",
    ]

    if uses_elevator:
        parts.append("층간 이동 시 엘리베이터를 이용합니다.")
    elif summary["total_stairs"] > 0:
        parts.append("이동 시간을 줄이기 위해 계단 구간이 포함되었습니다.")
    else:
        parts.append("계단이 포함되지 않은 경로입니다.")

    if "중간" in step_levels:
        parts.append("일부 구간에 턱 중간이 있어 통과 시 주의가 필요합니다.")
    elif "미니" in step_levels:
        parts.append("일부 구간에 낮은 턱인 턱 미니가 있습니다.")

    return " ".join(parts)


def convert_route(
    route: dict[str, Any],
    profile: str,
    mode: str,
    route_index: int,
) -> dict[str, Any]:
    summary = route["summary"]
    total_distance = float(summary.get("total_distance_m") or 0)
    total_stairs = int(summary.get("total_stairs") or 0)

    details = []
    for index, detail in enumerate(route["details"]):
        details.append(
            {
                **detail,
                "index": index + 1,
                "from_label": NODE_LABELS.get(
                    detail["from"],
                    detail["from"],
                ),
                "to_label": NODE_LABELS.get(
                    detail["to"],
                    detail["to"],
                ),
            }
        )

    converted = {
        "id": f"route-{route_index + 1}",
        "rank": route_index + 1,
        "path": route["path"],
        "path_labels": [
            NODE_LABELS.get(node_id, node_id)
            for node_id in route["path"]
        ],
        "details": details,
        "summary": summary,
        "estimated_seconds": calculate_estimated_seconds(
            total_distance,
            total_stairs,
            profile,
        ),
        "warnings": build_warnings(details),
    }

    converted["recommendation_reason"] = build_recommendation_reason(
        converted,
        profile,
        mode,
        route_index,
    )

    return converted


@app.get("/api/health")
def health():
    return jsonify(
        {
            "ok": True,
            "message": "Path-Twin API가 실행 중입니다.",
        }
    )


@app.get("/api/config")
def config():
    return jsonify(
        {
            "profiles": [
                {
                    "value": profile,
                    "label": PROFILE_LABELS.get(profile, profile),
                }
                for profile in PROFILES
            ],
            "modes": MODES,
            "start_locations": START_LOCATIONS,
            "destination": {
                "node_id": DESTINATION_NODE,
                "label": NODE_LABELS[DESTINATION_NODE],
                "floor": 3,
            },
        }
    )


@app.get("/api/nodes")
def nodes():
    return jsonify(
        [
            {
                **node,
                "label": NODE_LABELS.get(
                    node["node_id"],
                    node.get("name") or node["node_id"],
                ),
            }
            for node in get_all_nodes()
        ]
    )


@app.post("/api/routes")
def routes():
    body = request.get_json(silent=True) or {}

    start_location_id = str(body.get("start_location_id") or "").strip()
    end = str(body.get("end") or DESTINATION_NODE).strip()
    profile = str(body.get("profile") or "일반").strip()
    mode = str(body.get("mode") or "빠른도착").strip()

    selected_location = next(
        (
            item
            for item in START_LOCATIONS
            if item["location_id"] == start_location_id
        ),
        None,
    )

    if selected_location is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "올바른 출발지를 선택해 주세요.",
                }
            ),
            400,
        )

    # 사용자가 고른 장소명을 실제 CSV 그래프 노드로 변환합니다.
    start = selected_location["route_node_id"]

    if end != DESTINATION_NODE:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "현재 데모 목적지는 3층 노트북 열람실입니다.",
                }
            ),
            400,
        )

    if profile not in PROFILES:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "지원하지 않는 사용자 프로필입니다.",
                }
            ),
            400,
        )

    if mode not in MODES:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "지원하지 않는 이동 방식입니다.",
                }
            ),
            400,
        )

    results = find_top_k_paths(
        start=start,
        end=end,
        profile=profile,
        mode=mode,
        k=3,
    )

    if not results:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "선택한 조건으로 이동 가능한 경로를 찾지 못했습니다.",
                    "routes": [],
                }
            ),
            404,
        )

    converted_routes = [
        convert_route(route, profile, mode, index)
        for index, route in enumerate(results)
    ]

    response = {
        "ok": True,
        "request": {
            "start_location_id": start_location_id,
            "start": start,
            "start_label": selected_location["label"],
            "start_floor": selected_location["floor"],
            "end": end,
            "end_label": NODE_LABELS.get(end, end),
            "profile": profile,
            "profile_label": PROFILE_LABELS.get(profile, profile),
            "mode": mode,
        },
        "routes": converted_routes,
    }

    return jsonify(make_json_safe(response))


@app.errorhandler(Exception)
def handle_unexpected_error(error: Exception):
    app.logger.exception("처리되지 않은 서버 오류가 발생했습니다.")

    return (
        jsonify(
            {
                "ok": False,
                "message": f"서버 오류가 발생했습니다: {error}",
            }
        ),
        500,
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
    