# Web Player - Technical Documentation

웹 브라우저를 통해 원격 컴퓨터 화면을 실시간 스트리밍하고 마우스/키보드 입력을 전달하는 시스템.

---

## 1. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Client                              │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Canvas Display │  │  Event Handlers  │  │ WebSocket Client│ │
│  └────────────────┘  └──────────────────┘  └─────────────────┘ │
└───────────────────────────────┬─────────────────────────────────┘
                                │ WebSocket (JSON)
┌───────────────────────────────▼─────────────────────────────────┐
│                         Server (FastAPI)                        │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ WebSocket      │  │ Screen Controller│  │ Action Handler  │ │
│  │ Endpoint       │◄─┤  (화면 캡처/전송) │◄─┤ (입력 처리)     │ │
│  └────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                      │          │
│                              ┌───────────────────────▼────────┐ │
│                              │ PyAutoGUI / MSS               │ │
│                              └───────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, FastAPI, WebSocket |
| Frontend | Vanilla JS, HTML5 Canvas |
| Screen Capture | MSS, Pillow |
| Input Control | PyAutoGUI |

### Project Structure

```
web-player/
├── src/server/
│   ├── main.py              # FastAPI 앱, WebSocket 엔드포인트
│   ├── config.py            # 환경설정
│   ├── models.py            # Pydantic 데이터 모델
│   ├── screen_controller.py # 화면 캡처 및 스트리밍
│   └── action_handler.py    # 마우스/키보드 액션 처리
├── static/
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── main.js
│       ├── websocket-client.js
│       ├── screen-renderer.js
│       └── input-handler.js
├── run.py
└── requirements.txt
```

---

## 2. API Reference

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | 클라이언트 HTML |
| GET | `/health` | 서버 상태 확인 |

```bash
# Health check
curl http://localhost:8000/health
# Response: {"status":"healthy","service":"web-player","version":"1.0.0","screen":{"width":1920,"height":1080}}
```

### WebSocket API

**Endpoint**: `ws://localhost:8000/ws`

#### Server → Client Messages

**Screen Frame** (30 FPS):
```json
{
    "type": "screen",
    "data": "<base64-jpeg>",
    "width": 1920,
    "height": 1080,
    "timestamp": 1699999999.999
}
```

**Status**:
```json
{
    "type": "status",
    "status": "connected",
    "message": "Connection established"
}
```

**Error**:
```json
{
    "type": "error",
    "message": "Error description",
    "code": "ERROR_CODE"
}
```

#### Client → Server Messages

**Click**:
```json
{"type": "action", "action_type": "click", "x": 100, "y": 200}
```

**Double Click**:
```json
{"type": "action", "action_type": "double_click", "x": 100, "y": 200}
```

**Right Click**:
```json
{"type": "action", "action_type": "right_click", "x": 100, "y": 200}
```

**Drag**:
```json
{"type": "action", "action_type": "drag", "start_x": 100, "start_y": 200, "end_x": 300, "end_y": 400}
```

**Type Text**:
```json
{"type": "action", "action_type": "type", "text": "Hello World"}
```

**Hotkey**:
```json
{"type": "action", "action_type": "hotkey", "key": "ctrl c"}
```

**Scroll**:
```json
{"type": "action", "action_type": "scroll", "x": 500, "y": 300, "direction": "down"}
```

**Config Change**:
```json
{"type": "config", "setting": "quality", "value": 80}
```

### Data Models

```python
class ActionRequest(BaseModel):
    type: Literal["action"] = "action"
    action_type: str  # click, double_click, right_click, drag, type, hotkey, scroll
    x: Optional[int] = None
    y: Optional[int] = None
    start_x: Optional[int] = None
    start_y: Optional[int] = None
    end_x: Optional[int] = None
    end_y: Optional[int] = None
    text: Optional[str] = None
    key: Optional[str] = None
    direction: Optional[str] = None

class ActionResponse(BaseModel):
    status: Literal["success", "error"]
    message: Optional[str] = None
    code: Optional[str] = None

class ScreenFrame(BaseModel):
    type: Literal["screen"] = "screen"
    data: str  # Base64 encoded JPEG
    width: int
    height: int
    timestamp: float
```

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_INPUT` | 입력 검증 실패 |
| `EXECUTION_ERROR` | 액션 실행 실패 |
| `ACTION_ERROR` | 액션 처리 에러 |

---

## 3. Development

### Setup

```bash
# Clone
git clone git@github.com:seunghyun-kim-bagel/web-player.git
cd web-player

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
# Development (with hot reload)
python run.py

# Production
uvicorn src.server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_HOST` | 0.0.0.0 | 서버 호스트 |
| `SERVER_PORT` | 8000 | 서버 포트 |
| `SCREEN_FPS` | 30 | 화면 캡처 FPS |
| `SCREEN_QUALITY` | 70 | JPEG 품질 (1-100) |
| `LOG_LEVEL` | INFO | 로그 레벨 |

### Testing

```bash
# Health check
curl http://localhost:8000/health

# WebSocket test (requires wscat)
npm install -g wscat
wscat -c ws://localhost:8000/ws

# Send action
> {"type": "action", "action_type": "click", "x": 100, "y": 200}
```

---

## 4. Features

### Supported Actions

| Action | Description | Required Fields |
|--------|-------------|-----------------|
| `click` | 좌클릭 | x, y |
| `double_click` | 더블클릭 | x, y |
| `right_click` | 우클릭 | x, y |
| `drag` | 드래그 | start_x, start_y, end_x, end_y |
| `type` | 텍스트 입력 | text |
| `hotkey` | 단축키 | key |
| `scroll` | 스크롤 | direction, (x, y optional) |
| `hover` | 마우스 이동 | x, y |

### Hotkey Format

키는 공백으로 구분:
- `ctrl c` → Ctrl+C
- `cmd v` → Cmd+V (macOS)
- `alt tab` → Alt+Tab
- `enter` → Enter

### Requirements

- **Server**: Python 3.10+, macOS/Windows/Linux
- **Client**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

---

## 5. Coordinate System

Canvas 좌표를 원격 화면 좌표로 변환:

```javascript
// Canvas → Remote
remoteX = canvasX * (remoteWidth / canvasWidth)
remoteY = canvasY * (remoteHeight / canvasHeight)
```

---

## 6. Performance

| Metric | Target |
|--------|--------|
| FPS | 30 |
| Latency | < 500ms |
| Response time | < 100ms |
