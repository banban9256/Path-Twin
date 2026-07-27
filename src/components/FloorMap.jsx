// src/components/FloorMap.jsx

import {
  MAP_SIZE,
  getFloorMap,
  getPathNodesForFloor,
} from "../mapData";

const FLOOR_IMAGE_PATHS = {
  1: "/maps/gyeongsam-1f.svg",
  2: "/maps/gyeongsam-2f.svg",
  3: "/maps/gyeongsam-3f.svg",
  4: "/maps/gyeongsam-4f.svg",
};

/*
 * 지도 확대 배율
 *
 * 1.15 = 15% 확대
 * 1.25 = 25% 확대
 * 1.35 = 35% 확대
 */
const MAP_ZOOM = 1.25;

/* =========================================================
   경로 표시
========================================================= */

function RouteLayer({
  routePath = [],
  floor,
  routeColor = "#e85b55",
}) {
  const pathNodes = getPathNodesForFloor(routePath, floor);

  if (pathNodes.length === 0) {
    return null;
  }

  /*
   * 중간 꺾임점을 포함한 전체 좌표
   */
  const points = pathNodes
    .map((node) => `${node.x},${node.y}`)
    .join(" ");

  /*
   * 움직이는 동그라미가 따라갈 SVG 경로
   */
  const pathData = pathNodes
    .map((node, index) => {
      const command = index === 0 ? "M" : "L";

      return `${command} ${node.x} ${node.y}`;
    })
    .join(" ");

  /*
   * 화면용 꺾임점이 아닌 실제 백엔드 노드만 추출
   */
  const realNodes = pathNodes.filter(
    (node) => !node.isWaypoint,
  );

  /*
   * 전체 경로의 진짜 출발 노드와 진짜 목적지 노드
   *
   * 예:
   * 전체 경로가
   * 1층 출발 → 1층 엘리베이터 → 3층 엘리베이터 → 열람실
   *
   * 이라면:
   * globalStartNodeId = 1층 출발점
   * globalDestinationNodeId = 3층 열람실
   */
  const globalStartNodeId = routePath[0] ?? null;

  const globalDestinationNodeId =
    routePath.length > 0
      ? routePath[routePath.length - 1]
      : null;

  /*
   * 현재 층에 전체 경로의 진짜 출발점이 있는지 확인
   */
  const startNode =
    realNodes.find(
      (node) => node.nodeId === globalStartNodeId,
    ) ?? null;

  /*
   * 현재 층에 전체 경로의 진짜 목적지가 있는지 확인
   *
   * 따라서 1층 엘리베이터 앞에는 도착이 표시되지 않고,
   * 최종 목적지인 3층 노트북 열람실에만 도착이 표시됩니다.
   */
  const destinationNode =
    realNodes.find(
      (node) =>
        node.nodeId === globalDestinationNodeId,
    ) ?? null;

  return (
    <g className="route-layer">
      {/*
        움직이는 점선 애니메이션
      */}
      <style>
        {`
          @keyframes pathTwinDashMove {
            to {
              stroke-dashoffset: -34;
            }
          }

          .path-twin-route-line {
            animation: pathTwinDashMove 1.05s linear infinite;
          }

          .path-twin-moving-marker {
            filter:
              drop-shadow(
                0 2px 3px rgba(31, 39, 72, 0.28)
              );
          }
        `}
      </style>

      {pathNodes.length >= 2 && (
        <>
          {/*
            경로 아래의 흰색 테두리

            지도 글자나 방 테두리 위에서도
            경로가 잘 보이게 합니다.
          */}
          <polyline
            points={points}
            fill="none"
            stroke="rgba(255, 255, 255, 0.96)"
            strokeWidth="15"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/*
            실제 움직이는 점선 경로
          */}
          <polyline
            points={points}
            fill="none"
            stroke={routeColor}
            strokeWidth="8"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray="18 10"
            className="path-twin-route-line"
          />

          {/*
            경로를 따라 움직이는 작은 마커
          */}
          <circle
            r="5.5"
            fill="#ffffff"
            stroke={routeColor}
            strokeWidth="3"
            className="path-twin-moving-marker"
          >
            <animateMotion
              dur="4.2s"
              repeatCount="indefinite"
              path={pathData}
            />
          </circle>
        </>
      )}

      {/*
        실제 전체 경로의 출발점이 현재 층에 있을 때만 표시

        1층 출발이라면 1층에만 표시됩니다.
      */}
      {startNode && (
        <g className="route-start-marker">
          <circle
            cx={startNode.x}
            cy={startNode.y}
            r="12"
            fill={routeColor}
            stroke="#ffffff"
            strokeWidth="4"
          />

          <text
            x={startNode.x}
            y={startNode.y - 20}
            textAnchor="middle"
            className="route-marker-label"
          >
            출발
          </text>
        </g>
      )}

      {/*
        전체 경로의 최종 목적지가 현재 층에 있을 때만 표시

        목적지가 3층 노트북 열람실이라면
        1층과 2층에는 절대 도착이 뜨지 않습니다.
      */}
      {destinationNode && (
        <g className="route-destination-marker">
          <circle
            cx={destinationNode.x}
            cy={destinationNode.y}
            r="12"
            fill={routeColor}
            stroke="#ffffff"
            strokeWidth="4"
          />

          <text
            x={destinationNode.x}
            y={destinationNode.y - 20}
            textAnchor="middle"
            className="route-marker-label"
          >
            도착
          </text>
        </g>
      )}
    </g>
  );
}

/* =========================================================
   범례 아이콘
========================================================= */

function MiniThresholdIcon() {
  return (
    <span
      className="legend-color-box"
      style={{
        backgroundColor: "#80f26b",
      }}
      aria-hidden="true"
    />
  );
}

function MediumThresholdIcon() {
  return (
    <span
      className="legend-color-box"
      style={{
        backgroundColor: "#ed8b2c",
      }}
      aria-hidden="true"
    />
  );
}

function ElevatorIcon() {
  return (
    <svg
      className="legend-svg-icon"
      viewBox="0 0 36 36"
      aria-hidden="true"
    >
      <rect
        x="5"
        y="3"
        width="26"
        height="30"
        rx="4"
        fill="#ffffff"
        stroke="#182b55"
        strokeWidth="2"
      />

      <path
        d="M12 11V6M12 6L9 9M12 6L15 9"
        fill="none"
        stroke="#182b55"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <path
        d="M24 6V11M24 11L21 8M24 11L27 8"
        fill="none"
        stroke="#182b55"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <circle
        cx="13"
        cy="17"
        r="2.2"
        fill="#182b55"
      />

      <circle
        cx="23"
        cy="17"
        r="2.2"
        fill="#182b55"
      />

      <path
        d="M10 21H16V29H10ZM20 21H26V29H20Z"
        fill="#182b55"
      />
    </svg>
  );
}

function AccessibleRouteIcon() {
  return (
    <span
      className="legend-accessibility-icon"
      aria-hidden="true"
    >
      ♿
    </span>
  );
}

/* =========================================================
   범례
========================================================= */

function MapLegend() {
  return (
    <div
      className="map-legend"
      aria-label="지도 범례"
    >
      <strong className="map-legend-title">
        범례
      </strong>

      <div className="map-legend-list">
        <div className="map-legend-item">
          <MiniThresholdIcon />
          <span>턱 미니</span>
        </div>

        <div className="map-legend-item">
          <MediumThresholdIcon />
          <span>턱 중간</span>
        </div>

        <div className="map-legend-item">
          <ElevatorIcon />
          <span>엘리베이터</span>
        </div>

        <div className="map-legend-item">
          <AccessibleRouteIcon />
          <span>장애인 통로</span>
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   FloorMap 컴포넌트
========================================================= */

export default function FloorMap({
  floor = 1,
  routePath = [],
  routeColor = "#e85b55",
  showLegend = true,
}) {
  const map = getFloorMap(floor);

  const floorImage =
    FLOOR_IMAGE_PATHS[floor] ??
    FLOOR_IMAGE_PATHS[1];

  return (
    <section className="floor-map-section">
      {/*
        지도 제목
      */}
      <div className="floor-map-header">
        <div>
          <p className="floor-map-eyebrow">
            경삼관 실내 안내 지도
          </p>

          <h2>
            {map?.title ??
              `경삼관 ${floor}층`}
          </h2>

          {map?.description && (
            <p className="floor-map-description">
              {map.description}
            </p>
          )}
        </div>

        <div
          className="floor-map-current-floor"
          aria-label={`현재 ${floor}층`}
        >
          <span>{floor}</span>
          <small>F</small>
        </div>
      </div>

      {/*
        지도 표시 영역
      */}
      <div className="floor-map-scroll-area">
        <div className="floor-map-canvas-wrap">
          <div className="floor-map-viewport">
            <div
              className="floor-map-stage"
              style={{
                transform: `scale(${MAP_ZOOM})`,
              }}
            >
              {/*
                Figma에서 만든 층별 SVG 지도
              */}
              <img
                src={floorImage}
                alt={`경삼관 ${floor}층 실내 지도`}
                className="floor-map-image"
                draggable="false"
              />

              {/*
                지도 위 경로 오버레이
              */}
              <svg
                viewBox={`0 0 ${MAP_SIZE.width} ${MAP_SIZE.height}`}
                preserveAspectRatio="xMidYMid meet"
                className="floor-map-route-overlay"
                aria-hidden="true"
              >
                <RouteLayer
                  routePath={routePath}
                  floor={floor}
                  routeColor={routeColor}
                />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {showLegend && <MapLegend />}

      <p className="map-disclaimer">
        실제 건축 도면이 아닌 접근성 경로
        시뮬레이션을 위한 간략 안내 지도입니다.
      </p>
    </section>
  );
}