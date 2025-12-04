# Web Player - 상세 기술 스펙 문서

## 1. 프로젝트 개요

### 1.1 프로젝트 명
**Web Player** - UI-TARS 기반 웹 원격 데스크톱 제어 시스템

### 1.2 목적
웹 브라우저를 통해 원격 컴퓨터의 화면을 실시간으로 스트리밍하고,
UI-TARS의 액션 파싱 기능을 활용하여 마우스/키보드 입력을 원격으로 전달하는 시스템

### 1.3 핵심 기술 스택
- **Backend**: Python 3.10+, FastAPI, WebSocket
- **Frontend**: Vanilla JavaScript, HTML5 Canvas, WebSocket API
- **AI/ML**: UI-TARS (액션 파싱 및 좌표 변환)
- **Screen Control**: PyAutoGUI, MSS (화면 캡처)

---

## 2. 시스템 요구사항

### 2.1 기능 요구사항

#### FR-001: 실시간 화면 스트리밍
- **설명**: 서버(원격 PC)의 화면을 실시간으로 캡처하여 클라이언트(웹 브라우저)로 전송
- **세부사항**:
  - 최소 15 FPS, 권장 30 FPS
  - JPEG 압축 (품질: 70%, 조정 가능)
  - Base64 인코딩으로 WebSocket 전송
  - 화면 해상도 자동 감지 및 전송

#### FR-002: 마우스 클릭 원격 전달
- **설명**: 웹 클라이언트에서 발생한 클릭을 원격 PC에 전달
- **지원 액션**:
  - 좌클릭 (single click)
  - 더블클릭 (double click)
  - 우클릭 (right click)
  - 드래그 (drag)
  - 호버 (hover/mouseover)
- **좌표 변환**:
  - 클라이언트 Canvas 좌표 → 원격 화면 절대 좌표
  - UI-TARS action parser를 통한 정확한 좌표 변환

#### FR-003: 키보드 입력 원격 전달
- **지원 액션**:
  - 단일 키 입력 (keypress)
  - 단축키 (hotkey, 예: Ctrl+C, Alt+Tab)
  - 텍스트 입력 (type)
  - 특수 키 (Enter, Tab, Escape, Arrow keys 등)

#### FR-004: 스크롤 기능
- **설명**: 마우스 휠 스크롤을 원격으로 전달
- **지원**:
  - 상하 스크롤
  - 좌우 스크롤 (지원 디바이스에 한함)
  - 특정 위치에서의 스크롤

#### FR-005: 연결 상태 관리
- **기능**:
  - WebSocket 연결/재연결 자동 처리
  - 연결 상태 시각적 표시
  - 끊김 시 자동 재연결 시도
  - 타임아웃 및 핑/퐁 메커니즘

### 2.2 비기능 요구사항

#### NFR-001: 성능
- **응답 시간**: 클릭 입력 후 100ms 이내 원격 실행
- **스트리밍 지연**: 500ms 이하
- **CPU 사용률**: 서버 20% 이하 (유휴 시)
- **메모리 사용량**: 서버 500MB 이하

#### NFR-002: 확장성
- **동시 연결**: 최소 1개 클라이언트 지원 (v1.0)
- **향후 확장**: 다중 클라이언트 지원 가능한 구조

#### NFR-003: 보안 (선택적)
- 인증 토큰 기반 접근 제어
- HTTPS/WSS 지원
- 입력 검증 및 sanitization

#### NFR-004: 호환성
- **브라우저**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **서버 OS**: Windows 10/11, macOS 11+, Ubuntu 20.04+
- **Python**: 3.10, 3.11, 3.12

---

## 3. 시스템 아키텍처

### 3.1 전체 구조도

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Client                              │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Canvas Display │  │  Event Handlers  │  │ WebSocket Client│ │
│  │  (화면 렌더링)  │  │ (클릭/키보드 캡처)│  │   (통신 관리)   │ │
│  └────────────────┘  └──────────────────┘  └─────────────────┘ │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ WebSocket (JSON)
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                         Server (FastAPI)                        │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ WebSocket      │  │ Screen Controller│  │ Action Handler  │ │
│  │ Endpoint       │◄─┤  (화면 캡처/전송) │◄─┤ (UI-TARS 통합) │ │
│  └────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                      │           │
│                                                      ▼           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              UI-TARS Library                                ││
│  │  • parse_action_to_structure_output()                      ││
│  │  • parsing_response_to_pyautogui_code()                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                      │           │
│                                                      ▼           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              PyAutoGUI / MSS                                ││
│  │  • 화면 캡처: mss.mss().grab()                              ││
│  │  • 액션 실행: pyautogui.click(), type(), hotkey()          ││
│  └─────────────────────────────────────────────────────────────┘│
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │ OS (Windows/  │
                        │  macOS/Linux) │
                        └───────────────┘
```

### 3.2 데이터 흐름

#### 3.2.1 화면 스트리밍 (Server → Client)
```
1. [Server] ScreenController.capture_screen()
   └─ mss.grab() → PIL.Image

2. [Server] ScreenController.encode_frame()
   └─ Image.save(format='JPEG') → base64.encode()

3. [Server] WebSocket.send_json()
   └─ {"type": "screen", "data": "<base64>", "width": 1920, "height": 1080}

4. [Client] WebSocket.onmessage()
   └─ Parse JSON → Create Image → Draw on Canvas
```

#### 3.2.2 액션 전송 (Client → Server)
```
1. [Client] Canvas.onclick(event)
   └─ Calculate coordinates → Create action JSON

2. [Client] WebSocket.send()
   └─ {"type": "action", "action_type": "click", "x": 100, "y": 200}

3. [Server] WebSocket.receive_json()
   └─ Parse action data

4. [Server] ActionHandler.process_action()
   └─ Convert to UI-TARS format
   └─ Call parse_action_to_structure_output()
   └─ Call parsing_response_to_pyautogui_code()

5. [Server] Execute PyAutoGUI code
   └─ exec(pyautogui_code)
   └─ OS performs action
```

---

## 4. 모듈 상세 설계

### 4.1 Server 모듈

#### 4.1.1 main.py
**역할**: FastAPI 애플리케이션 진입점

**주요 컴포넌트**:
```python
class ServerConfig:
    """서버 설정"""
    host: str = "0.0.0.0"
    port: int = 8000
    fps: int = 30
    quality: int = 70

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 연결 엔드포인트"""
    pass

@app.get("/")
async def serve_client():
    """클라이언트 HTML 제공"""
    pass

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    pass
```

#### 4.1.2 screen_controller.py
**역할**: 화면 캡처 및 스트리밍 관리

**클래스**: `ScreenController`

**메서드**:
```python
class ScreenController:
    def __init__(self, fps: int = 30, quality: int = 70):
        """
        Args:
            fps: 초당 프레임 수
            quality: JPEG 품질 (1-100)
        """
        self.fps = fps
        self.quality = quality
        self.screen_width, self.screen_height = pyautogui.size()
        self.is_streaming = False

    async def start_streaming(self, websocket: WebSocket):
        """
        화면 스트리밍 시작

        Args:
            websocket: 연결된 WebSocket

        Process:
            1. mss로 화면 캡처
            2. PIL로 이미지 변환
            3. JPEG 압축
            4. Base64 인코딩
            5. WebSocket으로 전송
            6. fps에 맞춰 대기
        """
        self.is_streaming = True
        interval = 1.0 / self.fps

        while self.is_streaming:
            try:
                # 화면 캡처
                frame = self.capture_frame()

                # 전송
                await websocket.send_json({
                    "type": "screen",
                    "data": frame["data"],
                    "width": frame["width"],
                    "height": frame["height"],
                    "timestamp": time.time()
                })

                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                break

    def capture_frame(self) -> dict:
        """
        단일 프레임 캡처

        Returns:
            {
                "data": "<base64-encoded-jpeg>",
                "width": int,
                "height": int
            }
        """
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # 주 모니터
            screenshot = sct.grab(monitor)

            # PIL Image로 변환
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

            # JPEG 압축 및 인코딩
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=self.quality)
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            return {
                "data": img_base64,
                "width": screenshot.width,
                "height": screenshot.height
            }

    def stop_streaming(self):
        """스트리밍 중지"""
        self.is_streaming = False
```

#### 4.1.3 action_handler.py
**역할**: UI-TARS를 이용한 액션 처리

**클래스**: `ActionHandler`

**메서드**:
```python
class ActionHandler:
    def __init__(self, screen_width: int, screen_height: int):
        """
        Args:
            screen_width: 화면 너비
            screen_height: 화면 높이
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

    async def process_action(self, action_data: dict) -> dict:
        """
        액션 처리 메인 메서드

        Args:
            action_data: {
                "type": "action",
                "action_type": "click|double_click|right_click|drag|type|hotkey|scroll",
                "x": int (optional),
                "y": int (optional),
                "text": str (optional, for type),
                "key": str (optional, for hotkey),
                "direction": str (optional, for scroll)
            }

        Returns:
            {"status": "success|error", "message": str}
        """
        try:
            action_type = action_data.get("action_type")

            # UI-TARS 형식으로 변환
            uitars_response = self._convert_to_uitars_format(action_data)

            # UI-TARS 파서로 파싱
            parsed_actions = parse_action_to_structure_output(
                uitars_response,
                factor=1000,
                origin_resized_height=self.screen_height,
                origin_resized_width=self.screen_width,
                model_type="qwen25vl"
            )

            # PyAutoGUI 코드 생성
            pyautogui_code = parsing_response_to_pyautogui_code(
                parsed_actions,
                image_height=self.screen_height,
                image_width=self.screen_width
            )

            # 실행
            exec(pyautogui_code)

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Action processing error: {e}")
            return {"status": "error", "message": str(e)}

    def _convert_to_uitars_format(self, action_data: dict) -> str:
        """
        클라이언트 액션 데이터를 UI-TARS 응답 형식으로 변환

        Args:
            action_data: 클라이언트에서 받은 액션 데이터

        Returns:
            UI-TARS 형식의 응답 문자열
            예: "Thought: User clicked\nAction: click(start_box='(100,200)')"
        """
        action_type = action_data.get("action_type")

        if action_type == "click":
            x, y = action_data["x"], action_data["y"]
            return f"Thought: Click action\nAction: click(start_box='({x},{y})')"

        elif action_type == "double_click":
            x, y = action_data["x"], action_data["y"]
            return f"Action: left_double(start_box='({x},{y})')"

        elif action_type == "right_click":
            x, y = action_data["x"], action_data["y"]
            return f"Action: right_single(start_box='({x},{y})')"

        elif action_type == "drag":
            x1, y1 = action_data["start_x"], action_data["start_y"]
            x2, y2 = action_data["end_x"], action_data["end_y"]
            return f"Action: drag(start_box='({x1},{y1})', end_box='({x2},{y2})')"

        elif action_type == "type":
            text = action_data["text"]
            return f"Action: type(content='{text}')"

        elif action_type == "hotkey":
            keys = action_data["key"]
            return f"Action: hotkey(key='{keys}')"

        elif action_type == "scroll":
            x, y = action_data.get("x", 0), action_data.get("y", 0)
            direction = action_data.get("direction", "down")
            return f"Action: scroll(start_box='({x},{y})', direction='{direction}')"

        else:
            raise ValueError(f"Unknown action type: {action_type}")
```

### 4.2 Client 모듈

#### 4.2.1 index.html
**구조**:
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Player - Remote Desktop</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <!-- 상태 표시 -->
    <div id="status-bar">
        <span id="connection-status">Disconnected</span>
        <span id="fps-counter">0 FPS</span>
        <span id="latency">0 ms</span>
    </div>

    <!-- 화면 디스플레이 -->
    <div id="screen-container">
        <canvas id="screen-canvas"></canvas>
    </div>

    <!-- 컨트롤 패널 -->
    <div id="control-panel">
        <button id="btn-connect">Connect</button>
        <button id="btn-disconnect">Disconnect</button>
        <button id="btn-fullscreen">Fullscreen</button>
        <div id="settings">
            <label>Quality: <input type="range" id="quality-slider" min="10" max="100" value="70"></label>
        </div>
    </div>

    <script src="/static/js/websocket-client.js"></script>
    <script src="/static/js/screen-renderer.js"></script>
    <script src="/static/js/input-handler.js"></script>
    <script src="/static/js/main.js"></script>
</body>
</html>
```

#### 4.2.2 websocket-client.js
**역할**: WebSocket 연결 관리

```javascript
class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.callbacks = {
            onOpen: null,
            onMessage: null,
            onError: null,
            onClose: null
        };
    }

    connect() {
        /**
         * WebSocket 연결 시작
         *
         * Process:
         * 1. WebSocket 객체 생성
         * 2. 이벤트 핸들러 등록
         * 3. 연결 시도
         */
        this.ws = new WebSocket(this.url);

        this.ws.onopen = (event) => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            if (this.callbacks.onOpen) {
                this.callbacks.onOpen(event);
            }
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (this.callbacks.onMessage) {
                this.callbacks.onMessage(data);
            }
        };

        this.ws.onerror = (event) => {
            console.error('WebSocket error:', event);
            if (this.callbacks.onError) {
                this.callbacks.onError(event);
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket closed');
            if (this.callbacks.onClose) {
                this.callbacks.onClose(event);
            }
            this.attemptReconnect();
        };
    }

    disconnect() {
        /**
         * WebSocket 연결 종료
         */
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    send(data) {
        /**
         * 데이터 전송
         *
         * Args:
         *   data: Object - 전송할 데이터
         */
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.error('WebSocket is not connected');
        }
    }

    attemptReconnect() {
        /**
         * 재연결 시도
         *
         * Logic:
         * - 최대 재연결 횟수 체크
         * - 지수 백오프로 재연결 지연 증가
         */
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connect(), delay);
        }
    }

    on(event, callback) {
        /**
         * 이벤트 콜백 등록
         *
         * Args:
         *   event: 'open'|'message'|'error'|'close'
         *   callback: Function
         */
        const eventMap = {
            'open': 'onOpen',
            'message': 'onMessage',
            'error': 'onError',
            'close': 'onClose'
        };

        if (eventMap[event]) {
            this.callbacks[eventMap[event]] = callback;
        }
    }
}
```

#### 4.2.3 screen-renderer.js
**역할**: Canvas에 화면 렌더링

```javascript
class ScreenRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.remoteWidth = 0;
        this.remoteHeight = 0;
        this.lastFrameTime = 0;
        this.fps = 0;
    }

    renderFrame(frameData) {
        /**
         * 프레임 렌더링
         *
         * Args:
         *   frameData: {
         *     data: string (base64),
         *     width: number,
         *     height: number,
         *     timestamp: number
         *   }
         *
         * Process:
         * 1. Base64 디코딩
         * 2. Image 객체 생성
         * 3. Canvas에 그리기
         * 4. FPS 계산
         */
        this.remoteWidth = frameData.width;
        this.remoteHeight = frameData.height;

        const img = new Image();
        img.onload = () => {
            // 캔버스 크기 조정 (최초 1회)
            if (this.canvas.width !== img.width || this.canvas.height !== img.height) {
                this.canvas.width = img.width;
                this.canvas.height = img.height;
            }

            // 화면 그리기
            this.ctx.drawImage(img, 0, 0);

            // FPS 계산
            this.calculateFPS();
        };

        img.src = 'data:image/jpeg;base64,' + frameData.data;
    }

    calculateFPS() {
        /**
         * FPS 계산
         */
        const now = performance.now();
        if (this.lastFrameTime) {
            const delta = now - this.lastFrameTime;
            this.fps = Math.round(1000 / delta);
        }
        this.lastFrameTime = now;
    }

    getCoordinateScale() {
        /**
         * 좌표 변환 스케일 계산
         *
         * Returns:
         *   {scaleX: number, scaleY: number}
         */
        return {
            scaleX: this.remoteWidth / this.canvas.width,
            scaleY: this.remoteHeight / this.canvas.height
        };
    }

    canvasToRemoteCoords(canvasX, canvasY) {
        /**
         * Canvas 좌표를 원격 화면 좌표로 변환
         *
         * Args:
         *   canvasX: Canvas X 좌표
         *   canvasY: Canvas Y 좌표
         *
         * Returns:
         *   {x: number, y: number}
         */
        const scale = this.getCoordinateScale();
        return {
            x: Math.round(canvasX * scale.scaleX),
            y: Math.round(canvasY * scale.scaleY)
        };
    }

    drawClickFeedback(canvasX, canvasY) {
        /**
         * 클릭 위치 시각적 피드백
         *
         * Args:
         *   canvasX: Canvas X 좌표
         *   canvasY: Canvas Y 좌표
         */
        this.ctx.beginPath();
        this.ctx.arc(canvasX, canvasY, 10, 0, 2 * Math.PI);
        this.ctx.strokeStyle = 'rgba(255, 0, 0, 0.8)';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();

        // 0.5초 후 사라짐
        setTimeout(() => {
            // 다음 프레임으로 덮어씌워짐
        }, 500);
    }
}
```

#### 4.2.4 input-handler.js
**역할**: 마우스/키보드 입력 처리

```javascript
class InputHandler {
    constructor(canvas, wsClient) {
        this.canvas = canvas;
        this.wsClient = wsClient;
        this.renderer = null; // ScreenRenderer 인스턴스
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;

        this.setupEventListeners();
    }

    setRenderer(renderer) {
        this.renderer = renderer;
    }

    setupEventListeners() {
        /**
         * 이벤트 리스너 등록
         */

        // 마우스 클릭
        this.canvas.addEventListener('click', (e) => this.handleClick(e));

        // 더블클릭
        this.canvas.addEventListener('dblclick', (e) => this.handleDoubleClick(e));

        // 우클릭
        this.canvas.addEventListener('contextmenu', (e) => this.handleRightClick(e));

        // 드래그
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));

        // 스크롤
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e));

        // 키보드 (전역)
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    getCanvasCoords(event) {
        /**
         * 이벤트에서 Canvas 좌표 추출
         */
        const rect = this.canvas.getBoundingClientRect();
        return {
            canvasX: event.clientX - rect.left,
            canvasY: event.clientY - rect.top
        };
    }

    handleClick(event) {
        /**
         * 좌클릭 처리
         *
         * Process:
         * 1. Canvas 좌표 계산
         * 2. 원격 좌표로 변환
         * 3. 액션 데이터 생성
         * 4. WebSocket으로 전송
         * 5. 시각적 피드백
         */
        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);

        this.wsClient.send({
            type: 'action',
            action_type: 'click',
            x: remoteCoords.x,
            y: remoteCoords.y
        });

        this.renderer.drawClickFeedback(canvasX, canvasY);
    }

    handleDoubleClick(event) {
        /**
         * 더블클릭 처리
         */
        event.preventDefault();
        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);

        this.wsClient.send({
            type: 'action',
            action_type: 'double_click',
            x: remoteCoords.x,
            y: remoteCoords.y
        });
    }

    handleRightClick(event) {
        /**
         * 우클릭 처리
         */
        event.preventDefault();
        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);

        this.wsClient.send({
            type: 'action',
            action_type: 'right_click',
            x: remoteCoords.x,
            y: remoteCoords.y
        });
    }

    handleMouseDown(event) {
        /**
         * 마우스 다운 (드래그 시작)
         */
        this.isDragging = true;
        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);
        this.dragStartX = remoteCoords.x;
        this.dragStartY = remoteCoords.y;
    }

    handleMouseMove(event) {
        /**
         * 마우스 이동 (드래그 중)
         */
        if (!this.isDragging) return;

        // 드래그 시각적 표시 (선택 사항)
    }

    handleMouseUp(event) {
        /**
         * 마우스 업 (드래그 종료)
         */
        if (!this.isDragging) return;

        this.isDragging = false;
        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);

        // 시작과 끝 좌표가 다르면 드래그로 처리
        if (Math.abs(remoteCoords.x - this.dragStartX) > 5 ||
            Math.abs(remoteCoords.y - this.dragStartY) > 5) {

            this.wsClient.send({
                type: 'action',
                action_type: 'drag',
                start_x: this.dragStartX,
                start_y: this.dragStartY,
                end_x: remoteCoords.x,
                end_y: remoteCoords.y
            });
        }
    }

    handleWheel(event) {
        /**
         * 마우스 휠 (스크롤) 처리
         */
        event.preventDefault();
        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);

        const direction = event.deltaY < 0 ? 'up' : 'down';

        this.wsClient.send({
            type: 'action',
            action_type: 'scroll',
            x: remoteCoords.x,
            y: remoteCoords.y,
            direction: direction
        });
    }

    handleKeyDown(event) {
        /**
         * 키보드 입력 처리
         *
         * Special handling:
         * - Ctrl+C, Ctrl+V 등 단축키
         * - 특수 키 (Enter, Tab, Escape 등)
         */

        // 단축키 감지
        if (event.ctrlKey || event.metaKey || event.altKey) {
            event.preventDefault();

            let keys = [];
            if (event.ctrlKey) keys.push('ctrl');
            if (event.metaKey) keys.push('cmd');
            if (event.altKey) keys.push('alt');
            if (event.shiftKey) keys.push('shift');
            keys.push(event.key.toLowerCase());

            this.wsClient.send({
                type: 'action',
                action_type: 'hotkey',
                key: keys.join(' ')
            });
        }
        // 일반 키 입력
        else if (event.key.length === 1) {
            this.wsClient.send({
                type: 'action',
                action_type: 'type',
                text: event.key
            });
        }
        // 특수 키
        else {
            this.wsClient.send({
                type: 'action',
                action_type: 'hotkey',
                key: event.key.toLowerCase()
            });
        }
    }
}
```

#### 4.2.5 main.js
**역할**: 애플리케이션 초기화 및 통합

```javascript
// 전역 변수
let wsClient;
let screenRenderer;
let inputHandler;
let statusBar;

// 애플리케이션 초기화
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    /**
     * 애플리케이션 초기화
     *
     * Process:
     * 1. WebSocket 클라이언트 생성
     * 2. 화면 렌더러 생성
     * 3. 입력 핸들러 생성
     * 4. UI 컨트롤 설정
     * 5. 연결 시작
     */

    // WebSocket 클라이언트
    const wsUrl = `ws://${window.location.host}/ws`;
    wsClient = new WebSocketClient(wsUrl);

    // 화면 렌더러
    screenRenderer = new ScreenRenderer('screen-canvas');

    // 입력 핸들러
    const canvas = document.getElementById('screen-canvas');
    inputHandler = new InputHandler(canvas, wsClient);
    inputHandler.setRenderer(screenRenderer);

    // 상태바
    statusBar = new StatusBar();

    // WebSocket 이벤트 핸들러
    wsClient.on('open', handleWebSocketOpen);
    wsClient.on('message', handleWebSocketMessage);
    wsClient.on('error', handleWebSocketError);
    wsClient.on('close', handleWebSocketClose);

    // UI 컨트롤
    setupUIControls();

    // 자동 연결
    wsClient.connect();
}

function handleWebSocketOpen(event) {
    /**
     * WebSocket 연결 성공
     */
    console.log('Connected to server');
    statusBar.setStatus('connected', 'Connected');
}

function handleWebSocketMessage(data) {
    /**
     * WebSocket 메시지 수신
     *
     * Message types:
     * - screen: 화면 프레임 데이터
     * - status: 서버 상태 정보
     * - error: 에러 메시지
     */

    if (data.type === 'screen') {
        screenRenderer.renderFrame(data);
        statusBar.updateFPS(screenRenderer.fps);
    }
    else if (data.type === 'status') {
        statusBar.setStatus(data.status, data.message);
    }
    else if (data.type === 'error') {
        console.error('Server error:', data.message);
        statusBar.setStatus('error', data.message);
    }
}

function handleWebSocketError(event) {
    /**
     * WebSocket 에러
     */
    console.error('WebSocket error:', event);
    statusBar.setStatus('error', 'Connection error');
}

function handleWebSocketClose(event) {
    /**
     * WebSocket 연결 종료
     */
    console.log('Disconnected from server');
    statusBar.setStatus('disconnected', 'Disconnected');
}

function setupUIControls() {
    /**
     * UI 컨트롤 설정
     */

    // 연결 버튼
    document.getElementById('btn-connect').addEventListener('click', () => {
        wsClient.connect();
    });

    // 연결 해제 버튼
    document.getElementById('btn-disconnect').addEventListener('click', () => {
        wsClient.disconnect();
    });

    // 전체화면 버튼
    document.getElementById('btn-fullscreen').addEventListener('click', () => {
        const canvas = document.getElementById('screen-canvas');
        if (canvas.requestFullscreen) {
            canvas.requestFullscreen();
        }
    });

    // 품질 슬라이더 (향후 구현)
    document.getElementById('quality-slider').addEventListener('change', (e) => {
        const quality = e.target.value;
        wsClient.send({
            type: 'config',
            setting: 'quality',
            value: quality
        });
    });
}

// 상태바 클래스
class StatusBar {
    constructor() {
        this.statusElement = document.getElementById('connection-status');
        this.fpsElement = document.getElementById('fps-counter');
        this.latencyElement = document.getElementById('latency');
    }

    setStatus(status, message) {
        this.statusElement.textContent = message;
        this.statusElement.className = `status-${status}`;
    }

    updateFPS(fps) {
        this.fpsElement.textContent = `${fps} FPS`;
    }

    updateLatency(latency) {
        this.latencyElement.textContent = `${latency} ms`;
    }
}
```

---

## 5. 프로토콜 명세

### 5.1 WebSocket 메시지 포맷

#### 5.1.1 Server → Client

**화면 프레임**:
```json
{
    "type": "screen",
    "data": "<base64-encoded-jpeg>",
    "width": 1920,
    "height": 1080,
    "timestamp": 1699999999.999
}
```

**상태 메시지**:
```json
{
    "type": "status",
    "status": "connected|disconnected|error",
    "message": "Connection established"
}
```

**에러 메시지**:
```json
{
    "type": "error",
    "message": "Failed to execute action",
    "code": "ACTION_ERROR",
    "details": {}
}
```

#### 5.1.2 Client → Server

**클릭 액션**:
```json
{
    "type": "action",
    "action_type": "click",
    "x": 100,
    "y": 200
}
```

**더블클릭**:
```json
{
    "type": "action",
    "action_type": "double_click",
    "x": 100,
    "y": 200
}
```

**우클릭**:
```json
{
    "type": "action",
    "action_type": "right_click",
    "x": 100,
    "y": 200
}
```

**드래그**:
```json
{
    "type": "action",
    "action_type": "drag",
    "start_x": 100,
    "start_y": 200,
    "end_x": 300,
    "end_y": 400
}
```

**텍스트 입력**:
```json
{
    "type": "action",
    "action_type": "type",
    "text": "Hello World"
}
```

**단축키**:
```json
{
    "type": "action",
    "action_type": "hotkey",
    "key": "ctrl c"
}
```

**스크롤**:
```json
{
    "type": "action",
    "action_type": "scroll",
    "x": 500,
    "y": 300,
    "direction": "up|down"
}
```

**설정 변경**:
```json
{
    "type": "config",
    "setting": "quality|fps",
    "value": 70
}
```

---

## 6. 에러 처리

### 6.1 Server 에러

**에러 코드**:
- `SCREEN_CAPTURE_ERROR`: 화면 캡처 실패
- `ACTION_PARSE_ERROR`: 액션 파싱 실패
- `ACTION_EXECUTION_ERROR`: 액션 실행 실패
- `WEBSOCKET_ERROR`: WebSocket 통신 에러

**처리 방식**:
```python
try:
    # 액션 실행
    result = await action_handler.process_action(action_data)
except Exception as e:
    await websocket.send_json({
        "type": "error",
        "message": str(e),
        "code": "ACTION_EXECUTION_ERROR"
    })
    logger.error(f"Action error: {e}", exc_info=True)
```

### 6.2 Client 에러

**에러 시나리오**:
- WebSocket 연결 실패
- 재연결 횟수 초과
- 이미지 렌더링 실패
- 좌표 변환 에러

**처리 방식**:
- 자동 재연결 (최대 5회)
- 사용자에게 에러 메시지 표시
- 로그 기록

---

## 7. 성능 최적화

### 7.1 화면 스트리밍 최적화

1. **적응형 FPS**: 네트워크 상태에 따라 FPS 동적 조정
2. **JPEG 품질 조정**: 대역폭에 따라 품질 자동 조절
3. **차등 압축**: 변경된 영역만 전송 (향후 개선)
4. **H.264 코덱**: WebRTC 도입 검토 (v2.0)

### 7.2 액션 처리 최적화

1. **배치 처리**: 짧은 시간 내 여러 액션을 배치로 처리
2. **캐싱**: 반복되는 액션 파싱 결과 캐싱
3. **비동기 처리**: 모든 I/O 작업 비동기화

---

## 8. 테스트 계획

### 8.1 단위 테스트

**Server**:
- `ScreenController.capture_frame()` 테스트
- `ActionHandler._convert_to_uitars_format()` 테스트
- 좌표 변환 로직 테스트

**Client**:
- `ScreenRenderer.canvasToRemoteCoords()` 테스트
- `InputHandler` 이벤트 처리 테스트

### 8.2 통합 테스트

- WebSocket 연결/재연결 테스트
- 화면 스트리밍 end-to-end 테스트
- 액션 전송 및 실행 테스트

### 8.3 성능 테스트

- FPS 측정 (목표: 30 FPS)
- 지연시간 측정 (목표: < 500ms)
- CPU/메모리 사용률 모니터링

---

## 9. 배포 및 실행

### 9.1 환경 설정

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집
```

### 9.2 서버 실행

```bash
# 개발 모드
python src/server/main.py

# 프로덕션 모드
uvicorn src.server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 9.3 클라이언트 접속

```
http://localhost:8000
```

---

## 10. 향후 개선 사항

### v1.1
- [ ] 다중 모니터 지원
- [ ] 클립보드 공유
- [ ] 파일 전송

### v2.0
- [ ] WebRTC 기반 스트리밍
- [ ] 다중 사용자 동시 접속
- [ ] 세션 녹화 기능
- [ ] AI 자동 조작 (UI-TARS AI 모델 통합)

### v3.0
- [ ] 모바일 앱 (iOS/Android)
- [ ] 게임 컨트롤 최적화
- [ ] VR/AR 지원

---

## 부록

### A. UI-TARS 액션 타입 매핑표

| Client Action | UI-TARS Format | PyAutoGUI Method |
|---------------|----------------|------------------|
| click | `click(start_box='(x,y)')` | `pyautogui.click(x, y)` |
| double_click | `left_double(start_box='(x,y)')` | `pyautogui.doubleClick(x, y)` |
| right_click | `right_single(start_box='(x,y)')` | `pyautogui.click(x, y, button='right')` |
| drag | `drag(start_box='(x1,y1)', end_box='(x2,y2)')` | `pyautogui.dragTo(x2, y2)` |
| type | `type(content='text')` | `pyautogui.write('text')` |
| hotkey | `hotkey(key='ctrl c')` | `pyautogui.hotkey('ctrl', 'c')` |
| scroll | `scroll(start_box='(x,y)', direction='up')` | `pyautogui.scroll(5)` |

### B. 좌표 변환 공식

**Canvas → Remote**:
```
remote_x = canvas_x * (remote_width / canvas_width)
remote_y = canvas_y * (remote_height / canvas_height)
```

**UI-TARS 상대 좌표 (Qwen2.5-VL)**:
```
relative_x = absolute_x / smart_resize_width
relative_y = absolute_y / smart_resize_height
```

### C. 참고 자료

- UI-TARS Documentation: [README.md](../README.md)
- FastAPI Docs: https://fastapi.tiangolo.com/
- WebSocket API: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- PyAutoGUI Docs: https://pyautogui.readthedocs.io/
