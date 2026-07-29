// src/components/FloorMap.jsx

import {
  MAP_SIZE,
  getFloorMap,
  getNodePosition,
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
 */
const MAP_ZOOM = 1.25;

/*
 * 층별 이동시설 기본 위치
 *
 * 해당 층의 실제 노드 좌표를 찾지 못했을 때만
 * 아래 좌표를 대체값으로 사용합니다.
 */
const TRANSITION_FALLBACK_POSITIONS = {
  elevator: {
    1: { x: 790, y: 335 },
    2: { x: 790, y: 335 },
    3: { x: 790, y: 340 },
    4: { x: 790, y: 340 },
  },

  stairs: {
    1: { x: 700, y: 325 },
    2: { x: 700, y: 285 },
    3: { x: 700, y: 330 },
    4: { x: 700, y: 330 },
  },
};

/* =========================================================
   이동수단 판별
========================================================= */

function getTransitionType(startNodeId, endNodeId) {
  const combinedId = `${startNodeId ?? ""} ${endNodeId ?? ""}`;

  if (
    combinedId.includes("엘리베이터") ||
    combinedId.toLowerCase().includes("elevator")
  ) {
    return "elevator";
  }

  if (
    combinedId.includes("계단") ||
    combinedId.toLowerCase().includes("stairs")
  ) {
    return "stairs";
  }

  return "floor-transition";
}

/* =========================================================
   현재 층에서 사용할 이동시설 위치 찾기
========================================================= */

function getTransitionPosition(floor, transitionType, routePath = []) {
  /*
   * mapData.js에 실제 해당 층 노드가 있으면
   * 그 좌표를 가장 먼저 사용합니다.
   */
  const usesReadingRoomSideStairs = routePath.some((nodeId) =>
    [
      "쪽길_시작노드(개구멍)",
      "쪽계단_아래",
      "열람실_긴계단_아래(동관쪽길)",
      "구름다리_입구",
      "구름다리_출구(서관2층)",
      "3층_쪽계단위",
    ].includes(nodeId),
  );

  let candidateNodeIds;

  if (transitionType === "elevator") {
    candidateNodeIds = [
      `서관_${floor}층_엘리베이터앞`,
      `${floor}층_엘리베이터앞`,
      `동관_${floor}층_엘리베이터앞`,
    ];
  } else if (usesReadingRoomSideStairs) {
    const readingRoomStairNodesByFloor = {
      1: [
        "열람실_긴계단_아래(동관쪽길)",
        "쪽계단_아래",
      ],
      2: ["구름다리_출구(서관2층)"],
      3: ["3층_쪽계단위"],
    };

    candidateNodeIds = readingRoomStairNodesByFloor[floor] ?? [];
  } else {
    candidateNodeIds = [
      `서관_${floor}층_계단앞`,
      `동관_${floor}층_계단앞`,
      `${floor}층_계단앞`,
    ];
  }

  for (const nodeId of candidateNodeIds) {
    const position = getNodePosition(nodeId);

    if (position && position.floor === floor) {
      return {
        x: position.x,
        y: position.y,
      };
    }
  }

  /*
   * 실제 노드를 찾지 못하면 기본 좌표 사용
   */
  return (
    TRANSITION_FALLBACK_POSITIONS[transitionType]?.[floor] ??
    TRANSITION_FALLBACK_POSITIONS.elevator[floor] ?? {
      x: 790,
      y: 340,
    }
  );
}

/* =========================================================
   현재 층이 중간 통과층인지 확인
========================================================= */

function getIntermediateFloorTransition(routePath, floor) {
  if (!Array.isArray(routePath) || routePath.length < 2) {
    return null;
  }

  for (let index = 0; index < routePath.length - 1; index += 1) {
    const startNodeId = routePath[index];
    const endNodeId = routePath[index + 1];

    const startPosition = getNodePosition(startNodeId);
    const endPosition = getNodePosition(endNodeId);

    if (!startPosition || !endPosition) {
      continue;
    }

    if (startPosition.floor === endPosition.floor) {
      continue;
    }

    const lowerFloor = Math.min(
      startPosition.floor,
      endPosition.floor,
    );

    const upperFloor = Math.max(
      startPosition.floor,
      endPosition.floor,
    );

    /*
     * 출발층과 도착층 사이에 있는 층만
     * 중간 통과층으로 처리합니다.
     *
     * 예:
     * 1층 → 3층
     * 현재 floor가 2라면 중간층
     */
    const isIntermediateFloor =
      floor > lowerFloor && floor < upperFloor;

    if (!isIntermediateFloor) {
      continue;
    }

    const transitionType = getTransitionType(
      startNodeId,
      endNodeId,
    );

    return {
      type: transitionType,
      direction:
        endPosition.floor > startPosition.floor
          ? "up"
          : "down",
      fromFloor: startPosition.floor,
      toFloor: endPosition.floor,
      position: getTransitionPosition(
        floor,
        transitionType,
        routePath,
      ),
    };
  }

  return null;
}

/* =========================================================
   움직이는 중간층 표시
========================================================= */

function IntermediateFloorMarker({
  transition,
  routeColor,
}) {
  if (!transition) {
    return null;
  }

  const { type, direction, position, fromFloor, toFloor } =
    transition;

  const isElevator = type === "elevator";
  const isStairs = type === "stairs";

  const label = isElevator
    ? "엘리베이터 이동 중"
    : isStairs
      ? "계단 이동 중"
      : "층간 이동 중";

  const icon = isElevator
    ? "↕"
    : direction === "up"
      ? "↑"
      : "↓";

  return (
    <g className="intermediate-floor-layer">
      <style>
        {`
          @keyframes pathTwinTransitPulse {
            0% {
              opacity: 0.45;
              transform: scale(0.86);
            }

            50% {
              opacity: 1;
              transform: scale(1.12);
            }

            100% {
              opacity: 0.45;
              transform: scale(0.86);
            }
          }

          @keyframes pathTwinTransitDash {
            to {
              stroke-dashoffset: -28;
            }
          }

          .path-twin-transit-pulse {
            transform-box: fill-box;
            transform-origin: center;
            animation:
              pathTwinTransitPulse 1.35s
              ease-in-out infinite;
          }

          .path-twin-transit-line {
            animation:
              pathTwinTransitDash 0.9s
              linear infinite;
          }
        `}
      </style>

      {/*
        이동시설을 통과 중이라는 짧은 점선
      */}
      <line
        x1={position.x}
        y1={position.y - 38}
        x2={position.x}
        y2={position.y + 38}
        stroke="rgba(255,255,255,0.98)"
        strokeWidth="15"
        strokeLinecap="round"
      />

      <line
        x1={position.x}
        y1={position.y - 38}
        x2={position.x}
        y2={position.y + 38}
        stroke={routeColor}
        strokeWidth="8"
        strokeLinecap="round"
        strokeDasharray="15 9"
        className="path-twin-transit-line"
      />

      {/*
        이동시설 중앙의 움직이는 빨간 마커
      */}
      <g className="path-twin-transit-pulse">
        <circle
          cx={position.x}
          cy={position.y}
          r="15"
          fill="#ffffff"
          stroke={routeColor}
          strokeWidth="4"
        />

        <circle
          cx={position.x}
          cy={position.y}
          r="9"
          fill={routeColor}
        />
      </g>

      {/*
        위아래 이동 아이콘
      */}
      <g>
        <rect
          x={position.x - 17}
          y={position.y - 68}
          width="34"
          height="27"
          rx="9"
          fill="#ffffff"
          stroke={routeColor}
          strokeWidth="2.5"
        />

        <text
          x={position.x}
          y={position.y - 49}
          textAnchor="middle"
          fill={routeColor}
          fontSize="18"
          fontWeight="900"
        >
          {icon}
        </text>
      </g>

      {/*
        이동 중 안내문
      */}
      <g>
        <rect
          x={position.x - 75}
          y={position.y + 49}
          width="150"
          height="50"
          rx="16"
          fill="#ffffff"
          stroke={routeColor}
          strokeWidth="2.5"
        />

        <text
          x={position.x}
          y={position.y + 70}
          textAnchor="middle"
          fill="#202331"
          fontSize="14"
          fontWeight="900"
        >
          {label}
        </text>

        <text
          x={position.x}
          y={position.y + 88}
          textAnchor="middle"
          fill="#747d92"
          fontSize="11"
          fontWeight="800"
        >
          {fromFloor}층 → {toFloor}층
        </text>
      </g>
    </g>
  );
}

/* =========================================================
   실제 경로 표시
========================================================= */

function RouteLayer({
  routePath = [],
  floor,
  routeColor = "#e85b55",
}) {
  const pathNodes = getPathNodesForFloor(
    routePath,
    floor,
  );

  /*
   * 현재 층에 실제 노드는 없지만
   * 다른 층으로 이동하면서 지나가는 층인지 검사
   */
  const intermediateTransition =
    getIntermediateFloorTransition(routePath, floor);

  const globalStartNodeId =
    routePath.length > 0 ? routePath[0] : null;

  const globalDestinationNodeId =
    routePath.length > 0
      ? routePath[routePath.length - 1]
      : null;

  /*
   * 현재 층에 실제 경로가 없는 경우에도
   * 중간층 표시가 있으면 렌더링합니다.
   */
  if (
    pathNodes.length === 0 &&
    !intermediateTransition
  ) {
    return null;
  }

  if (pathNodes.length === 0) {
    return (
      <IntermediateFloorMarker
        transition={intermediateTransition}
        routeColor={routeColor}
      />
    );
  }

  const points = pathNodes
    .map((node) => `${node.x},${node.y}`)
    .join(" ");

  const pathData = pathNodes
    .map((node, index) => {
      const command = index === 0 ? "M" : "L";

      return `${command} ${node.x} ${node.y}`;
    })
    .join(" ");

  const realNodes = pathNodes.filter(
    (node) => !node.isWaypoint,
  );

  const startNode =
    realNodes.find(
      (node) =>
        node.nodeId === globalStartNodeId,
    ) ?? null;

  const destinationNode =
    realNodes.find(
      (node) =>
        node.nodeId === globalDestinationNodeId,
    ) ?? null;

  return (
    <g className="route-layer">
      <style>
        {`
          @keyframes pathTwinDashMove {
            to {
              stroke-dashoffset: -34;
            }
          }

          .path-twin-route-line {
            animation:
              pathTwinDashMove 1.05s
              linear infinite;
          }

          .path-twin-moving-marker {
            filter:
              drop-shadow(
                0 2px 3px
                rgba(31, 39, 72, 0.28)
              );
          }
        `}
      </style>

      {pathNodes.length >= 2 && (
        <>
          {/*
            흰색 외곽선
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
            움직이는 빨간 점선
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
            경로를 따라 움직이는 작은 점
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
        전체 경로의 진짜 출발지에서만 표시
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
        전체 경로의 최종 목적지에서만 표시
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

      {/*
        현재 층에 실제 경로도 있고,
        동시에 더 위/아래 층으로 이동 중인 정보가 있다면
        이동시설 표시도 함께 출력합니다.
      */}
      {intermediateTransition && (
        <IntermediateFloorMarker
          transition={intermediateTransition}
          routeColor={routeColor}
        />
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
   FloorMap
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
      <div className="floor-map-header">
        <div>
          <p className="floor-map-eyebrow">
            경삼관 실내 안내 지도
          </p>

          <h2>
            {map?.title ??
              `경삼관 ${floor}층`}
          </h2>
        </div>

        <div
          className="floor-map-current-floor"
          aria-label={`현재 ${floor}층`}
        >
          <span>{floor}</span>
          <small>F</small>
        </div>
      </div>

      <div className="floor-map-scroll-area">
        <div className="floor-map-canvas-wrap">
          <div className="floor-map-viewport">
            <div
              className="floor-map-stage"
              style={{
                transform: `scale(${MAP_ZOOM})`,
              }}
            >
              <img
                src={floorImage}
                alt={`경삼관 ${floor}층 실내 지도`}
                className="floor-map-image"
                draggable="false"
              />

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