# Web Player - 아키텍처 설계 문서

## 목차
1. [시스템 개요](#1-시스템-개요)
2. [아키텍처 패턴](#2-아키텍처-패턴)
3. [컴포넌트 구조](#3-컴포넌트-구조)
4. [데이터 흐름](#4-데이터-흐름)
5. [기술 스택 상세](#5-기술-스택-상세)
6. [보안 설계](#6-보안-설계)
7. [확장성 고려사항](#7-확장성-고려사항)

---

## 1. 시스템 개요

### 1.1 아키텍처 목표

**핵심 원칙**:
- **실시간성**: 최소 지연시간으로 화면 스트리밍 및 입력 전달
- **확장성**: 향후 다중 사용자, 다중 모니터 지원 가능한 구조
- **모듈성**: 각 컴포넌트의 독립성 보장
- **유지보수성**: 명확한 책임 분리 및 인터페이스 정의

### 1.2 High-Level 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Web Client (Browser)                       │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐  ┌────────────┐│
│  │ Presentation│  │   Business  │  │ Communication│  │   State    ││
│  │    Layer    │◄─┤    Logic    │◄─┤    Layer     │◄─┤  Manager   ││
│  │             │  │             │  │              │  │            ││
│  │ • Canvas    │  │ • Renderer  │  │ • WebSocket  │  │ • UI State ││
│  │ • UI        │  │ • Input     │  │ • Reconnect  │  │ • Settings ││
│  └────────────┘  └─────────────┘  └──────────────┘  └────────────┘│
└────────────────────────────┬────────────────────────────────────────┘
                             │ WebSocket (JSON over TCP)
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                        Server (FastAPI)                             │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐  ┌────────────┐│
│  │ API Layer  │  │   Service   │  │   Adapter    │  │  System    ││
│  │            │─►│    Layer    │─►│    Layer     │─►│   Layer    ││
│  │            │  │             │  │              │  │            ││
│  │ • WebSocket│  │ • Screen    │  │ • UI-TARS   │  │ • PyAutoGUI││
│  │ • REST     │  │ • Action    │  │   Parser    │  │ • MSS      ││
│  │ • Health   │  │ • Session   │  │ • Coordinate│  │ • OS API   ││
│  └────────────┘  └─────────────┘  └──────────────┘  └────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 아키텍처 패턴

### 2.1 전체 패턴: Client-Server + Event-Driven

**선택 이유**:
- 웹 브라우저와 원격 PC 간 명확한 역할 분리
- 실시간 양방향 통신 필요
- 비동기 이벤트 처리 (화면 캡처, 입력 이벤트)

### 2.2 Server 패턴: Layered Architecture

```
┌─────────────────────────────────────┐
│      API Layer (FastAPI)            │  ← HTTP/WebSocket 엔드포인트
├─────────────────────────────────────┤
│      Service Layer                  │  ← 비즈니스 로직
│  • ScreenController                 │
│  • ActionHandler                    │
├─────────────────────────────────────┤
│      Adapter Layer                  │  ← 외부 라이브러리 통합
│  • UI-TARS Integration              │
│  • PyAutoGUI Wrapper                │
├─────────────────────────────────────┤
│      Infrastructure Layer           │  ← 시스템 리소스 접근
│  • Screen Capture (MSS)             │
│  • OS Input Injection               │
└─────────────────────────────────────┘
```

**레이어별 책임**:

1. **API Layer**:
   - HTTP/WebSocket 요청 수신
   - 요청 검증 및 응답 포맷팅
   - 에러 핸들링 및 로깅

2. **Service Layer**:
   - 핵심 비즈니스 로직
   - 화면 캡처/스트리밍 오케스트레이션
   - 액션 처리 워크플로우

3. **Adapter Layer**:
   - 외부 라이브러리 추상화
   - UI-TARS 파싱 로직
   - 좌표 변환

4. **Infrastructure Layer**:
   - 하드웨어/OS 접근
   - 화면 캡처
   - 마우스/키보드 제어

### 2.3 Client 패턴: MVC-like Pattern

```
┌─────────────────────────────────────┐
│           View Layer                │  ← HTML/Canvas
│  • index.html                       │
│  • CSS Styles                       │
├─────────────────────────────────────┤
│         Controller Layer            │  ← 이벤트 처리
│  • InputHandler                     │
│  • ConnectionManager                │
├─────────────────────────────────────┤
│           Model Layer               │  ← 데이터 및 상태
│  • ScreenRenderer                   │
│  • WebSocketClient                  │
│  • ApplicationState                 │
└─────────────────────────────────────┘
```

---

## 3. 컴포넌트 구조

### 3.1 Server 컴포넌트 상세

#### 3.1.1 FastAPI Application (`main.py`)

**책임**:
- 애플리케이션 라이프사이클 관리
- 라우팅 및 미들웨어 설정
- 의존성 주입 설정

**주요 객체**:
```python
app: FastAPI
    ├── middleware: CORS, logging, error handling
    ├── routes:
    │   ├── /ws (WebSocket)
    │   ├── / (Static files)
    │   └── /health (Health check)
    └── lifespan_events:
        ├── startup: 리소스 초기화
        └── shutdown: 리소스 정리
```

**의존성 그래프**:
```
FastAPI App
    └─► ScreenController
        ├─► MSS (화면 캡처)
        └─► PIL (이미지 처리)
    └─► ActionHandler
        ├─► UI-TARS Parser
        └─► PyAutoGUI
```

#### 3.1.2 ScreenController (`screen_controller.py`)

**책임**:
- 화면 캡처 및 인코딩
- 스트리밍 속도 제어 (FPS)
- 다중 클라이언트 관리 (향후)

**상태 다이어그램**:
```
    [Idle]
      │
      │ start_streaming()
      ▼
  [Capturing] ◄──┐
      │          │
      │ capture_frame()
      │          │
      │ encode_frame()
      │          │
      │ send_frame()
      │          │
      └──────────┘
      │
      │ stop_streaming()
      ▼
    [Stopped]
```

**메서드 호출 순서**:
```
1. __init__()
   └─ 화면 크기 감지

2. start_streaming(websocket)
   └─ while is_streaming:
       ├─ capture_frame()
       │  └─ mss.grab() → PIL.Image
       ├─ encode_frame()
       │  └─ JPEG 압축 → base64
       ├─ send_frame(websocket)
       │  └─ websocket.send_json()
       └─ await asyncio.sleep(1/fps)

3. stop_streaming()
   └─ is_streaming = False
```

**성능 고려사항**:
- **병렬 처리**: 캡처와 인코딩을 별도 스레드로 분리 가능
- **버퍼링**: 프레임 큐로 안정적 전송
- **적응형 FPS**: 네트워크 지연 감지 시 FPS 감소

#### 3.1.3 ActionHandler (`action_handler.py`)

**책임**:
- 클라이언트 액션을 UI-TARS 형식으로 변환
- UI-TARS 파서 호출
- PyAutoGUI 코드 생성 및 실행

**처리 파이프라인**:
```
Client Action JSON
    │
    ▼
[Validation]
    │
    ▼
[Convert to UI-TARS Format]
    │
    ▼
[UI-TARS Parser]
    │  parse_action_to_structure_output()
    │
    ▼
[Coordinate Transformation]
    │  • Canvas coords → Absolute coords
    │  • Absolute → Relative (UI-TARS)
    │
    ▼
[PyAutoGUI Code Generation]
    │  parsing_response_to_pyautogui_code()
    │
    ▼
[Execute]
    │  exec(code)
    │
    ▼
[Response]
```

**액션 타입별 처리**:

| Action Type | Validation | Transformation | Execution |
|-------------|------------|----------------|-----------|
| click | x, y 범위 체크 | 좌표 변환 | pyautogui.click() |
| double_click | x, y 범위 체크 | 좌표 변환 | pyautogui.doubleClick() |
| right_click | x, y 범위 체크 | 좌표 변환 | pyautogui.click(button='right') |
| drag | start/end 좌표 체크 | 좌표 변환 | pyautogui.dragTo() |
| type | 문자열 sanitization | 특수문자 이스케이프 | pyautogui.write() |
| hotkey | 키 조합 검증 | 키 이름 매핑 | pyautogui.hotkey() |
| scroll | 방향 검증 | 스크롤 양 계산 | pyautogui.scroll() |

**에러 처리 전략**:
```python
try:
    # 액션 처리
    result = await process_action(action_data)
except ValidationError as e:
    # 입력 검증 실패
    return {"status": "error", "code": "INVALID_INPUT", "message": str(e)}
except CoordinateError as e:
    # 좌표 변환 실패
    return {"status": "error", "code": "COORDINATE_ERROR", "message": str(e)}
except ExecutionError as e:
    # PyAutoGUI 실행 실패
    return {"status": "error", "code": "EXECUTION_ERROR", "message": str(e)}
except Exception as e:
    # 예기치 않은 에러
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return {"status": "error", "code": "INTERNAL_ERROR", "message": "Internal server error"}
```

### 3.2 Client 컴포넌트 상세

#### 3.2.1 WebSocketClient (`websocket-client.js`)

**책임**:
- WebSocket 연결 관리
- 재연결 로직
- 메시지 송수신

**상태 머신**:
```
    [Disconnected]
         │
         │ connect()
         ▼
    [Connecting]
         │
         ├─► [Connected] ─┐
         │       │         │
         │       │ send()  │ onmessage
         │       │         │
         │       │◄────────┘
         │       │
         │       │ disconnect() or error
         │       ▼
         └─► [Reconnecting]
                 │
                 │ attempt < max
                 └─► [Connecting]
```

**재연결 전략: Exponential Backoff**:
```javascript
delay = base_delay * (2 ^ (attempt - 1))

Attempt 1: 1000ms
Attempt 2: 2000ms
Attempt 3: 4000ms
Attempt 4: 8000ms
Attempt 5: 16000ms (max)
```

#### 3.2.2 ScreenRenderer (`screen-renderer.js`)

**책임**:
- Canvas에 화면 렌더링
- 좌표 변환 (Canvas ↔ Remote)
- FPS 계산

**렌더링 파이프라인**:
```
Frame Data (base64)
    │
    ▼
[Decode Base64]
    │
    ▼
[Create Image Object]
    │
    ▼
[Wait for Image Load]
    │
    ▼
[Update Canvas Size] (if needed)
    │
    ▼
[Draw Image on Canvas]
    │  ctx.drawImage(img, 0, 0)
    │
    ▼
[Calculate FPS]
    │
    ▼
[Update UI]
```

**좌표 변환 로직**:
```javascript
// Canvas → Remote
function canvasToRemote(canvasX, canvasY) {
    const scaleX = remoteWidth / canvas.width;
    const scaleY = remoteHeight / canvas.height;

    return {
        x: Math.round(canvasX * scaleX),
        y: Math.round(canvasY * scaleY)
    };
}

// Remote → Canvas (for feedback)
function remoteToCanvas(remoteX, remoteY) {
    const scaleX = canvas.width / remoteWidth;
    const scaleY = canvas.height / remoteHeight;

    return {
        x: Math.round(remoteX * scaleX),
        y: Math.round(remoteY * scaleY)
    };
}
```

#### 3.2.3 InputHandler (`input-handler.js`)

**책임**:
- DOM 이벤트 캡처
- 이벤트 데이터 추출
- 액션 JSON 생성 및 전송

**이벤트 처리 플로우**:
```
Browser Event (MouseEvent, KeyboardEvent)
    │
    ▼
[Event Listener]
    │
    ▼
[Prevent Default] (if needed)
    │
    ▼
[Extract Event Data]
    │  • Coordinates
    │  • Key codes
    │  • Modifiers
    │
    ▼
[Transform Coordinates]
    │  Canvas → Remote
    │
    ▼
[Create Action JSON]
    │
    ▼
[Send via WebSocket]
    │
    ▼
[Visual Feedback] (optional)
```

**이벤트 매핑**:

| Browser Event | Handler Method | Action Type |
|---------------|----------------|-------------|
| click | handleClick() | click |
| dblclick | handleDoubleClick() | double_click |
| contextmenu | handleRightClick() | right_click |
| mousedown + mouseup | handleDrag() | drag |
| wheel | handleWheel() | scroll |
| keydown | handleKeyDown() | type / hotkey |

---

## 4. 데이터 흐름

### 4.1 화면 스트리밍 흐름 (Server → Client)

**시퀀스 다이어그램**:
```
ScreenController    WebSocket    Network    Client    Canvas
      │                 │            │         │         │
      │ capture_frame() │            │         │         │
      ├────────────────►│            │         │         │
      │                 │            │         │         │
      │ encode_frame()  │            │         │         │
      ├────────────────►│            │         │         │
      │                 │            │         │         │
      │                 │ send_json()│         │         │
      │                 ├───────────►│         │         │
      │                 │            │         │         │
      │                 │            │ receive │         │
      │                 │            ├────────►│         │
      │                 │            │         │         │
      │                 │            │         │ decode  │
      │                 │            │         ├────────►│
      │                 │            │         │         │
      │                 │            │         │  draw   │
      │                 │            │         │◄────────┤
      │                 │            │         │         │
```

**데이터 변환 과정**:
```
[Screen Pixels]
    │ mss.grab()
    ▼
[Raw RGB Array]
    │ PIL.Image.frombytes()
    ▼
[PIL Image Object]
    │ Image.save(format='JPEG', quality=70)
    ▼
[JPEG Binary]
    │ base64.b64encode()
    ▼
[Base64 String]
    │ JSON.stringify()
    ▼
[WebSocket Message]
    │ Network transmission
    ▼
[Client receives]
    │ JSON.parse()
    ▼
[Base64 String]
    │ Create Image()
    ▼
[Browser Image Object]
    │ ctx.drawImage()
    ▼
[Canvas Display]
```

### 4.2 액션 전송 흐름 (Client → Server)

**시퀀스 다이어그램**:
```
User    Canvas    InputHandler    WebSocket    Network    Server    ActionHandler    PyAutoGUI    OS
 │        │           │               │            │          │            │              │         │
 │ click  │           │               │            │          │            │              │         │
 ├───────►│           │               │            │          │            │              │         │
 │        │           │               │            │          │            │              │         │
 │        │ onclick() │               │            │          │            │              │         │
 │        ├──────────►│               │            │          │            │              │         │
 │        │           │               │            │          │            │              │         │
 │        │           │ getCoords()   │            │          │            │              │         │
 │        │           ├──────────────►│            │          │            │              │         │
 │        │           │               │            │          │            │              │         │
 │        │           │               │ send_json()│          │            │              │         │
 │        │           │               ├───────────►│          │            │              │         │
 │        │           │               │            │          │            │              │         │
 │        │           │               │            │ receive  │            │              │         │
 │        │           │               │            ├─────────►│            │              │         │
 │        │           │               │            │          │            │              │         │
 │        │           │               │            │          │ process()  │              │         │
 │        │           │               │            │          ├───────────►│              │         │
 │        │           │               │            │          │            │              │         │
 │        │           │               │            │          │            │ parse()      │         │
 │        │           │               │            │          │            ├─────────────►│         │
 │        │           │               │            │          │            │              │         │
 │        │           │               │            │          │            │              │ click() │
 │        │           │               │            │          │            │              ├────────►│
 │        │           │               │            │          │            │              │         │
 │        │           │               │            │          │            │              │         │ Action!
 │        │           │               │            │          │            │              │         │◄────────
```

### 4.3 에러 전파 흐름

**에러 처리 체인**:
```
[Error Source]
    │
    ▼
[Exception Handler]
    │
    ▼
[Log Error]
    │  logger.error()
    │
    ▼
[Create Error Response]
    │  {"type": "error", ...}
    │
    ▼
[Send to Client]
    │  websocket.send_json()
    │
    ▼
[Client Error Handler]
    │
    ▼
[Display to User]
    │  statusBar.setStatus('error', message)
    │
    ▼
[Recovery Action]
    │  • Retry
    │  • Reconnect
    │  • Fallback
```

---

## 5. 기술 스택 상세

### 5.1 Server 기술

#### Python 3.10+
- **선택 이유**:
  - UI-TARS 라이브러리 네이티브 지원
  - 풍부한 비동기 라이브러리
  - 빠른 개발 속도

#### FastAPI
- **역할**: Web 프레임워크
- **특징**:
  - 비동기 지원 (async/await)
  - WebSocket 내장 지원
  - 자동 API 문서화
  - Pydantic 데이터 검증

**선택 이유 vs. 다른 프레임워크**:
| 프레임워크 | 장점 | 단점 | 채택 여부 |
|-----------|------|------|----------|
| FastAPI | 비동기, WebSocket, 빠름 | - | ✅ 채택 |
| Flask | 간단, 성숙함 | 비동기 지원 약함 | ❌ |
| Django | 풀스택 | 무거움, WebSocket 복잡 | ❌ |
| Tornado | 비동기, WebSocket | 생태계 작음 | ❌ |

#### PyAutoGUI
- **역할**: 마우스/키보드 제어
- **한계**:
  - 플랫폼별 제약사항 존재
  - 일부 보안 앱과 충돌 가능

**대안 검토**:
- **pynput**: 더 low-level, 크로스 플랫폼
- **pywin32** (Windows): Windows 전용, 강력
- **Quartz** (macOS): macOS 전용, 네이티브

#### MSS (Multiple Screenshots)
- **역할**: 화면 캡처
- **장점**:
  - 가장 빠른 Python 화면 캡처 라이브러리
  - 멀티 모니터 지원
  - 크로스 플랫폼

**대안 검토**:
| 라이브러리 | 속도 | 멀티 모니터 | 크로스 플랫폼 | 채택 |
|-----------|------|------------|-------------|------|
| MSS | ⭐⭐⭐⭐⭐ | ✅ | ✅ | ✅ |
| PyAutoGUI.screenshot | ⭐⭐⭐ | ✅ | ✅ | ❌ |
| PIL.ImageGrab | ⭐⭐⭐ | ❌ | Windows/macOS | ❌ |
| python-mss | ⭐⭐⭐⭐ | ✅ | ✅ | ❌ (MSS와 동일) |

### 5.2 Client 기술

#### Vanilla JavaScript
- **선택 이유**:
  - 프레임워크 없이 빠른 성능
  - 번들 크기 최소화
  - 의존성 없음

**향후 고려사항**:
- React/Vue 도입 검토 (복잡한 UI 필요 시)
- TypeScript 도입 (타입 안정성)

#### HTML5 Canvas
- **역할**: 화면 렌더링
- **장점**:
  - 고성능 그래픽
  - 픽셀 수준 제어
  - 브라우저 네이티브 지원

**대안 검토**:
- **Video Element**: 비디오 스트리밍에 적합하지만 정적 이미지 스트리밍에는 오버헤드
- **WebGL**: 3D에 최적화, 2D 이미지에는 과도

#### WebSocket
- **역할**: 실시간 양방향 통신
- **장점**:
  - 낮은 지연시간
  - 서버 푸시 가능
  - HTTP/HTTPS와 호환

**대안 검토**:
| 기술 | 지연시간 | 양방향 | 브라우저 지원 | 채택 |
|-----|---------|--------|-------------|------|
| WebSocket | ⭐⭐⭐⭐⭐ | ✅ | ✅ | ✅ |
| WebRTC | ⭐⭐⭐⭐⭐ | ✅ | ✅ | ❌ (v2.0 검토) |
| Server-Sent Events | ⭐⭐⭐ | ❌ | ✅ | ❌ |
| Long Polling | ⭐⭐ | ❌ | ✅ | ❌ |

---

## 6. 보안 설계

### 6.1 인증 및 인가

**v1.0 (선택적)**:
```
Client                    Server
  │                         │
  │  Connect + Token        │
  ├────────────────────────►│
  │                         │ Validate Token
  │                         ├──────────────►
  │                         │
  │  Accept / Reject        │
  │◄────────────────────────┤
```

**Token 기반 인증 구현**:
```python
# Server
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")

async def authenticate(websocket: WebSocket, token: str) -> bool:
    if not AUTH_TOKEN:
        return True  # 인증 비활성화
    return token == AUTH_TOKEN

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query("")):
    if not await authenticate(websocket, token):
        await websocket.close(code=1008, reason="Unauthorized")
        return
    # ... 연결 처리
```

### 6.2 입력 검증

**좌표 검증**:
```python
def validate_coordinates(x: int, y: int, screen_width: int, screen_height: int):
    if not (0 <= x <= screen_width):
        raise ValidationError(f"X coordinate {x} out of bounds")
    if not (0 <= y <= screen_height):
        raise ValidationError(f"Y coordinate {y} out of bounds")
```

**텍스트 입력 Sanitization**:
```python
def sanitize_text_input(text: str) -> str:
    # 제어 문자 제거
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # 최대 길이 제한
    text = text[:1000]
    return text
```

### 6.3 Rate Limiting

**액션 빈도 제한**:
```python
from collections import deque
import time

class RateLimiter:
    def __init__(self, max_actions: int = 100, window: int = 1):
        self.max_actions = max_actions
        self.window = window
        self.actions = deque()

    def check(self) -> bool:
        now = time.time()
        # 윈도우 밖 액션 제거
        while self.actions and self.actions[0] < now - self.window:
            self.actions.popleft()

        if len(self.actions) >= self.max_actions:
            return False

        self.actions.append(now)
        return True
```

### 6.4 HTTPS/WSS

**프로덕션 배포 시**:
```python
# Uvicorn with SSL
uvicorn.run(
    app,
    host="0.0.0.0",
    port=443,
    ssl_keyfile="/path/to/privkey.pem",
    ssl_certfile="/path/to/fullchain.pem"
)
```

---

## 7. 확장성 고려사항

### 7.1 수평 확장 (Horizontal Scaling)

**v2.0: 다중 서버 지원**
```
            ┌─────────────┐
            │ Load Balancer│
            │   (Nginx)   │
            └──────┬──────┘
                   │
      ┌────────────┼────────────┐
      │            │            │
      ▼            ▼            ▼
  [Server 1]  [Server 2]  [Server 3]
      │            │            │
      └────────────┼────────────┘
                   │
            ┌──────▼──────┐
            │    Redis    │
            │  (Session)  │
            └─────────────┘
```

**세션 관리**:
- Redis에 WebSocket 세션 저장
- Sticky session 또는 서버 간 메시지 전달

### 7.2 다중 모니터 지원

**구조 변경**:
```python
class MultiMonitorController:
    def __init__(self):
        self.monitors = self.detect_monitors()

    def detect_monitors(self) -> List[Monitor]:
        with mss.mss() as sct:
            return [Monitor(i, mon) for i, mon in enumerate(sct.monitors[1:])]

    def capture_monitor(self, monitor_id: int) -> Image:
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[monitor_id + 1])
            return Image.frombytes('RGB', screenshot.size, screenshot.rgb)

    def stream_all_monitors(self, websocket: WebSocket):
        # 각 모니터를 별도 스트림으로 전송
        for monitor in self.monitors:
            asyncio.create_task(self.stream_monitor(monitor.id, websocket))
```

### 7.3 WebRTC 마이그레이션

**v2.0 고려사항**:
- **장점**:
  - 더 낮은 지연시간
  - H.264 하드웨어 인코딩
  - 네트워크 적응형 스트리밍
- **단점**:
  - 복잡한 구현
  - 브라우저 호환성
  - STUN/TURN 서버 필요

**아키텍처 변경**:
```
Client (WebRTC)          Server (WebRTC)
  │                         │
  │  Offer (SDP)            │
  ├────────────────────────►│
  │                         │
  │  Answer (SDP)           │
  │◄────────────────────────┤
  │                         │
  │  ICE Candidates         │
  │◄───────────────────────►│
  │                         │
  │  Media Stream (RTP)     │
  │◄════════════════════════│
```

### 7.4 모바일 지원

**반응형 UI**:
```css
/* Mobile-first approach */
@media (max-width: 768px) {
    #screen-canvas {
        width: 100vw;
        height: calc(100vh - 60px);
    }

    #control-panel {
        position: fixed;
        bottom: 0;
        width: 100%;
    }
}
```

**터치 이벤트 지원**:
```javascript
canvas.addEventListener('touchstart', handleTouchStart);
canvas.addEventListener('touchmove', handleTouchMove);
canvas.addEventListener('touchend', handleTouchEnd);
```

---

## 부록

### A. 의존성 다이어그램

```
FastAPI
  ├── uvicorn (ASGI server)
  ├── websockets
  ├── pydantic (data validation)
  └── starlette (core)

ScreenController
  ├── mss (screen capture)
  └── PIL/Pillow (image processing)

ActionHandler
  ├── ui-tars (action parsing)
  │   ├── torch (AI model)
  │   └── transformers
  └── pyautogui (OS control)
```

### B. 파일 구조

```
web-player/
├── src/
│   ├── server/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── screen_controller.py # 화면 캡처/스트리밍
│   │   ├── action_handler.py    # 액션 처리
│   │   ├── models.py            # Pydantic models
│   │   ├── config.py            # 설정
│   │   └── utils.py             # 유틸리티
│   └── client/
│       └── __init__.py
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── websocket-client.js
│   │   ├── screen-renderer.js
│   │   ├── input-handler.js
│   │   └── main.js
│   └── index.html
├── tests/
│   ├── test_screen_controller.py
│   ├── test_action_handler.py
│   └── test_integration.py
├── docs/
│   ├── SPEC.md
│   ├── ARCHITECTURE.md (this file)
│   ├── DEVELOPMENT.md
│   └── API.md
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### C. 성능 벤치마크 목표

| 메트릭 | 목표 | 측정 방법 |
|--------|------|----------|
| 화면 스트리밍 FPS | 30 FPS | 클라이언트 FPS 카운터 |
| 액션 지연시간 | < 100ms | 클릭 → 실행 시간 측정 |
| 네트워크 지연 | < 500ms | 왕복 시간 (RTT) |
| CPU 사용률 (서버) | < 20% (유휴 시) | psutil.cpu_percent() |
| 메모리 사용량 (서버) | < 500MB | psutil.memory_info() |
| 대역폭 사용량 | < 5 Mbps @ 30 FPS | 네트워크 모니터링 |
