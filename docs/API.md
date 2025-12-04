# Web Player - API 명세서

## 목차
1. [WebSocket API](#1-websocket-api)
2. [REST API](#2-rest-api)
3. [데이터 모델](#3-데이터-모델)
4. [에러 코드](#4-에러-코드)
5. [사용 예시](#5-사용-예시)

---

## 1. WebSocket API

### 1.1 연결

**Endpoint**: `/ws`

**프로토콜**: WebSocket

**URL**: `ws://localhost:8000/ws` (개발) / `wss://your-domain.com/ws` (프로덕션)

**연결 예시**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    console.log('Connected');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

ws.onerror = (error) => {
    console.error('Error:', error);
};

ws.onclose = () => {
    console.log('Disconnected');
};
```

### 1.2 Server → Client 메시지

#### 1.2.1 화면 프레임 (screen)

서버에서 클라이언트로 화면 프레임을 전송합니다.

**메시지 형식**:
```json
{
    "type": "screen",
    "data": "<base64-encoded-jpeg>",
    "width": 1920,
    "height": 1080,
    "timestamp": 1699999999.999
}
```

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | ✅ | 메시지 타입 (고정값: "screen") |
| data | string | ✅ | Base64 인코딩된 JPEG 이미지 |
| width | number | ✅ | 원격 화면 너비 (픽셀) |
| height | number | ✅ | 원격 화면 높이 (픽셀) |
| timestamp | number | ✅ | Unix timestamp (초.밀리초) |

**전송 주기**: 설정된 FPS에 따라 (기본 30 FPS)

**예시**:
```json
{
    "type": "screen",
    "data": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAA...",
    "width": 1920,
    "height": 1080,
    "timestamp": 1699999999.123
}
```

#### 1.2.2 상태 메시지 (status)

서버 상태 또는 일반 메시지를 클라이언트에 전송합니다.

**메시지 형식**:
```json
{
    "type": "status",
    "status": "connected",
    "message": "Connection established"
}
```

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | ✅ | 메시지 타입 (고정값: "status") |
| status | string | ✅ | 상태 값 |
| message | string | ✅ | 상태 메시지 |

**Status 값**:
- `connected`: 연결 성공
- `disconnected`: 연결 해제
- `streaming_started`: 스트리밍 시작
- `streaming_stopped`: 스트리밍 중지

#### 1.2.3 에러 메시지 (error)

에러 발생 시 클라이언트에 에러 정보를 전송합니다.

**메시지 형식**:
```json
{
    "type": "error",
    "message": "Failed to execute action",
    "code": "ACTION_EXECUTION_ERROR",
    "details": {
        "action_type": "click",
        "error": "Coordinate out of bounds"
    }
}
```

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | ✅ | 메시지 타입 (고정값: "error") |
| message | string | ✅ | 에러 메시지 |
| code | string | ✅ | 에러 코드 |
| details | object | ❌ | 추가 에러 정보 |

### 1.3 Client → Server 메시지

#### 1.3.1 클릭 액션 (click)

좌클릭을 실행합니다.

**메시지 형식**:
```json
{
    "type": "action",
    "action_type": "click",
    "x": 100,
    "y": 200
}
```

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | ✅ | 메시지 타입 (고정값: "action") |
| action_type | string | ✅ | 액션 타입 (고정값: "click") |
| x | number | ✅ | 클릭 X 좌표 (픽셀) |
| y | number | ✅ | 클릭 Y 좌표 (픽셀) |

**응답**:
```json
{
    "status": "success",
    "message": null,
    "code": null
}
```

#### 1.3.2 더블클릭 액션 (double_click)

더블클릭을 실행합니다.

**메시지 형식**:
```json
{
    "type": "action",
    "action_type": "double_click",
    "x": 100,
    "y": 200
}
```

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | ✅ | 메시지 타입 (고정값: "action") |
| action_type | string | ✅ | 액션 타입 (고정값: "double_click") |
| x | number | ✅ | 클릭 X 좌표 (픽셀) |
| y | number | ✅ | 클릭 Y 좌표 (픽셀) |

#### 1.3.3 우클릭 액션 (right_click)

우클릭을 실행합니다.

**메시지 형식**:
```json
{
    "type": "action",
    "action_type": "right_click",
    "x": 100,
    "y": 200
}
```

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | ✅ | 메시지 타입 (고정값: "action") |
| action_type | string | ✅ | 액션 타입 (고정값: "right_click") |
| x | number | ✅ | 클릭 X 좌표 (픽셀) |
| y | number | ✅ | 클릭 Y 좌표 (픽셀) |

#### 1.3.4 드래그 액션 (drag)

마우스 드래그를 실행합니다.

**메시지 형식**:
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

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | ✅ | 메시지 타입 (고정값: "action") |
| action_type | string | ✅ | 액션 타입 (고정값: "drag") |
| start_x | number | ✅ | 드래그 시작 X 좌표 (픽셀) |
| start_y | number | ✅ | 드래그 시작 Y 좌표 (픽셀) |
| end_x | number | ✅ | 드래그 종료 X 좌표 (픽셀) |
| end_y | number | ✅ | 드래그 종료 Y 좌표 (픽셀) |

#### 1.3.5 텍스트 입력 액션 (type)

텍스트를 입력합니다.

**메시지 형식**:
```json
{
    "type": "action",
    "action_type": "type",
    "text": "Hello World"
}
```

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | ✅ | 메시지 타입 (고정값: "action") |
| action_type | string | ✅ | 액션 타입 (고정값: "type") |
| text | string | ✅ | 입력할 텍스트 (최대 1000자) |

#### 1.3.6 단축키 액션 (hotkey)

키보드 단축키를 실행합니다.

**메시지 형식**:
```json
{
    "type": "action",
    "action_type": "hotkey",
    "key": "ctrl c"
}
```

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | ✅ | 메시지 타입 (고정값: "action") |
| action_type | string | ✅ | 액션 타입 (고정값: "hotkey") |
| key | string | ✅ | 키 조합 (공백으로 구분) |

**키 조합 예시**:
- `"ctrl c"`: Ctrl+C
- `"cmd v"`: Cmd+V (macOS)
- `"alt tab"`: Alt+Tab
- `"shift enter"`: Shift+Enter
- `"enter"`: Enter 키만

**지원 키**:
- 수정자: `ctrl`, `cmd`, `alt`, `shift`
- 특수 키: `enter`, `tab`, `escape`, `space`, `backspace`, `delete`
- 방향 키: `up`, `down`, `left`, `right` (또는 `arrowup`, `arrowdown`, etc.)
- 기능 키: `f1`, `f2`, ..., `f12`
- 일반 키: `a-z`, `0-9`, 특수문자

#### 1.3.7 스크롤 액션 (scroll)

마우스 휠 스크롤을 실행합니다.

**메시지 형식**:
```json
{
    "type": "action",
    "action_type": "scroll",
    "x": 500,
    "y": 300,
    "direction": "down"
}
```

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | ✅ | 메시지 타입 (고정값: "action") |
| action_type | string | ✅ | 액션 타입 (고정값: "scroll") |
| x | number | ❌ | 스크롤 위치 X 좌표 (픽셀) |
| y | number | ❌ | 스크롤 위치 Y 좌표 (픽셀) |
| direction | string | ✅ | 스크롤 방향 ("up" 또는 "down") |

**Direction 값**:
- `"up"`: 위로 스크롤 (줌인 효과)
- `"down"`: 아래로 스크롤 (줌아웃 효과)

#### 1.3.8 설정 변경 (config) - 향후 지원

품질, FPS 등 설정을 변경합니다.

**메시지 형식**:
```json
{
    "type": "config",
    "setting": "quality",
    "value": 80
}
```

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | ✅ | 메시지 타입 (고정값: "config") |
| setting | string | ✅ | 설정 이름 ("quality" 또는 "fps") |
| value | number | ✅ | 설정 값 |

---

## 2. REST API

### 2.1 루트 엔드포인트

**Endpoint**: `GET /`

**설명**: 클라이언트 HTML을 제공합니다.

**응답**:
- Content-Type: `text/html`
- Body: `static/index.html` 파일 내용

**예시**:
```bash
curl http://localhost:8000/
```

### 2.2 헬스 체크

**Endpoint**: `GET /health`

**설명**: 서버 상태를 확인합니다.

**응답**:
```json
{
    "status": "healthy",
    "service": "web-player",
    "version": "1.0.0"
}
```

**Status Code**: `200 OK`

**예시**:
```bash
curl http://localhost:8000/health

# 응답:
# {"status":"healthy","service":"web-player","version":"1.0.0"}
```

### 2.3 정적 파일

**Endpoint**: `GET /static/*`

**설명**: 정적 파일(CSS, JS, 이미지 등)을 제공합니다.

**예시**:
```bash
curl http://localhost:8000/static/css/style.css
curl http://localhost:8000/static/js/main.js
```

---

## 3. 데이터 모델

### 3.1 ActionRequest

클라이언트가 서버로 보내는 액션 요청

```python
class ActionRequest(BaseModel):
    type: Literal["action"] = "action"
    action_type: str  # "click", "double_click", etc.
    x: Optional[int] = None
    y: Optional[int] = None
    start_x: Optional[int] = None
    start_y: Optional[int] = None
    end_x: Optional[int] = None
    end_y: Optional[int] = None
    text: Optional[str] = None
    key: Optional[str] = None
    direction: Optional[str] = None
```

### 3.2 ActionResponse

서버가 클라이언트로 보내는 액션 응답

```python
class ActionResponse(BaseModel):
    status: Literal["success", "error"]
    message: Optional[str] = None
    code: Optional[str] = None
```

### 3.3 ScreenFrame

서버가 클라이언트로 보내는 화면 프레임

```python
class ScreenFrame(BaseModel):
    type: Literal["screen"] = "screen"
    data: str  # Base64 인코딩된 JPEG
    width: int
    height: int
    timestamp: float
```

### 3.4 StatusMessage

상태 메시지

```python
class StatusMessage(BaseModel):
    type: Literal["status"] = "status"
    status: str
    message: str
```

### 3.5 ErrorMessage

에러 메시지

```python
class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    message: str
    code: str
    details: Optional[dict] = None
```

---

## 4. 에러 코드

### 4.1 클라이언트 에러 (4xx)

| 코드 | 설명 | 원인 | 해결 방법 |
|------|------|------|----------|
| `INVALID_INPUT` | 입력 검증 실패 | 좌표 범위 초과, 필수 필드 누락 | 입력 데이터 확인 |
| `INVALID_ACTION_TYPE` | 알 수 없는 액션 타입 | 지원하지 않는 action_type | 지원 액션 확인 |
| `COORDINATE_ERROR` | 좌표 변환 실패 | 잘못된 좌표 형식 | 좌표 데이터 확인 |

### 4.2 서버 에러 (5xx)

| 코드 | 설명 | 원인 | 해결 방법 |
|------|------|------|----------|
| `SCREEN_CAPTURE_ERROR` | 화면 캡처 실패 | 시스템 리소스 부족, 권한 없음 | 권한 확인, 시스템 리소스 확인 |
| `ACTION_PARSE_ERROR` | 액션 파싱 실패 | UI-TARS 파서 에러 | 로그 확인, 버그 리포트 |
| `ACTION_EXECUTION_ERROR` | 액션 실행 실패 | PyAutoGUI 실행 에러 | 권한 확인, OS 호환성 확인 |
| `WEBSOCKET_ERROR` | WebSocket 통신 에러 | 네트워크 문제, 연결 끊김 | 재연결 시도 |
| `INTERNAL_ERROR` | 내부 서버 에러 | 예기치 않은 에러 | 로그 확인, 버그 리포트 |

### 4.3 에러 응답 예시

```json
{
    "type": "error",
    "message": "X coordinate 9999 out of bounds (0-1920)",
    "code": "INVALID_INPUT",
    "details": {
        "field": "x",
        "value": 9999,
        "max": 1920
    }
}
```

---

## 5. 사용 예시

### 5.1 Python 클라이언트 예시

```python
import asyncio
import websockets
import json


async def test_client():
    uri = "ws://localhost:8000/ws"

    async with websockets.connect(uri) as websocket:
        print("Connected")

        # 화면 프레임 수신 (비동기)
        async def receive_frames():
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                if data["type"] == "screen":
                    print(f"Frame received: {data['width']}x{data['height']}")

        # 액션 전송
        async def send_action():
            await asyncio.sleep(2)  # 2초 대기

            # 클릭 액션 전송
            action = {
                "type": "action",
                "action_type": "click",
                "x": 100,
                "y": 200
            }
            await websocket.send(json.dumps(action))
            print(f"Action sent: {action}")

            # 응답 수신
            response = await websocket.recv()
            print(f"Response: {response}")

        # 두 태스크를 동시 실행
        await asyncio.gather(
            receive_frames(),
            send_action()
        )


asyncio.run(test_client())
```

### 5.2 JavaScript 클라이언트 예시

```javascript
// WebSocket 연결
const ws = new WebSocket('ws://localhost:8000/ws');

// 연결 성공
ws.onopen = () => {
    console.log('Connected to server');

    // 2초 후 클릭 액션 전송
    setTimeout(() => {
        const action = {
            type: 'action',
            action_type: 'click',
            x: 100,
            y: 200
        };
        ws.send(JSON.stringify(action));
        console.log('Action sent:', action);
    }, 2000);
};

// 메시지 수신
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'screen') {
        console.log(`Frame: ${data.width}x${data.height}`);
        // 화면 렌더링
        renderFrame(data);
    }
    else if (data.type === 'error') {
        console.error('Error:', data.message);
    }
    else {
        console.log('Response:', data);
    }
};

// 에러 처리
ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

// 연결 종료
ws.onclose = () => {
    console.log('Disconnected');
};

function renderFrame(frameData) {
    const canvas = document.getElementById('screen-canvas');
    const ctx = canvas.getContext('2d');

    const img = new Image();
    img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
    };
    img.src = 'data:image/jpeg;base64,' + frameData.data;
}
```

### 5.3 curl로 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# WebSocket 연결 (wscat 사용)
# npm install -g wscat
wscat -c ws://localhost:8000/ws

# 연결 후 메시지 전송
> {"type": "action", "action_type": "click", "x": 100, "y": 200}
```

### 5.4 액션 시퀀스 예시

```javascript
// 복잡한 액션 시퀀스
async function performComplexAction(ws) {
    // 1. 특정 위치 클릭
    ws.send(JSON.stringify({
        type: 'action',
        action_type: 'click',
        x: 100,
        y: 200
    }));
    await sleep(500);

    // 2. 텍스트 입력
    ws.send(JSON.stringify({
        type: 'action',
        action_type: 'type',
        text: 'Hello World'
    }));
    await sleep(500);

    // 3. Ctrl+A (전체 선택)
    ws.send(JSON.stringify({
        type: 'action',
        action_type: 'hotkey',
        key: 'ctrl a'
    }));
    await sleep(500);

    // 4. Ctrl+C (복사)
    ws.send(JSON.stringify({
        type: 'action',
        action_type: 'hotkey',
        key: 'ctrl c'
    }));
    await sleep(500);

    // 5. 다른 위치 클릭
    ws.send(JSON.stringify({
        type: 'action',
        action_type: 'click',
        x: 300,
        y: 400
    }));
    await sleep(500);

    // 6. Ctrl+V (붙여넣기)
    ws.send(JSON.stringify({
        type: 'action',
        action_type: 'hotkey',
        key: 'ctrl v'
    }));
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
```

---

## 부록

### A. WebSocket 상태 코드

| 코드 | 설명 |
|------|------|
| 1000 | Normal Closure |
| 1001 | Going Away |
| 1002 | Protocol Error |
| 1003 | Unsupported Data |
| 1006 | Abnormal Closure |
| 1008 | Policy Violation |
| 1011 | Internal Server Error |

### B. 브라우저 호환성

| 기능 | Chrome | Firefox | Safari | Edge |
|------|--------|---------|--------|------|
| WebSocket | ✅ 90+ | ✅ 88+ | ✅ 14+ | ✅ 90+ |
| Canvas | ✅ | ✅ | ✅ | ✅ |
| Fullscreen API | ✅ | ✅ | ✅ | ✅ |

### C. 성능 권장사항

| 항목 | 권장값 | 설명 |
|------|--------|------|
| FPS | 30 | 화면 스트리밍 프레임 속도 |
| Quality | 70% | JPEG 품질 |
| Max Message Size | 10 MB | WebSocket 메시지 크기 제한 |
| Ping Interval | 30s | 연결 유지 확인 간격 |
| Reconnect Delay | 1-16s | 재연결 대기 시간 (exponential backoff) |

---

**관련 문서**:
- [SPEC.md](./SPEC.md) - 전체 기술 스펙
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 아키텍처 설계
- [DEVELOPMENT.md](./DEVELOPMENT.md) - 개발 가이드
