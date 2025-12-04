# Web Player - 개발 가이드

## 목차
1. [개발 환경 설정](#1-개발-환경-설정)
2. [단계별 구현 가이드](#2-단계별-구현-가이드)
3. [코드 작성 규칙](#3-코드-작성-규칙)
4. [테스트 가이드](#4-테스트-가이드)
5. [디버깅 팁](#5-디버깅-팁)
6. [배포 가이드](#6-배포-가이드)

---

## 1. 개발 환경 설정

### 1.1 필수 요구사항

**운영체제**:
- Windows 10/11
- macOS 11+ (Big Sur 이상)
- Ubuntu 20.04+

**소프트웨어**:
- Python 3.10 이상
- Git
- 텍스트 에디터 (VS Code 권장)

**브라우저**:
- Chrome 90+ (개발 권장)
- Firefox 88+
- Safari 14+
- Edge 90+

### 1.2 환경 설정 단계

#### Step 1: 레포지토리 클론

```bash
# 레포지토리 클론
git clone git@github.com:seunghyun-kim-bagel/web-player.git
cd web-player

# 브랜치 확인
git branch
```

#### Step 2: Python 가상환경 생성

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# 가상환경이 활성화되면 프롬프트 앞에 (venv) 표시됨
```

#### Step 3: 의존성 설치

```bash
# pip 업그레이드
pip install --upgrade pip

# 프로젝트 의존성 설치
pip install -r requirements.txt

# 설치 확인
pip list
```

**주요 패키지 확인**:
- ui-tars
- fastapi
- uvicorn
- pyautogui
- pillow
- mss

#### Step 4: 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (선택사항)
# Windows:
notepad .env

# macOS/Linux:
nano .env
```

**기본 설정**:
```env
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SCREEN_FPS=30
SCREEN_QUALITY=70
ENABLE_AUTH=false
LOG_LEVEL=INFO
```

#### Step 5: VS Code 설정 (권장)

**.vscode/settings.json** 생성:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "[javascript]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode"
    }
}
```

**.vscode/launch.json** 생성 (디버깅용):
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.server.main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000"
            ],
            "jinja": true,
            "justMyCode": false
        }
    ]
}
```

---

## 2. 단계별 구현 가이드

### Phase 1: 서버 기본 구조 (1-2일)

#### Step 1.1: FastAPI 앱 생성

**파일**: `src/server/main.py`

```python
"""
Web Player - FastAPI 애플리케이션 진입점
"""
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Web Player",
    description="UI-TARS 기반 원격 데스크톱 제어 시스템",
    version="1.0.0"
)

# Static 파일 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """클라이언트 HTML 제공"""
    html_path = Path("static/index.html")
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return {"message": "Web Player API"}


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "web-player",
        "version": "1.0.0"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 연결 엔드포인트"""
    await websocket.accept()
    logger.info("Client connected")

    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_json()
            logger.info(f"Received: {data}")

            # Echo back (임시)
            await websocket.send_json({
                "type": "status",
                "message": "Echo: " + str(data)
            })

    except WebSocketDisconnect:
        logger.info("Client disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

**테스트**:
```bash
# 서버 실행
python src/server/main.py

# 브라우저에서 접속
# http://localhost:8000/health
# 결과: {"status": "healthy", ...}
```

#### Step 1.2: 설정 관리

**파일**: `src/server/config.py`

```python
"""
설정 관리
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # Screen Capture
    screen_fps: int = 30
    screen_quality: int = 70
    screen_format: str = "JPEG"

    # Security
    enable_auth: bool = False
    auth_token: Optional[str] = None

    # WebSocket
    ws_ping_interval: int = 30
    ws_ping_timeout: int = 10

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/server.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 전역 설정 인스턴스
settings = Settings()
```

**사용 예시**:
```python
from src.server.config import settings

print(f"FPS: {settings.screen_fps}")
print(f"Quality: {settings.screen_quality}")
```

#### Step 1.3: 데이터 모델 정의

**파일**: `src/server/models.py`

```python
"""
Pydantic 데이터 모델
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class ActionRequest(BaseModel):
    """클라이언트 액션 요청"""
    type: Literal["action"] = "action"
    action_type: str = Field(..., description="액션 타입")
    x: Optional[int] = Field(None, description="X 좌표")
    y: Optional[int] = Field(None, description="Y 좌표")
    start_x: Optional[int] = None
    start_y: Optional[int] = None
    end_x: Optional[int] = None
    end_y: Optional[int] = None
    text: Optional[str] = None
    key: Optional[str] = None
    direction: Optional[str] = None


class ActionResponse(BaseModel):
    """액션 실행 결과"""
    status: Literal["success", "error"]
    message: Optional[str] = None
    code: Optional[str] = None


class ScreenFrame(BaseModel):
    """화면 프레임 데이터"""
    type: Literal["screen"] = "screen"
    data: str = Field(..., description="Base64 인코딩된 이미지")
    width: int
    height: int
    timestamp: float


class StatusMessage(BaseModel):
    """상태 메시지"""
    type: Literal["status"] = "status"
    status: str
    message: str


class ErrorMessage(BaseModel):
    """에러 메시지"""
    type: Literal["error"] = "error"
    message: str
    code: str
    details: Optional[dict] = None
```

---

### Phase 2: 화면 캡처 및 스트리밍 (2-3일)

#### Step 2.1: ScreenController 구현

**파일**: `src/server/screen_controller.py`

```python
"""
화면 캡처 및 스트리밍 컨트롤러
"""
import asyncio
import base64
import logging
import time
from io import BytesIO
from typing import Optional

import mss
import pyautogui
from PIL import Image
from fastapi import WebSocket

from .config import settings
from .models import ScreenFrame

logger = logging.getLogger(__name__)


class ScreenController:
    """화면 캡처 및 스트리밍 관리"""

    def __init__(
        self,
        fps: int = None,
        quality: int = None
    ):
        """
        Args:
            fps: 초당 프레임 수 (기본값: settings.screen_fps)
            quality: JPEG 품질 1-100 (기본값: settings.screen_quality)
        """
        self.fps = fps or settings.screen_fps
        self.quality = quality or settings.screen_quality
        self.screen_width, self.screen_height = pyautogui.size()
        self.is_streaming = False
        self.frame_count = 0

        logger.info(
            f"ScreenController initialized: "
            f"{self.screen_width}x{self.screen_height} @ {self.fps} FPS"
        )

    async def start_streaming(self, websocket: WebSocket):
        """
        화면 스트리밍 시작

        Args:
            websocket: 연결된 WebSocket 클라이언트
        """
        self.is_streaming = True
        interval = 1.0 / self.fps

        logger.info("Screen streaming started")

        try:
            while self.is_streaming:
                loop_start = time.time()

                # 화면 캡처
                frame = self.capture_frame()

                if frame:
                    # 프레임 전송
                    await websocket.send_json(frame.model_dump())
                    self.frame_count += 1

                    # FPS 유지를 위한 대기
                    elapsed = time.time() - loop_start
                    sleep_time = max(0, interval - elapsed)
                    await asyncio.sleep(sleep_time)
                else:
                    # 캡처 실패 시 짧게 대기
                    await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
        finally:
            self.is_streaming = False
            logger.info(
                f"Screen streaming stopped. Total frames: {self.frame_count}"
            )

    def capture_frame(self) -> Optional[ScreenFrame]:
        """
        단일 프레임 캡처

        Returns:
            ScreenFrame 또는 None (실패 시)
        """
        try:
            with mss.mss() as sct:
                # 주 모니터 캡처
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)

                # PIL Image로 변환
                img = Image.frombytes(
                    'RGB',
                    screenshot.size,
                    screenshot.rgb
                )

                # JPEG 압축 및 Base64 인코딩
                buffered = BytesIO()
                img.save(
                    buffered,
                    format=settings.screen_format,
                    quality=self.quality
                )
                img_base64 = base64.b64encode(buffered.getvalue()).decode()

                return ScreenFrame(
                    data=img_base64,
                    width=screenshot.width,
                    height=screenshot.height,
                    timestamp=time.time()
                )

        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return None

    def stop_streaming(self):
        """스트리밍 중지"""
        self.is_streaming = False
        logger.info("Streaming stop requested")
```

**main.py에 통합**:
```python
from .screen_controller import ScreenController

# 전역 컨트롤러 인스턴스
screen_controller = ScreenController()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected")

    # 스트리밍 태스크 시작
    streaming_task = asyncio.create_task(
        screen_controller.start_streaming(websocket)
    )

    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"Received: {data}")

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    finally:
        screen_controller.stop_streaming()
        streaming_task.cancel()
```

**테스트**:
```bash
# 서버 실행
python src/server/main.py

# WebSocket 클라이언트로 테스트 (별도 터미널)
# pip install websocket-client
python -c "
import websocket
ws = websocket.WebSocket()
ws.connect('ws://localhost:8000/ws')
msg = ws.recv()
print(msg[:100])  # 첫 100자 출력
ws.close()
"
```

---

### Phase 3: 액션 처리 (2-3일)

#### Step 3.1: ActionHandler 구현

**파일**: `src/server/action_handler.py`

```python
"""
UI-TARS 기반 액션 처리
"""
import logging
from typing import Dict

import pyautogui
from ui_tars.action_parser import (
    parse_action_to_structure_output,
    parsing_response_to_pyautogui_code
)

from .models import ActionRequest, ActionResponse

logger = logging.getLogger(__name__)


class ActionHandler:
    """액션 처리 핸들러"""

    def __init__(self, screen_width: int, screen_height: int):
        """
        Args:
            screen_width: 화면 너비
            screen_height: 화면 높이
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        logger.info(
            f"ActionHandler initialized: {screen_width}x{screen_height}"
        )

    async def process_action(self, action: ActionRequest) -> ActionResponse:
        """
        액션 처리

        Args:
            action: 액션 요청 데이터

        Returns:
            ActionResponse
        """
        try:
            # 입력 검증
            self._validate_action(action)

            # UI-TARS 형식으로 변환
            uitars_response = self._convert_to_uitars_format(action)
            logger.debug(f"UI-TARS format: {uitars_response}")

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

            logger.debug(f"PyAutoGUI code:\n{pyautogui_code}")

            # 실행
            if pyautogui_code != "DONE":
                exec(pyautogui_code)

            logger.info(f"Action executed: {action.action_type}")
            return ActionResponse(status="success")

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return ActionResponse(
                status="error",
                code="INVALID_INPUT",
                message=str(e)
            )
        except Exception as e:
            logger.error(f"Action processing error: {e}", exc_info=True)
            return ActionResponse(
                status="error",
                code="EXECUTION_ERROR",
                message=str(e)
            )

    def _validate_action(self, action: ActionRequest):
        """액션 검증"""
        if action.x is not None:
            if not (0 <= action.x <= self.screen_width):
                raise ValueError(
                    f"X coordinate {action.x} out of bounds "
                    f"(0-{self.screen_width})"
                )

        if action.y is not None:
            if not (0 <= action.y <= self.screen_height):
                raise ValueError(
                    f"Y coordinate {action.y} out of bounds "
                    f"(0-{self.screen_height})"
                )

    def _convert_to_uitars_format(self, action: ActionRequest) -> str:
        """
        클라이언트 액션을 UI-TARS 형식으로 변환

        Args:
            action: ActionRequest

        Returns:
            UI-TARS 형식 문자열
        """
        action_type = action.action_type

        if action_type == "click":
            x, y = action.x, action.y
            return f"Thought: Click action\nAction: click(start_box='({x},{y})')"

        elif action_type == "double_click":
            x, y = action.x, action.y
            return f"Action: left_double(start_box='({x},{y})')"

        elif action_type == "right_click":
            x, y = action.x, action.y
            return f"Action: right_single(start_box='({x},{y})')"

        elif action_type == "drag":
            x1, y1 = action.start_x, action.start_y
            x2, y2 = action.end_x, action.end_y
            return f"Action: drag(start_box='({x1},{y1})', end_box='({x2},{y2})')"

        elif action_type == "type":
            text = action.text
            return f"Action: type(content='{text}')"

        elif action_type == "hotkey":
            keys = action.key
            return f"Action: hotkey(key='{keys}')"

        elif action_type == "scroll":
            x, y = action.x or 0, action.y or 0
            direction = action.direction or "down"
            return f"Action: scroll(start_box='({x},{y})', direction='{direction}')"

        else:
            raise ValueError(f"Unknown action type: {action_type}")
```

**main.py에 통합**:
```python
from .action_handler import ActionHandler
from .models import ActionRequest

# 전역 핸들러 인스턴스
screen_controller = ScreenController()
action_handler = ActionHandler(
    screen_width=screen_controller.screen_width,
    screen_height=screen_controller.screen_height
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected")

    # 스트리밍 시작
    streaming_task = asyncio.create_task(
        screen_controller.start_streaming(websocket)
    )

    try:
        while True:
            # 클라이언트로부터 액션 수신
            data = await websocket.receive_json()

            if data.get("type") == "action":
                # 액션 처리
                action = ActionRequest(**data)
                result = await action_handler.process_action(action)

                # 결과 전송
                await websocket.send_json(result.model_dump())

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    finally:
        screen_controller.stop_streaming()
        streaming_task.cancel()
```

---

### Phase 4: 클라이언트 구현 (3-4일)

#### Step 4.1: HTML 구조

**파일**: `static/index.html`

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
    <!-- 상태 표시 바 -->
    <div id="status-bar">
        <div class="status-left">
            <span id="connection-status" class="status-disconnected">Disconnected</span>
        </div>
        <div class="status-right">
            <span id="fps-counter">0 FPS</span>
            <span id="latency">0 ms</span>
        </div>
    </div>

    <!-- 화면 컨테이너 -->
    <div id="screen-container">
        <canvas id="screen-canvas"></canvas>
        <div id="loading" class="loading">
            <div class="spinner"></div>
            <p>Connecting...</p>
        </div>
    </div>

    <!-- 컨트롤 패널 -->
    <div id="control-panel">
        <button id="btn-connect" class="btn btn-primary">Connect</button>
        <button id="btn-disconnect" class="btn btn-secondary" disabled>Disconnect</button>
        <button id="btn-fullscreen" class="btn btn-secondary">Fullscreen</button>

        <div class="settings">
            <label for="quality-slider">
                Quality:
                <input type="range" id="quality-slider" min="10" max="100" value="70" step="10">
                <span id="quality-value">70%</span>
            </label>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="/static/js/websocket-client.js"></script>
    <script src="/static/js/screen-renderer.js"></script>
    <script src="/static/js/input-handler.js"></script>
    <script src="/static/js/main.js"></script>
</body>
</html>
```

#### Step 4.2: CSS 스타일

**파일**: `static/css/style.css`

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #1e1e1e;
    color: #ffffff;
    overflow: hidden;
}

/* 상태 바 */
#status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 20px;
    background: #2d2d2d;
    border-bottom: 1px solid #3d3d3d;
}

#connection-status {
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
}

.status-connected {
    background: #28a745;
    color: white;
}

.status-disconnected {
    background: #dc3545;
    color: white;
}

.status-connecting {
    background: #ffc107;
    color: black;
}

.status-error {
    background: #ff6b6b;
    color: white;
}

#fps-counter, #latency {
    margin-left: 20px;
    font-size: 14px;
    color: #aaa;
}

/* 화면 컨테이너 */
#screen-container {
    position: relative;
    width: 100vw;
    height: calc(100vh - 100px);
    display: flex;
    justify-content: center;
    align-items: center;
    background: #000;
}

#screen-canvas {
    max-width: 100%;
    max-height: 100%;
    cursor: crosshair;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.loading {
    position: absolute;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
}

.spinner {
    width: 50px;
    height: 50px;
    border: 5px solid #3d3d3d;
    border-top: 5px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 컨트롤 패널 */
#control-panel {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 20px;
    background: #2d2d2d;
    border-top: 1px solid #3d3d3d;
}

.btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-primary {
    background: #007bff;
    color: white;
}

.btn-primary:hover {
    background: #0056b3;
}

.btn-secondary {
    background: #6c757d;
    color: white;
}

.btn-secondary:hover {
    background: #5a6268;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.settings {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 10px;
}

.settings label {
    font-size: 14px;
    color: #aaa;
}

#quality-slider {
    width: 100px;
}

#quality-value {
    font-weight: 600;
    color: #fff;
}
```

#### Step 4.3: JavaScript - WebSocket Client

**파일**: `static/js/websocket-client.js`

```javascript
/**
 * WebSocket 클라이언트
 */
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
        console.log(`Connecting to ${this.url}`);
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
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.error('WebSocket is not connected');
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connect(), delay);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    on(event, callback) {
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

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}
```

#### Step 4.4: JavaScript - Screen Renderer

**파일**: `static/js/screen-renderer.js`

```javascript
/**
 * 화면 렌더러
 */
class ScreenRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.remoteWidth = 0;
        this.remoteHeight = 0;
        this.lastFrameTime = 0;
        this.fps = 0;
        this.frameCount = 0;
    }

    renderFrame(frameData) {
        this.remoteWidth = frameData.width;
        this.remoteHeight = frameData.height;

        const img = new Image();
        img.onload = () => {
            // 캔버스 크기 조정 (최초 1회)
            if (this.canvas.width !== img.width || this.canvas.height !== img.height) {
                this.canvas.width = img.width;
                this.canvas.height = img.height;
                console.log(`Canvas resized to ${img.width}x${img.height}`);
            }

            // 화면 그리기
            this.ctx.drawImage(img, 0, 0);

            // FPS 계산
            this.calculateFPS();
            this.frameCount++;
        };

        img.src = 'data:image/jpeg;base64,' + frameData.data;
    }

    calculateFPS() {
        const now = performance.now();
        if (this.lastFrameTime) {
            const delta = now - this.lastFrameTime;
            this.fps = Math.round(1000 / delta);
        }
        this.lastFrameTime = now;
    }

    canvasToRemoteCoords(canvasX, canvasY) {
        const scaleX = this.remoteWidth / this.canvas.width;
        const scaleY = this.remoteHeight / this.canvas.height;

        return {
            x: Math.round(canvasX * scaleX),
            y: Math.round(canvasY * scaleY)
        };
    }

    drawClickFeedback(canvasX, canvasY) {
        this.ctx.beginPath();
        this.ctx.arc(canvasX, canvasY, 10, 0, 2 * Math.PI);
        this.ctx.strokeStyle = 'rgba(255, 0, 0, 0.8)';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
    }

    getFPS() {
        return this.fps;
    }
}
```

#### Step 4.5: JavaScript - Input Handler

**파일**: `static/js/input-handler.js`

```javascript
/**
 * 입력 핸들러
 */
class InputHandler {
    constructor(canvas, wsClient, renderer) {
        this.canvas = canvas;
        this.wsClient = wsClient;
        this.renderer = renderer;
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;

        this.setupEventListeners();
    }

    setupEventListeners() {
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

        // 키보드
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    getCanvasCoords(event) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            canvasX: event.clientX - rect.left,
            canvasY: event.clientY - rect.top
        };
    }

    handleClick(event) {
        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);

        this.wsClient.send({
            type: 'action',
            action_type: 'click',
            x: remoteCoords.x,
            y: remoteCoords.y
        });

        this.renderer.drawClickFeedback(canvasX, canvasY);
        console.log(`Click at (${remoteCoords.x}, ${remoteCoords.y})`);
    }

    handleDoubleClick(event) {
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
        this.isDragging = true;
        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);
        this.dragStartX = remoteCoords.x;
        this.dragStartY = remoteCoords.y;
    }

    handleMouseMove(event) {
        if (!this.isDragging) return;
        // 드래그 시각화 (선택사항)
    }

    handleMouseUp(event) {
        if (!this.isDragging) return;

        this.isDragging = false;
        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);

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
        // Ctrl/Cmd + Key 조합
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
    }
}
```

#### Step 4.6: JavaScript - Main App

**파일**: `static/js/main.js`

```javascript
/**
 * 메인 애플리케이션
 */

// 전역 변수
let wsClient;
let screenRenderer;
let inputHandler;

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log('Web Player initializing...');
    initializeApp();
});

function initializeApp() {
    // WebSocket 클라이언트
    const wsUrl = `ws://${window.location.host}/ws`;
    wsClient = new WebSocketClient(wsUrl);

    // 화면 렌더러
    screenRenderer = new ScreenRenderer('screen-canvas');

    // 입력 핸들러
    const canvas = document.getElementById('screen-canvas');
    inputHandler = new InputHandler(canvas, wsClient, screenRenderer);

    // WebSocket 이벤트 핸들러
    wsClient.on('open', handleWebSocketOpen);
    wsClient.on('message', handleWebSocketMessage);
    wsClient.on('error', handleWebSocketError);
    wsClient.on('close', handleWebSocketClose);

    // UI 컨트롤
    setupUIControls();

    console.log('Web Player initialized');
}

function handleWebSocketOpen(event) {
    console.log('Connected to server');
    updateConnectionStatus('connected', 'Connected');
    hideLoading();
    enableDisconnectButton();
}

function handleWebSocketMessage(data) {
    if (data.type === 'screen') {
        screenRenderer.renderFrame(data);
        updateFPS(screenRenderer.getFPS());
    }
    else if (data.type === 'status') {
        console.log('Status:', data.message);
    }
    else if (data.type === 'error') {
        console.error('Server error:', data.message);
        updateConnectionStatus('error', data.message);
    }
}

function handleWebSocketError(event) {
    console.error('WebSocket error:', event);
    updateConnectionStatus('error', 'Connection error');
}

function handleWebSocketClose(event) {
    console.log('Disconnected from server');
    updateConnectionStatus('disconnected', 'Disconnected');
    showLoading();
    enableConnectButton();
}

function setupUIControls() {
    // 연결 버튼
    document.getElementById('btn-connect').addEventListener('click', () => {
        wsClient.connect();
        updateConnectionStatus('connecting', 'Connecting...');
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

    // 품질 슬라이더
    const qualitySlider = document.getElementById('quality-slider');
    const qualityValue = document.getElementById('quality-value');

    qualitySlider.addEventListener('input', (e) => {
        qualityValue.textContent = e.target.value + '%';
    });

    qualitySlider.addEventListener('change', (e) => {
        const quality = e.target.value;
        console.log(`Quality changed to ${quality}%`);
        // TODO: 서버에 품질 변경 요청
    });
}

// UI 업데이트 함수
function updateConnectionStatus(status, message) {
    const statusElement = document.getElementById('connection-status');
    statusElement.textContent = message;
    statusElement.className = `status-${status}`;
}

function updateFPS(fps) {
    document.getElementById('fps-counter').textContent = `${fps} FPS`;
}

function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function enableConnectButton() {
    document.getElementById('btn-connect').disabled = false;
    document.getElementById('btn-disconnect').disabled = true;
}

function enableDisconnectButton() {
    document.getElementById('btn-connect').disabled = true;
    document.getElementById('btn-disconnect').disabled = false;
}
```

---

## 3. 코드 작성 규칙

### 3.1 Python 코드 스타일

- **PEP 8** 준수
- **Type hints** 사용
- **Docstrings** 작성 (Google 스타일)

```python
def process_action(self, action: ActionRequest) -> ActionResponse:
    """
    액션을 처리합니다.

    Args:
        action: 액션 요청 데이터

    Returns:
        ActionResponse: 처리 결과

    Raises:
        ValueError: 입력 검증 실패 시
        ExecutionError: 실행 중 에러 발생 시
    """
    pass
```

### 3.2 JavaScript 코드 스타일

- **ES6+** 문법 사용
- **JSDoc** 주석 작성
- **camelCase** 네이밍

```javascript
/**
 * 화면 프레임을 렌더링합니다.
 * @param {Object} frameData - 프레임 데이터
 * @param {string} frameData.data - Base64 인코딩된 이미지
 * @param {number} frameData.width - 화면 너비
 * @param {number} frameData.height - 화면 높이
 */
renderFrame(frameData) {
    // ...
}
```

### 3.3 Git 커밋 메시지

```
<type>: <subject>

<body>

<footer>
```

**Type**:
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드/설정 변경

**예시**:
```
feat: Add screen streaming functionality

Implement ScreenController class with mss-based capture
and WebSocket streaming at 30 FPS.

Closes #1
```

---

## 4. 테스트 가이드

### 4.1 단위 테스트

**파일**: `tests/test_action_handler.py`

```python
import pytest
from src.server.action_handler import ActionHandler
from src.server.models import ActionRequest


class TestActionHandler:
    @pytest.fixture
    def handler(self):
        return ActionHandler(screen_width=1920, screen_height=1080)

    def test_validate_coordinates_valid(self, handler):
        """유효한 좌표 검증"""
        action = ActionRequest(
            action_type="click",
            x=100,
            y=200
        )
        handler._validate_action(action)  # 에러 없이 통과

    def test_validate_coordinates_out_of_bounds(self, handler):
        """범위 밖 좌표 검증"""
        action = ActionRequest(
            action_type="click",
            x=9999,
            y=200
        )
        with pytest.raises(ValueError):
            handler._validate_action(action)

    def test_convert_click_action(self, handler):
        """클릭 액션 변환"""
        action = ActionRequest(
            action_type="click",
            x=100,
            y=200
        )
        result = handler._convert_to_uitars_format(action)
        assert "click(start_box='(100,200)')" in result
```

**실행**:
```bash
pytest tests/ -v
```

### 4.2 통합 테스트

**파일**: `tests/test_integration.py`

```python
import pytest
from fastapi.testclient import TestClient
from src.server.main import app


client = TestClient(app)


def test_health_check():
    """헬스 체크 엔드포인트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_websocket_connection():
    """WebSocket 연결 테스트"""
    with client.websocket_connect("/ws") as websocket:
        # 화면 프레임 수신
        data = websocket.receive_json()
        assert data["type"] == "screen"
        assert "data" in data
        assert "width" in data
        assert "height" in data
```

---

## 5. 디버깅 팁

### 5.1 서버 디버깅

**로깅 레벨 조정**:
```python
logging.basicConfig(level=logging.DEBUG)
```

**VS Code 디버거 사용**:
1. F5 키 또는 "Run and Debug" 클릭
2. Breakpoint 설정
3. 변수 inspect

### 5.2 클라이언트 디버깅

**브라우저 개발자 도구**:
1. F12 키로 개발자 도구 열기
2. Console 탭: 로그 확인
3. Network 탭 > WS: WebSocket 메시지 확인
4. Sources 탭: JavaScript 디버깅

**WebSocket 메시지 모니터링**:
```javascript
// wsClient에 추가
this.ws.onmessage = (event) => {
    console.log('Received:', event.data);  // 모든 메시지 로깅
    // ...
};
```

---

## 6. 배포 가이드

### 6.1 개발 환경

```bash
python src/server/main.py
```

### 6.2 프로덕션 환경

```bash
# Uvicorn으로 실행
uvicorn src.server.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info
```

### 6.3 Docker 배포 (향후)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

**다음 단계**: [API.md](./API.md)에서 API 명세를 확인하세요.
