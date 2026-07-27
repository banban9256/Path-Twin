// src/App.jsx

import { useEffect, useMemo, useState } from "react";
import FloorMap from "./components/FloorMap";
import { FLOOR_ORDER } from "./mapData";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:5000";

const DEFAULT_CONFIG = {
  profiles: [
    { value: "일반", label: "일반 보행자" },
    { value: "휠체어", label: "휠체어 사용자" },
    { value: "목발", label: "목발 사용자" },
    { value: "유아차", label: "유아차 이용자" },
    { value: "짐", label: "무거운 짐 소지자" },
  ],
  modes: ["빠른도착", "편하게"],
  start_locations: [
    { location_id: "kkumjirak", label: "꼼지락", floor: 1, route_node_id: "서관_1층_계단앞" },
    { location_id: "job_plus_center", label: "대학 일자리 플러스센터", floor: 1, route_node_id: "서관_1층_로비" },
    { location_id: "cafe", label: "카페", floor: 1, route_node_id: "서관_1층_로비" },
    { location_id: "copy_room", label: "복사실", floor: 1, route_node_id: "동관_1층_계단앞" },
    { location_id: "student_happiness_lounge", label: "학생 행복 라운지", floor: 1, route_node_id: "서관_1층_로비" },
    { location_id: "east_lobby", label: "동관 로비", floor: 1, route_node_id: "동관_1층_로비" },
    { location_id: "west_entrance", label: "서관 입구", floor: 1, route_node_id: "서관_시작노드" },
    { location_id: "east_entrance", label: "동관 입구", floor: 1, route_node_id: "동관_시작노드" },
    { location_id: "west_1f_elevator", label: "서관 1층 엘리베이터 앞", floor: 1, route_node_id: "서관_1층_엘리베이터앞" },
    { location_id: "central_corridor_1f", label: "1층 중앙 연결통로", floor: 1, route_node_id: "1층_중앙복도(연결통로)" },
    { location_id: "west_1f_stairs", label: "서관 1층 계단 앞", floor: 1, route_node_id: "서관_1층_계단앞" },
    { location_id: "east_1f_stairs", label: "동관 1층 계단 앞", floor: 1, route_node_id: "동관_1층_계단앞" },
    { location_id: "reading_stairs_1f", label: "열람실 계단", floor: 1, route_node_id: "열람실_긴계단_아래(동관쪽길)" },
    { location_id: "teaching_support_center", label: "교수학습지원센터", floor: 2, route_node_id: "서관_2층_계단앞" },
    { location_id: "university_admin_team", label: "대학행정팀", floor: 2, route_node_id: "서관_2층_엘리베이터앞" },
    { location_id: "central_library_room_1", label: "중앙 도서관(자료실 1)", floor: 2, route_node_id: "서관_2층_엘리베이터앞" },
    { location_id: "ipp_center", label: "IPP센터", floor: 2, route_node_id: "서관_2층_계단앞" },
    { location_id: "west_2f_stairs", label: "서관 2층 계단 앞", floor: 2, route_node_id: "서관_2층_계단앞" },
    { location_id: "west_2f_elevator", label: "서관 2층 엘리베이터 앞", floor: 2, route_node_id: "서관_2층_엘리베이터앞" },
    { location_id: "cloud_bridge_entrance", label: "구름다리 입구", floor: 2, route_node_id: "구름다리_입구" },
    { location_id: "reading_stairs_2f_entrance", label: "2층 열람실 계단 입구", floor: 2, route_node_id: "구름다리_출구(서관2층)" },
    { location_id: "central_library_room_2", label: "중앙 도서관(자료실 2)", floor: 3, route_node_id: "서관_3층_엘리베이터앞" },
    { location_id: "reading_room", label: "열람실", floor: 3, route_node_id: "서관_3층_엘리베이터앞" },
    { location_id: "seminar_room", label: "세미나실", floor: 3, route_node_id: "서관_3층_계단앞" },
    { location_id: "west_3f_stairs", label: "서관 3층 계단 앞", floor: 3, route_node_id: "서관_3층_계단앞" },
    { location_id: "west_3f_elevator", label: "서관 3층 엘리베이터 앞", floor: 3, route_node_id: "서관_3층_엘리베이터앞" },
    { location_id: "reading_stairs_3f_entrance", label: "3층 열람실 계단 입구", floor: 3, route_node_id: "3층_쪽계단위" },
    { location_id: "book_cafe", label: "북카페", floor: 4, route_node_id: "서관_3층_엘리베이터앞" },
    { location_id: "parking_stairs", label: "주차장쪽 계단", floor: "외부", route_node_id: "주차장쪽_시작노드" },
    { location_id: "side_road_entrance", label: "쪽길 입구", floor: "외부", route_node_id: "쪽길_시작노드(개구멍)" },
  ],
  destination: {
    node_id: "3층_열람실_입구",
    label: "3층 노트북 열람실",
    floor: 3,
  },
};

const REQUIRED_START_LOCATIONS = [
  {
    location_id: "reading_stairs_1f",
    label: "열람실 계단",
    floor: 1,
    route_node_id: "열람실_긴계단_아래(동관쪽길)",
  },
];

function mergeStartLocations(apiLocations) {
  const baseLocations =
    Array.isArray(apiLocations) && apiLocations.length > 0
      ? apiLocations
      : DEFAULT_CONFIG.start_locations;

  const locationMap = new Map(
    baseLocations.map((location) => [
      location.location_id,
      location,
    ]),
  );

  REQUIRED_START_LOCATIONS.forEach((location) => {
    locationMap.set(location.location_id, {
      ...locationMap.get(location.location_id),
      ...location,
    });
  });

  return Array.from(locationMap.values());
}

const PROFILE_META = {
  일반: {
    icon: "🚶",
    title: "일반 보행자",
    description: "일반적인 보행 조건을 적용합니다.",
  },
  휠체어: {
    icon: "♿",
    title: "휠체어 사용자",
    description: "계단을 제외하고 턱과 문 통과 부담을 반영합니다.",
  },
  목발: {
    icon: "🩼",
    title: "목발 사용자",
    description: "느린 이동 속도와 계단 부담을 반영합니다.",
  },
  유아차: {
    icon: "👶",
    title: "유아차 이용자",
    description: "계단을 제외하고 문과 턱의 불편을 반영합니다.",
  },
  짐: {
    icon: "🧳",
    title: "무거운 짐 소지자",
    description: "짐을 든 상태의 이동 부담을 반영합니다.",
  },
};

const MODE_META = {
  빠른도착: {
    icon: "⚡",
    title: "뭐가 됐든 빨리 도착할래요",
    description: "예상 이동 시간이 짧은 경로를 우선 추천합니다.",
  },
  편하게: {
    icon: "🌿",
    title: "조금 느려도 편하게 갈래요",
    description: "계단, 턱, 문 통과 부담이 적은 경로를 우선 추천합니다.",
  },
};

const ROUTE_COLORS = ["#e85b55", "#5667df", "#1e9b76"];

function formatDuration(totalSeconds) {
  const safeSeconds = Number(totalSeconds) || 0;
  const minutes = Math.floor(safeSeconds / 60);
  const seconds = safeSeconds % 60;

  if (minutes <= 0) {
    return `${seconds}초`;
  }

  if (seconds === 0) {
    return `${minutes}분`;
  }

  return `${minutes}분 ${seconds}초`;
}

function getRouteTitle(route, index) {
  const details = route?.details ?? [];

  const usesElevator = details.some(
    (detail) => detail.edge_type === "엘리베이터",
  );

  const totalStairs = Number(route?.summary?.total_stairs ?? 0);

  const usesSideRoute = (route?.path ?? []).some(
    (node) =>
      node.includes("쪽계단") ||
      node.includes("구름다리") ||
      node.includes("쪽길"),
  );

  if (index === 0) {
    return "가장 추천하는 경로";
  }

  if (usesElevator && totalStairs === 0) {
    return "엘리베이터 중심 경로";
  }

  if (usesSideRoute) {
    return "쪽길·구름다리 경로";
  }

  if (totalStairs > 0) {
    return "계단을 이용하는 대안 경로";
  }

  return `추천 경로 ${index + 1}`;
}

function calculateSafetyScore(route) {
  if (!route) {
    return 0;
  }

  const details = route.details ?? [];
  const totalStairs = Number(route.summary?.total_stairs ?? 0);

  let score = 100;

  score -= Math.min(totalStairs * 0.45, 25);

  details.forEach((detail) => {
    if (detail.step_height === "미니") {
      score -= 2;
    }

    if (detail.step_height === "중간") {
      score -= 7;
    }

    if (detail.door_type && detail.door_type !== "없음") {
      score -= 2;
    }

    if (
      detail.obstacle_info &&
      detail.obstacle_info !== "없음" &&
      detail.obstacle_info.trim() !== ""
    ) {
      score -= 2;
    }
  });

  return Math.max(0, Math.round(score));
}

function getSafetyLabel(score) {
  if (score >= 90) {
    return "매우 안전";
  }

  if (score >= 80) {
    return "안전";
  }

  if (score >= 65) {
    return "주의 필요";
  }

  return "위험 요소 있음";
}


function getEstimatedSeconds(route) {
  const value = Number(route?.estimated_seconds);
  return Number.isFinite(value) ? value : Number.MAX_SAFE_INTEGER;
}

function getTotalDistance(route) {
  const value = Number(route?.summary?.total_distance_m);
  return Number.isFinite(value) ? value : Number.MAX_SAFE_INTEGER;
}

function getTotalStairs(route) {
  const value = Number(route?.summary?.total_stairs);
  return Number.isFinite(value) ? value : Number.MAX_SAFE_INTEGER;
}

/*
 * 이동 우선순위에 맞춰 경로 후보를 프론트에서도 한 번 더 정렬합니다.
 *
 * 빠른도착:
 *   1) 예상 소요 시간 오름차순
 *   2) 이동 거리 오름차순
 *   3) 안전도 내림차순
 *
 * 편하게:
 *   1) 안전도 내림차순
 *   2) 계단 수 오름차순
 *   3) 예상 소요 시간 오름차순
 *   4) 이동 거리 오름차순
 */
function sortRoutesByMode(routeList, mode) {
  const safeRoutes = Array.isArray(routeList) ? [...routeList] : [];

  safeRoutes.sort((routeA, routeB) => {
    if (mode === "편하게") {
      const safetyDifference =
        calculateSafetyScore(routeB) - calculateSafetyScore(routeA);

      if (safetyDifference !== 0) {
        return safetyDifference;
      }

      const stairsDifference =
        getTotalStairs(routeA) - getTotalStairs(routeB);

      if (stairsDifference !== 0) {
        return stairsDifference;
      }

      const timeDifference =
        getEstimatedSeconds(routeA) - getEstimatedSeconds(routeB);

      if (timeDifference !== 0) {
        return timeDifference;
      }

      return getTotalDistance(routeA) - getTotalDistance(routeB);
    }

    const timeDifference =
      getEstimatedSeconds(routeA) - getEstimatedSeconds(routeB);

    if (timeDifference !== 0) {
      return timeDifference;
    }

    const distanceDifference =
      getTotalDistance(routeA) - getTotalDistance(routeB);

    if (distanceDifference !== 0) {
      return distanceDifference;
    }

    return calculateSafetyScore(routeB) - calculateSafetyScore(routeA);
  });

  return safeRoutes;
}

function getEdgeIcon(edgeType) {
  const type = String(edgeType ?? "");

  if (type.includes("엘리베이터")) {
    return "🛗";
  }

  if (type.includes("계단")) {
    return "🪜";
  }

  if (type.includes("외부")) {
    return "🌳";
  }

  if (type.includes("복도")) {
    return "➡️";
  }

  if (type.includes("문")) {
    return "🚪";
  }

  return "📍";
}

function App() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);

  const [profile, setProfile] = useState("일반");
  const [mode, setMode] = useState("빠른도착");
  const [startLocationId, setStartLocationId] = useState("kkumjirak");

  const [activeFloor, setActiveFloor] = useState(1);

  const [routes, setRoutes] = useState([]);
  const [selectedRouteIndex, setSelectedRouteIndex] = useState(0);

  const [isConfigLoading, setIsConfigLoading] = useState(true);
  const [isRouteLoading, setIsRouteLoading] = useState(false);

  const [configError, setConfigError] = useState("");
  const [routeError, setRouteError] = useState("");

  const selectedRoute = routes[selectedRouteIndex] ?? null;

  const selectedRouteColor =
    ROUTE_COLORS[selectedRouteIndex] ?? ROUTE_COLORS[0];

  const selectedProfileMeta =
    PROFILE_META[profile] ?? PROFILE_META.일반;

  const selectedModeMeta =
    MODE_META[mode] ?? MODE_META.빠른도착;

  const selectedStart = useMemo(
    () =>
      config.start_locations.find(
        (location) => location.location_id === startLocationId,
      ) ?? config.start_locations[0],
    [config.start_locations, startLocationId],
  );

  const groupedStartLocations = useMemo(() => {
    const groups = [1, 2, 3, 4, "외부"];

    return groups
      .map((floor) => ({
        floor,
        locations: config.start_locations.filter(
          (location) => location.floor === floor,
        ),
      }))
      .filter((group) => group.locations.length > 0);
  }, [config.start_locations]);

  const safetyScore = useMemo(
    () => calculateSafetyScore(selectedRoute),
    [selectedRoute],
  );

  useEffect(() => {
    async function loadConfig() {
      setIsConfigLoading(true);
      setConfigError("");

      try {
        const response = await fetch(`${API_BASE_URL}/api/config`);

        if (!response.ok) {
          throw new Error("설정 정보를 불러오지 못했습니다.");
        }

        const data = await response.json();

        setConfig({
          profiles:
            Array.isArray(data.profiles) && data.profiles.length > 0
              ? data.profiles
              : DEFAULT_CONFIG.profiles,

          modes:
            Array.isArray(data.modes) && data.modes.length > 0
              ? data.modes
              : DEFAULT_CONFIG.modes,

          start_locations: mergeStartLocations(
            data.start_locations,
          ),

          destination:
            data.destination ?? DEFAULT_CONFIG.destination,
        });

        if (
          Array.isArray(data.start_locations) &&
          data.start_locations.length > 0
        ) {
          setStartLocationId(data.start_locations[0].location_id);
        }
      } catch (error) {
        console.error(error);

        setConfig({
          ...DEFAULT_CONFIG,
          start_locations: mergeStartLocations(
            DEFAULT_CONFIG.start_locations,
          ),
        });
        setConfigError(
          "API 설정을 불러오지 못해 기본 설정을 표시하고 있습니다.",
        );
      } finally {
        setIsConfigLoading(false);
      }
    }

    loadConfig();
  }, []);

  async function handleSimulation() {
    setIsRouteLoading(true);
    setRouteError("");
    setRoutes([]);
    setSelectedRouteIndex(0);

    try {
      const response = await fetch(`${API_BASE_URL}/api/routes`, {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          start_location_id: startLocationId,
          start_node_id: selectedStart?.route_node_id,
          end: config.destination.node_id,
          profile,
          mode,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.ok) {
        throw new Error(
          data.message ?? "경로 시뮬레이션에 실패했습니다.",
        );
      }

      const sortedRoutes = sortRoutesByMode(data.routes, mode);

      setRoutes(sortedRoutes);
      setSelectedRouteIndex(0);
      setActiveFloor(
        typeof selectedStart?.floor === "number"
          ? selectedStart.floor
          : 1,
      );
    } catch (error) {
      console.error(error);

      setRouteError(
        error.message ||
          "서버와 연결할 수 없습니다. API 서버 실행 상태를 확인해 주세요.",
      );
    } finally {
      setIsRouteLoading(false);
    }
  }

  function handleRouteSelect(index) {
    setSelectedRouteIndex(index);

    const route = routes[index];

    if (route?.path?.includes("3층_열람실_입구")) {
      setActiveFloor(3);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-inner">
          <div className="brand-area">
            <div className="brand-mark" aria-hidden="true">
              PT
            </div>

            <div>
              <p className="brand-eyebrow">
                Inclusive AI Digital Twin
              </p>

              <h1>AI가 대신 가줍니다</h1>
            </div>
          </div>

          <div className="header-status">
            <span className="status-dot" />
            <span>경삼관 접근성 경로 시뮬레이터</span>
          </div>
        </div>
      </header>

      <main className="app-main">
        <aside className="control-panel">
          <div className="control-panel-header">
            <span className="step-badge">이동 조건 설정</span>

            <h2>오늘의 몸 상태를 알려주세요</h2>

            <p>
              선택한 조건에 맞춰 실제 경로 데이터를 먼저
              시뮬레이션합니다.
            </p>
          </div>

          {configError && (
            <div className="inline-notice inline-notice-warning">
              {configError}
            </div>
          )}

          <section className="control-section">
            <div className="section-title-row">
              <div>
                <span className="section-number">01</span>
                <h3>사용자 유형</h3>
              </div>
            </div>

            <div className="profile-grid">
              {config.profiles.map((item) => {
                const meta =
                  PROFILE_META[item.value] ?? PROFILE_META.일반;

                const isSelected = profile === item.value;

                return (
                  <button
                    key={item.value}
                    type="button"
                    className={[
                      "profile-card",
                      isSelected ? "is-selected" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    onClick={() => setProfile(item.value)}
                    disabled={isConfigLoading}
                  >
                    <span className="profile-icon">{meta.icon}</span>

                    <span className="profile-copy">
                      <strong>{meta.title}</strong>
                      <small>{meta.description}</small>
                    </span>

                    <span
                      className="selection-check"
                      aria-hidden="true"
                    >
                      ✓
                    </span>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="control-section">
            <div className="section-title-row">
              <div>
                <span className="section-number">02</span>
                <h3>이동 우선순위</h3>
              </div>
            </div>

            <div className="mode-grid">
              {config.modes.map((item) => {
                const meta =
                  MODE_META[item] ?? MODE_META.빠른도착;

                const isSelected = mode === item;

                return (
                  <button
                    key={item}
                    type="button"
                    className={[
                      "mode-card",
                      isSelected ? "is-selected" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    onClick={() => setMode(item)}
                    disabled={isConfigLoading}
                  >
                    <span className="mode-icon">{meta.icon}</span>

                    <span>
                      <strong>{meta.title}</strong>
                      <small>{meta.description}</small>
                    </span>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="control-section">
            <div className="section-title-row">
              <div>
                <span className="section-number">03</span>
                <h3>출발지와 목적지</h3>
              </div>
            </div>

            <label className="field-group">
              <span>출발지</span>

              <select
                value={startLocationId}
                onChange={(event) =>
                  setStartLocationId(event.target.value)
                }
                disabled={isConfigLoading}
              >
                {groupedStartLocations.map((group) => (
                  <optgroup
                    key={String(group.floor)}
                    label={
                      group.floor === "외부"
                        ? "건물 외부·외곽"
                        : `${group.floor}층`
                    }
                  >
                    {group.locations.map((location) => (
                      <option
                        key={location.location_id}
                        value={location.location_id}
                      >
                        {location.label}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </label>

            <div className="direction-arrow" aria-hidden="true">
              ↓
            </div>

            <label className="field-group">
              <span>목적지</span>

              <select value={config.destination.node_id} disabled>
                <option value={config.destination.node_id}>
                  {config.destination.floor}층 ·{" "}
                  {config.destination.label}
                </option>
              </select>
            </label>
          </section>

          <button
            type="button"
            className="simulation-button"
            onClick={handleSimulation}
            disabled={isRouteLoading || isConfigLoading}
          >
            {isRouteLoading ? (
              <>
                <span className="button-spinner" />
                실제 경로 계산 중...
              </>
            ) : (
              <>
                <span>경로 시뮬레이션 실행</span>
                <span aria-hidden="true">→</span>
              </>
            )}
          </button>

          <div className="current-settings-card">
            <p>현재 설정</p>

            <dl>
              <div>
                <dt>사용자</dt>
                <dd>
                  {selectedProfileMeta.icon}{" "}
                  {selectedProfileMeta.title}
                </dd>
              </div>

              <div>
                <dt>우선순위</dt>
                <dd>{selectedModeMeta.title}</dd>
              </div>

              <div>
                <dt>출발</dt>
                <dd>{selectedStart?.label ?? "선택 없음"}</dd>
              </div>

              <div>
                <dt>도착</dt>
                <dd>{config.destination.label}</dd>
              </div>
            </dl>
          </div>
        </aside>

        <section className="content-panel">
          <div className="map-panel">
            <div className="floor-tabs" role="tablist">
              {FLOOR_ORDER.map((floor) => (
                <button
                  key={floor}
                  type="button"
                  role="tab"
                  aria-selected={activeFloor === floor}
                  className={[
                    "floor-tab",
                    activeFloor === floor ? "is-active" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => setActiveFloor(floor)}
                >
                  {floor}층
                </button>
              ))}
            </div>

            <FloorMap
              floor={activeFloor}
              routePath={selectedRoute?.path ?? []}
              routeColor={selectedRouteColor}
            />
          </div>

          {routeError && (
            <div className="result-error-card">
              <strong>경로를 불러오지 못했습니다.</strong>
              <p>{routeError}</p>
              <small>
                `python api_server.py`가 실행 중인지 확인해 주세요.
              </small>
            </div>
          )}

          {!routeError && routes.length === 0 && (
            <div className="empty-result-card">
              <div className="empty-result-icon">🧭</div>

              <div>
                <h2>아직 시뮬레이션 결과가 없어요</h2>

                <p>
                  왼쪽에서 사용자 유형과 이동 조건을 선택한 후
                  경로 시뮬레이션을 실행해 주세요.
                </p>
              </div>
            </div>
          )}

          {routes.length > 0 && selectedRoute && (
            <div className="simulation-results">
              <section className="route-candidate-section">
                <div className="result-section-heading">
                  <div>
                    <span className="result-eyebrow">
                      추천 경로 후보
                    </span>

                    <h2>원하는 경로를 선택해 비교해 보세요.</h2>
                  </div>

                  <span className="route-count">
                    {routes.length}개 경로
                  </span>
                </div>

                <div className="route-card-grid">
                  {routes.map((route, index) => {
                    const isSelected =
                      selectedRouteIndex === index;

                    const routeSafetyScore =
                      calculateSafetyScore(route);

                    return (
                      <button
                        key={route.id ?? `route-${index}`}
                        type="button"
                        className={[
                          "route-candidate-card",
                          isSelected ? "is-selected" : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                        style={{
                          "--route-color": ROUTE_COLORS[index],
                        }}
                        onClick={() => handleRouteSelect(index)}
                      >
                        <div className="route-card-top">
                          <span
                            className="route-color-dot"
                            aria-hidden="true"
                          />

                          <span className="route-rank">
                            {index === 0
                              ? mode === "빠른도착"
                                ? "최단 시간"
                                : "가장 편한 경로"
                              : `${index + 1}순위`}
                          </span>
                        </div>

                        <strong>{getRouteTitle(route, index)}</strong>

                        <p>
                          {route.path_labels?.[0]} →{" "}
                          {route.path_labels?.[
                            route.path_labels.length - 1
                          ]}
                        </p>

                        <div className="route-card-metrics">
                          <span>
                            ⏱ {formatDuration(route.estimated_seconds)}
                          </span>

                          <span>
                            📏 {route.summary.total_distance_m}m
                          </span>

                          <span>🛡 {routeSafetyScore}점</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </section>

              <section className="selected-route-banner">
                <div>
                  <span>선택된 경로</span>
                  <strong>
                    {getRouteTitle(
                      selectedRoute,
                      selectedRouteIndex,
                    )}
                  </strong>

                  <p>
                    {selectedStart?.label} →{" "}
                    {config.destination.label}
                  </p>
                </div>

                <div
                  className="selected-route-symbol"
                  style={{
                    backgroundColor: selectedRouteColor,
                  }}
                  aria-hidden="true"
                >
                  {selectedRouteIndex + 1}
                </div>
              </section>

              <section className="summary-grid">
                <article className="summary-card">
                  <span className="summary-icon">⏱</span>
                  <p>총 소요 시간</p>
                  <strong>
                    {formatDuration(
                      selectedRoute.estimated_seconds,
                    )}
                  </strong>
                </article>

                <article className="summary-card">
                  <span className="summary-icon">📏</span>
                  <p>총 이동 거리</p>
                  <strong>
                    {selectedRoute.summary.total_distance_m}m
                  </strong>
                </article>

                <article className="summary-card">
                  <span className="summary-icon">🪜</span>
                  <p>총 계단 수</p>
                  <strong>
                    {selectedRoute.summary.total_stairs}칸
                  </strong>
                </article>

                <article className="summary-card">
                  <span className="summary-icon">🛡</span>
                  <p>경로 안전도</p>
                  <strong>{safetyScore}점</strong>
                  <small>{getSafetyLabel(safetyScore)}</small>
                </article>
              </section>

              <section className="result-detail-grid">
                <article className="result-card timeline-card">
                  <div className="card-heading">
                    <span>구간별 이동</span>
                    <h3>이동 타임라인</h3>
                  </div>

                  <ol className="timeline-list">
                    {selectedRoute.details.map((detail, index) => (
                      <li
                        key={`${detail.from}-${detail.to}-${index}`}
                        className="timeline-item"
                      >
                        <div className="timeline-marker">
                          <span>{getEdgeIcon(detail.edge_type)}</span>
                        </div>

                        <div className="timeline-copy">
                          <div className="timeline-title-row">
                            <strong>
                              {detail.from_label} → {detail.to_label}
                            </strong>

                            <span>{detail.distance_m}m</span>
                          </div>

                          <p>
                            {detail.edge_type || "이동 구간"}
                          </p>

                          <div className="timeline-tags">
                            {Number(detail.stairs_count) > 0 && (
                              <span className="timeline-tag tag-stairs">
                                계단 {detail.stairs_count}칸
                              </span>
                            )}

                            {detail.step_height === "미니" && (
                              <span className="timeline-tag tag-threshold-mini">
                                턱 미니
                              </span>
                            )}

                            {detail.step_height === "중간" && (
                              <span className="timeline-tag tag-threshold-medium">
                                턱 중간
                              </span>
                            )}

                            {detail.door_type &&
                              detail.door_type !== "없음" && (
                                <span className="timeline-tag">
                                  {detail.door_type}
                                </span>
                              )}
                          </div>

                          {detail.obstacle_info &&
                            detail.obstacle_info !== "없음" && (
                              <p className="timeline-warning">
                                주의: {detail.obstacle_info}
                              </p>
                            )}
                        </div>
                      </li>
                    ))}
                  </ol>
                </article>

                <div className="result-side-column">
                  <article className="result-card reason-card">
                    <div className="card-heading">
                      <span>경로 선택 근거</span>
                      <h3>추천 사유</h3>
                    </div>

                    <p className="reason-text">
                      {selectedRoute.recommendation_reason}
                    </p>

                    <div className="reason-meta">
                      <span>
                        {selectedProfileMeta.icon}{" "}
                        {selectedProfileMeta.title}
                      </span>

                      <span>{selectedModeMeta.icon}</span>
                    </div>
                  </article>

                  <article className="result-card warning-card">
                    <div className="card-heading">
                      <span>이동 전 확인</span>
                      <h3>주의 요소</h3>
                    </div>

                    {selectedRoute.warnings?.length > 0 ? (
                      <ul className="warning-list">
                        {selectedRoute.warnings.map(
                          (warning, index) => (
                            <li key={`${warning}-${index}`}>
                              <span aria-hidden="true">!</span>
                              <p>{warning}</p>
                            </li>
                          ),
                        )}
                      </ul>
                    ) : (
                      <div className="no-warning">
                        <span>✓</span>
                        <p>
                          현재 경로에서 별도의 주요 주의 요소가
                          확인되지 않았습니다.
                        </p>
                      </div>
                    )}
                  </article>
                </div>
              </section>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;