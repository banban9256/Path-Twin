import { useEffect, useMemo, useState } from "react";
import "./App.css";

const profileOptions = [
  {
    value: "general",
    label: "일반 보행자",
    icon: "🚶",
    description: "별도의 이동 제약 없이 이동합니다.",
  },
  {
    value: "wheelchair",
    label: "휠체어 사용자",
    icon: "♿",
    description: "계단과 높은 턱을 제외한 경로가 필요합니다.",
  },
  {
    value: "crutches",
    label: "목발 사용자",
    icon: "🩼",
    description: "긴 계단과 급한 경사를 피하는 것이 좋습니다.",
  },
  {
    value: "stroller",
    label: "유아차 이용자",
    icon: "👶",
    description: "넓은 복도와 엘리베이터 중심 경로가 필요합니다.",
  },
  {
    value: "luggage",
    label: "무거운 짐 소지자",
    icon: "🧳",
    description: "계단보다 엘리베이터 이용이 편리합니다.",
  },
];

const priorityOptions = [
  {
    value: "fast",
    title: "무조건 빨리 도착할래요",
    description: "이동 시간이 짧은 경로를 우선 추천합니다.",
    icon: "⚡",
  },
  {
    value: "comfort",
    title: "조금 느려도 편하게 갈래요",
    description: "계단, 턱, 긴 이동 구간을 줄인 경로를 추천합니다.",
    icon: "🌿",
  },
];

const locations = [
  {
    value: "east-accessible-entrance",
    label: "동관 장애인 통로 1",
    floor: 1,
    mapPoint: "eastEntrance",
  },
  {
    value: "east-accessible-entrance-2",
    label: "동관 장애인 통로 2",
    floor: 1,
    mapPoint: "eastEntrance2",
  },
  {
    value: "west-accessible-entrance",
    label: "서관 장애인 통로",
    floor: 1,
    mapPoint: "westEntrance",
  },
  {
    value: "east-main-entrance",
    label: "경삼관 동관 입구",
    floor: 1,
    mapPoint: "eastMain",
  },
  {
    value: "west-main-entrance",
    label: "경삼관 서관 입구",
    floor: 1,
    mapPoint: "westMain",
  },
  {
    value: "room-6121",
    label: "1층 동관 로비",
    floor: 1,
    mapPoint: "eastRoom",
  },
  {
    value: "room-6101",
    label: "1층 학생행복라운지",
    floor: 1,
    mapPoint: "westRoom",
  },
  {
    value: "room-6221",
    label: "2층 자료실 1",
    floor: 2,
    mapPoint: "eastRoom",
  },
  {
    value: "room-6201",
    label: "2층 IPP센터",
    floor: 2,
    mapPoint: "westRoom",
  },
  {
    value: "room-6204",
    label: "2층 대학행정팀",
    floor: 2,
    mapPoint: "southWestRoom",
  },
  {
    value: "room-6321",
    label: "3층 자료실 2",
    floor: 3,
    mapPoint: "eastRoom",
  },
  {
    value: "room-6305",
    label: "3층 노트북 열람실 1",
    floor: 3,
    mapPoint: "westRoom",
  },
  {
    value: "room-6421",
    label: "4층 북카페",
    floor: 4,
    mapPoint: "eastRoom",
  },
  {
    value: "room-6423",
    label: "4층 소극장",
    floor: 4,
    mapPoint: "southEastRoom",
  },
  {
    value: "room-6425",
    label: "4층 한신갤러리",
    floor: 4,
    mapPoint: "westRoom",
  },
];

const floorRooms = {
  1: [
    { x: 55, y: 70, width: 160, height: 80, label: "6124\n회의실" },
    { x: 55, y: 175, width: 180, height: 105, label: "6121\n동관 로비" },
    { x: 55, y: 305, width: 190, height: 90, label: "6126\n밀집서고실 1" },
    { x: 455, y: 65, width: 190, height: 90, label: "6102\n일자리센터" },
    { x: 475, y: 180, width: 170, height: 90, label: "6101\n행복라운지" },
    { x: 420, y: 300, width: 225, height: 95, label: "6106\n박물관 전시실" },
  ],
  2: [
    { x: 55, y: 70, width: 180, height: 110, label: "6221\n자료실 1" },
    { x: 55, y: 285, width: 190, height: 110, label: "6223\n학생상담센터" },
    { x: 455, y: 65, width: 190, height: 100, label: "6201\nIPP센터" },
    { x: 470, y: 190, width: 175, height: 80, label: "6202\n교수학습지원센터" },
    { x: 430, y: 300, width: 215, height: 95, label: "6204\n대학행정팀" },
  ],
  3: [
    { x: 55, y: 70, width: 190, height: 120, label: "6321\n자료실 2" },
    { x: 55, y: 285, width: 190, height: 110, label: "6324\nJOB SPACE" },
    { x: 455, y: 65, width: 190, height: 100, label: "6305\n노트북 열람실 1" },
    { x: 470, y: 190, width: 175, height: 80, label: "6306\n노트북 열람실 2" },
    { x: 430, y: 300, width: 215, height: 95, label: "6307\n열람실 3" },
  ],
  4: [
    { x: 55, y: 70, width: 190, height: 120, label: "6421\n북카페" },
    { x: 55, y: 285, width: 190, height: 110, label: "6423\n소극장" },
    { x: 455, y: 65, width: 190, height: 100, label: "6422\n멀티미디어실" },
    { x: 470, y: 190, width: 175, height: 80, label: "6425\n한신갤러리" },
    { x: 430, y: 300, width: 215, height: 95, label: "6426\n국제교류원" },
  ],
};

const destinationPoints = {
  eastRoom: [140, 220],
  westRoom: [555, 220],
  southWestRoom: [535, 350],
  southEastRoom: [145, 350],
  eastEntrance: [675, 345],
  eastEntrance2: [40, 345],
  westEntrance: [675, 80],
  eastMain: [350, 420],
  westMain: [350, 35],
};

const verticalCorePoints = {
  elevator: [405, 245],
  eastStairs: [330, 205],
  westStairs: [330, 295],
};

function getLocation(value) {
  return locations.find((location) => location.value === value);
}

function createRouteOptions(profile, priority, startLocation, destination) {
  const start = getLocation(startLocation);
  const end = getLocation(destination);

  if (!start || !end) {
    return [];
  }

  const floorDifference = Math.abs(end.floor - start.floor);
  const sameFloor = floorDifference === 0;

  const elevatorRoute = {
    id: "elevator",
    title: "엘리베이터 중심 경로",
    subtitle: "계단을 피하고 편안하게 이동",
    method: "elevator",
    icon: "🛗",
    totalSeconds: sameFloor ? 230 : 340 + floorDifference * 55,
    safetyScore: 96,
    tag: priority === "comfort" ? "추천" : "편안한 경로",
    warnings: [
      "엘리베이터 대기 시간에 따라 소요 시간이 달라질 수 있습니다.",
      "출입구 주변의 낮은 턱을 주의해 주세요.",
    ],
  };

  const eastStairsRoute = {
    id: "east-stairs",
    title: "동관 중앙계단 경로",
    subtitle: "동관 계단을 이용하는 빠른 경로",
    method: "eastStairs",
    icon: "🪜",
    totalSeconds: sameFloor ? 190 : 245 + floorDifference * 38,
    safetyScore: 78,
    tag: priority === "fast" ? "가장 빠름" : "빠른 경로",
    warnings: [
      "동관 중앙계단 이용 구간이 포함됩니다.",
      "계단 혼잡 시 이동 시간이 늘어날 수 있습니다.",
    ],
  };

  const westStairsRoute = {
    id: "west-stairs",
    title: "서관 중앙계단 경로",
    subtitle: "서관 쪽계단을 이용하는 대안 경로",
    method: "westStairs",
    icon: "↗️",
    totalSeconds: sameFloor ? 205 : 270 + floorDifference * 40,
    safetyScore: 82,
    tag: "대안 경로",
    warnings: [
      "서관 중앙계단 또는 쪽계단 이용 구간이 포함됩니다.",
      "계단 폭과 이용자 통행을 주의해 주세요.",
    ],
  };

  if (profile === "wheelchair" || profile === "stroller") {
    return [
      {
        ...elevatorRoute,
        tag: "추천",
      },
    ];
  }

  if (profile === "crutches" || profile === "luggage") {
    return priority === "fast"
      ? [eastStairsRoute, elevatorRoute, westStairsRoute]
      : [elevatorRoute, westStairsRoute, eastStairsRoute];
  }

  return priority === "fast"
    ? [eastStairsRoute, westStairsRoute, elevatorRoute]
    : [elevatorRoute, westStairsRoute, eastStairsRoute];
}

function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainSeconds = seconds % 60;

  return `${minutes}분 ${remainSeconds}초`;
}

function buildTimeline(route, startLocation, destination) {
  const start = getLocation(startLocation);
  const end = getLocation(destination);
  const sameFloor = start.floor === end.floor;

  const firstStep = {
    title: start.label,
    description: `${start.floor}층 출발지에서 이동을 시작합니다.`,
    time: "50초",
    type: "start",
  };

  if (sameFloor) {
    return [
      firstStep,
      {
        title: `${start.floor}층 중앙 복도`,
        description: "같은 층의 중앙 복도를 따라 이동합니다.",
        time: "1분 20초",
        type: "walk",
      },
      {
        title: end.label,
        description: "목적지에 도착합니다.",
        time: "1분",
        type: "destination",
      },
    ];
  }

  const movingMethod = {
    elevator: {
      title: "경삼관 엘리베이터",
      description: `${start.floor}층에서 ${end.floor}층까지 엘리베이터로 이동합니다.`,
      time: "2분",
      type: "elevator",
    },
    eastStairs: {
      title: "동관 중앙계단",
      description: `${start.floor}층에서 ${end.floor}층까지 동관 중앙계단으로 이동합니다.`,
      time: "1분 20초",
      type: "stairs",
    },
    westStairs: {
      title: "서관 중앙계단",
      description: `${start.floor}층에서 ${end.floor}층까지 서관 쪽계단으로 이동합니다.`,
      time: "1분 35초",
      type: "stairs",
    },
  };

  return [
    firstStep,
    {
      title: `${start.floor}층 중앙 복도`,
      description: `${movingMethod[route.method].title} 방향으로 이동합니다.`,
      time: "1분 10초",
      type: "walk",
    },
    movingMethod[route.method],
    {
      title: `${end.floor}층 중앙 복도`,
      description: `${end.floor}층에서 목적지 방향으로 이동합니다.`,
      time: "1분 10초",
      type: "walk",
    },
    {
      title: end.label,
      description: "목적지에 도착합니다.",
      time: "50초",
      type: "destination",
    },
  ];
}

function createReason(profile, priority, route, destination) {
  const profileName =
    profileOptions.find((option) => option.value === profile)?.label ??
    "사용자";

  const priorityText =
    priority === "fast"
      ? "이동 시간을 우선하여"
      : "편안하고 안전한 이동을 우선하여";

  const methodText = {
    elevator: "계단을 제외하고 엘리베이터를 이용하는",
    eastStairs: "동관 중앙계단을 활용해 이동 시간을 줄이는",
    westStairs: "서관 중앙계단을 이용해 혼잡 구간을 분산하는",
  };

  return `${profileName}의 이동 조건과 선택한 이동 성향을 반영했습니다. ${priorityText} ${methodText[route.method]} 경로를 추천하며, 목적지인 ${getLocation(destination).label}까지의 구간별 이동 정보를 함께 제공합니다.`;
}

const stepIcons = {
  start: "🚩",
  walk: "🚶",
  stairs: "🪜",
  elevator: "🛗",
  destination: "📍",
};

function FloorMap({
  floor,
  activeRoute,
  startLocation,
  destination,
  hasSimulation,
}) {
  const start = getLocation(startLocation);
  const end = getLocation(destination);

  const startPoint =
    start.floor === floor
      ? destinationPoints[start.mapPoint] ?? [350, 420]
      : verticalCorePoints[activeRoute?.method] ?? verticalCorePoints.elevator;

  const endPoint =
    end.floor === floor
      ? destinationPoints[end.mapPoint] ?? [555, 220]
      : verticalCorePoints[activeRoute?.method] ?? verticalCorePoints.elevator;

  const corePoint =
    verticalCorePoints[activeRoute?.method] ?? verticalCorePoints.elevator;

  let routePoints = "";

  if (hasSimulation && activeRoute) {
    if (start.floor === end.floor && floor === start.floor) {
      routePoints = `${startPoint[0]},${startPoint[1]} 350,${startPoint[1]} 350,${endPoint[1]} ${endPoint[0]},${endPoint[1]}`;
    } else if (floor === start.floor) {
      routePoints = `${startPoint[0]},${startPoint[1]} 350,${startPoint[1]} 350,${corePoint[1]} ${corePoint[0]},${corePoint[1]}`;
    } else if (floor === end.floor) {
      routePoints = `${corePoint[0]},${corePoint[1]} 350,${corePoint[1]} 350,${endPoint[1]} ${endPoint[0]},${endPoint[1]}`;
    } else if (
      floor > Math.min(start.floor, end.floor) &&
      floor < Math.max(start.floor, end.floor)
    ) {
      routePoints = `${corePoint[0]},${corePoint[1] - 50} ${corePoint[0]},${corePoint[1] + 50}`;
    }
  }

  return (
    <div className="map-wrapper">
      <svg
        className="floor-map"
        viewBox="0 0 700 450"
        role="img"
        aria-label={`경삼관 ${floor}층 간략 지도`}
      >
        <rect
          x="25"
          y="25"
          width="650"
          height="400"
          rx="26"
          className="building-outline"
        />

        <text x="48" y="55" className="wing-label">
          동관
        </text>

        <text x="610" y="55" className="wing-label">
          서관
        </text>

        <rect x="255" y="105" width="190" height="240" className="core-area" />

        <text x="350" y="132" textAnchor="middle" className="core-label">
          중앙 이동 구역
        </text>

        <rect x="305" y="168" width="52" height="72" rx="10" className="stair" />
        <text x="331" y="197" textAnchor="middle" className="facility-icon">
          🪜
        </text>
        <text x="331" y="222" textAnchor="middle" className="facility-label">
          동관 계단
        </text>

        <rect x="305" y="260" width="52" height="72" rx="10" className="stair" />
        <text x="331" y="289" textAnchor="middle" className="facility-icon">
          🪜
        </text>
        <text x="331" y="314" textAnchor="middle" className="facility-label">
          서관 계단
        </text>

        <rect
          x="378"
          y="208"
          width="55"
          height="76"
          rx="11"
          className="elevator"
        />
        <text x="405" y="240" textAnchor="middle" className="facility-icon">
          🛗
        </text>
        <text x="405" y="268" textAnchor="middle" className="facility-label">
          엘리베이터
        </text>

        {floorRooms[floor].map((room) => (
          <g key={`${floor}-${room.label}`}>
            <rect
              x={room.x}
              y={room.y}
              width={room.width}
              height={room.height}
              rx="12"
              className="room"
            />

            {room.label.split("\n").map((line, index) => (
              <text
                key={line}
                x={room.x + room.width / 2}
                y={room.y + room.height / 2 + index * 19 - 6}
                textAnchor="middle"
                className={index === 0 ? "room-number" : "room-name"}
              >
                {line}
              </text>
            ))}
          </g>
        ))}

        {floor === 1 && (
          <>
            <circle cx="350" cy="420" r="10" className="entrance-marker" />
            <text x="350" y="405" textAnchor="middle" className="entrance-label">
              동관 입구
            </text>

            <circle cx="350" cy="35" r="10" className="entrance-marker" />
            <text x="350" y="65" textAnchor="middle" className="entrance-label">
              서관 입구
            </text>

            <rect x="20" y="326" width="30" height="38" rx="7" className="access" />
            <text x="60" y="350" className="access-label">
              장애인 통로 2
            </text>

            <rect
              x="650"
              y="326"
              width="30"
              height="38"
              rx="7"
              className="access"
            />
            <text x="530" y="350" className="access-label">
              장애인 통로 1
            </text>

            <rect x="650" y="62" width="30" height="38" rx="7" className="access" />
            <text x="520" y="88" className="access-label">
              서관 장애인 통로
            </text>
          </>
        )}

        {routePoints && (
          <>
            <polyline points={routePoints} className="route-shadow" />
            <polyline points={routePoints} className="route-line" />
          </>
        )}

        {hasSimulation && start.floor === floor && (
          <g>
            <circle cx={startPoint[0]} cy={startPoint[1]} r="13" className="start-dot" />
            <text
              x={startPoint[0]}
              y={startPoint[1] - 22}
              textAnchor="middle"
              className="point-label"
            >
              출발
            </text>
          </g>
        )}

        {hasSimulation && end.floor === floor && (
          <g>
            <circle cx={endPoint[0]} cy={endPoint[1]} r="13" className="end-dot" />
            <text
              x={endPoint[0]}
              y={endPoint[1] - 22}
              textAnchor="middle"
              className="point-label"
            >
              도착
            </text>
          </g>
        )}
      </svg>

      <div className="map-legend">
        <span>
          <i className="legend-line" /> 추천 이동 경로
        </span>
        <span>🛗 엘리베이터</span>
        <span>🪜 계단</span>
        <span>🟨 장애인 통로</span>
      </div>

      <p className="map-note">
        실제 건축 도면이 아닌, 경로 시뮬레이션 UI 검토를 위한 간략 구조도입니다.
      </p>
    </div>
  );
}

function App() {
  const [profile, setProfile] = useState("wheelchair");
  const [priority, setPriority] = useState("comfort");
  const [startLocation, setStartLocation] = useState(
    "east-accessible-entrance",
  );
  const [destination, setDestination] = useState("room-6221");

  const [selectedFloor, setSelectedFloor] = useState(2);
  const [routeOptions, setRouteOptions] = useState([]);
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [hasSimulation, setHasSimulation] = useState(false);

  const selectedProfile = profileOptions.find(
    (option) => option.value === profile,
  );

  const selectedPriority = priorityOptions.find(
    (option) => option.value === priority,
  );

  const selectedRoute = useMemo(
    () =>
      routeOptions.find((route) => route.id === selectedRouteId) ??
      routeOptions[0] ??
      null,
    [routeOptions, selectedRouteId],
  );

  const destinationInfo = getLocation(destination);

  useEffect(() => {
    if (destinationInfo) {
      setSelectedFloor(destinationInfo.floor);
    }
  }, [destination, destinationInfo]);

  const resetSimulation = () => {
    setHasSimulation(false);
    setRouteOptions([]);
    setSelectedRouteId(null);
  };

  const handleSimulation = () => {
    if (startLocation === destination) {
      window.alert("출발지와 목적지를 다르게 선택해 주세요.");
      return;
    }

    const routes = createRouteOptions(
      profile,
      priority,
      startLocation,
      destination,
    );

    setRouteOptions(routes);
    setSelectedRouteId(routes[0]?.id ?? null);
    setHasSimulation(true);
    setSelectedFloor(getLocation(destination).floor);
  };

  const timeline = selectedRoute
    ? buildTimeline(selectedRoute, startLocation, destination)
    : [];

  const recommendationReason = selectedRoute
    ? createReason(profile, priority, selectedRoute, destination)
    : "";

  return (
    <div className="app">
      <header className="service-header">
        <div className="header-inner">
          <div>
            <p className="service-label">접근성 경로 디지털 트윈</p>
            <h1>AI가 대신 가줍니다</h1>
            <p className="service-description">
              사용자의 이동 제약과 이동 성향을 반영해 경삼관 실내 이동 경로를
              미리 시뮬레이션합니다.
            </p>
          </div>

          <span className="dummy-badge">더미데이터 기반 2차 프로토타입</span>
        </div>
      </header>

      <main className="main-layout">
        <section className="panel input-panel">
          <div className="section-heading">
            <span className="section-number">1</span>

            <div>
              <h2>이동 조건 설정</h2>
              <p>사용자 상태, 이동 성향과 목적지를 설정해 주세요.</p>
            </div>
          </div>

          <div className="form-group">
            <label>사용자 프로필</label>

            <div className="profile-grid">
              {profileOptions.map((option) => (
                <button
                  type="button"
                  key={option.value}
                  className={`profile-card ${
                    profile === option.value ? "selected" : ""
                  }`}
                  onClick={() => {
                    setProfile(option.value);
                    resetSimulation();
                  }}
                >
                  <span className="profile-icon">{option.icon}</span>
                  <span>{option.label}</span>
                </button>
              ))}
            </div>

            <div className="profile-description">
              <span>{selectedProfile.icon}</span>
              <p>{selectedProfile.description}</p>
            </div>
          </div>

          <div className="form-group">
            <label>어떤 경로를 원하시나요?</label>

            <div className="priority-grid">
              {priorityOptions.map((option) => (
                <button
                  type="button"
                  key={option.value}
                  className={`priority-card ${
                    priority === option.value ? "selected" : ""
                  }`}
                  onClick={() => {
                    setPriority(option.value);
                    resetSimulation();
                  }}
                >
                  <span className="priority-icon">{option.icon}</span>

                  <span className="priority-text">
                    <strong>{option.title}</strong>
                    <small>{option.description}</small>
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="location-group">
            <div className="form-group">
              <label htmlFor="start-location">출발지</label>

              <select
                id="start-location"
                value={startLocation}
                onChange={(event) => {
                  setStartLocation(event.target.value);
                  resetSimulation();
                }}
              >
                {locations.map((location) => (
                  <option key={location.value} value={location.value}>
                    {location.floor}층 · {location.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="route-arrow">↓</div>

            <div className="form-group">
              <label htmlFor="destination">목적지</label>

              <select
                id="destination"
                value={destination}
                onChange={(event) => {
                  setDestination(event.target.value);
                  resetSimulation();
                }}
              >
                {locations.map((location) => (
                  <option key={location.value} value={location.value}>
                    {location.floor}층 · {location.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            type="button"
            className="simulate-button"
            onClick={handleSimulation}
          >
            경로 시뮬레이션 실행
          </button>

          <div className="current-setting">
            <strong>현재 설정</strong>
            <p>
              {selectedProfile.icon} {selectedProfile.label}
            </p>
            <p>
              {selectedPriority.icon} {selectedPriority.title}
            </p>
          </div>

          <p className="input-note">
            현재는 UI 검증용 가상 데이터입니다. 추후 팀원의 실제 그래프·경로
            계산 API 응답으로 교체할 예정입니다.
          </p>
        </section>

        <section className="panel result-panel">
          <div className="map-header">
            <div>
              <p className="map-label">경삼관 실내 디지털 트윈</p>
              <h2>{selectedFloor}층 지도</h2>
            </div>

            <div className="floor-tabs">
              {[1, 2, 3, 4].map((floor) => (
                <button
                  type="button"
                  key={floor}
                  className={selectedFloor === floor ? "active" : ""}
                  onClick={() => setSelectedFloor(floor)}
                >
                  {floor}F
                </button>
              ))}
            </div>
          </div>

          <FloorMap
            floor={selectedFloor}
            activeRoute={selectedRoute}
            startLocation={startLocation}
            destination={destination}
            hasSimulation={hasSimulation}
          />

          {!hasSimulation ? (
            <div className="map-empty-message">
              <span>🧭</span>
              <div>
                <strong>출발지와 목적지를 선택해 주세요.</strong>
                <p>
                  선택한 목적지가 있는 층의 지도를 먼저 보여주며, 시뮬레이션
                  실행 후 추천 경로가 지도 위에 표시됩니다.
                </p>
              </div>
            </div>
          ) : (
            <div className="simulation-results">
              <section className="route-choice-section">
                <div className="result-title-row">
                  <div>
                    <p className="result-label">추천 경로 후보</p>
                    <h3>원하는 경로를 선택해 비교해 보세요.</h3>
                  </div>

                  <span>{routeOptions.length}개 경로</span>
                </div>

                <div className="route-options">
                  {routeOptions.map((route) => (
                    <button
                      type="button"
                      key={route.id}
                      className={`route-option ${
                        selectedRoute?.id === route.id ? "selected" : ""
                      }`}
                      onClick={() => {
                        setSelectedRouteId(route.id);
                        setSelectedFloor(getLocation(destination).floor);
                      }}
                    >
                      <div className="route-option-top">
                        <span className="route-method-icon">{route.icon}</span>
                        <span className="route-tag">{route.tag}</span>
                      </div>

                      <strong>{route.title}</strong>
                      <p>{route.subtitle}</p>

                      <div className="route-meta">
                        <span>⏱ {formatTime(route.totalSeconds)}</span>
                        <span>🛡 {route.safetyScore}점</span>
                      </div>
                    </button>
                  ))}
                </div>
              </section>

              <section className="selected-route-summary">
                <div>
                  <span>선택된 경로</span>
                  <strong>{selectedRoute.title}</strong>
                  <p>
                    {getLocation(startLocation).label} →{" "}
                    {getLocation(destination).label}
                  </p>
                </div>

                <span className="selected-route-icon">{selectedRoute.icon}</span>
              </section>

              <div className="metric-grid">
                <article className="metric-card">
                  <span>총 소요 시간</span>
                  <strong>{formatTime(selectedRoute.totalSeconds)}</strong>
                  <p>현재 더미데이터 기준 예상값</p>
                </article>

                <article className="metric-card">
                  <span>경로 안전도</span>
                  <strong>{selectedRoute.safetyScore}점</strong>
                  <p>100점 만점의 가상 점수</p>
                </article>
              </div>

              <section className="result-section">
                <div className="result-title-row">
                  <div>
                    <p className="result-label">구간별 이동</p>
                    <h3>이동 타임라인</h3>
                  </div>

                  <span>{timeline.length}개 구간</span>
                </div>

                <ol className="timeline">
                  {timeline.map((step, index) => (
                    <li
                      key={`${step.title}-${index}`}
                      className="timeline-item"
                    >
                      <div className="timeline-marker">
                        {stepIcons[step.type]}
                      </div>

                      <div className="timeline-content">
                        <div className="timeline-top">
                          <strong>{step.title}</strong>
                          <span>{step.time}</span>
                        </div>

                        <p>{step.description}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              </section>

              <section className="result-section">
                <p className="result-label">이동 전 확인</p>
                <h3>주의 요소</h3>

                <ul className="warning-list">
                  {selectedRoute.warnings.map((warning) => (
                    <li key={warning}>⚠️ {warning}</li>
                  ))}
                </ul>
              </section>

              <section className="ai-reason">
                <div className="ai-title">
                  <span>AI</span>
                  <h3>한국어 추천 사유</h3>
                </div>

                <p>{recommendationReason}</p>

                <small>
                  현재 문장은 생성형 AI 연결 전의 가상 문장입니다. 추후 실제
                  AI 응답으로 교체됩니다.
                </small>
              </section>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
