# Web Player - 목표 기반 자동화 설계 문서

## 1. 개요

### 1.1 목적
현재 Web Player의 단일 명령 → 단일 액션 방식을 확장하여, 사용자가 목표를 설정하면 해당 목표를 달성할 때까지 자동으로 화면을 분석하고 액션을 실행하는 **목표 기반 자동화** 기능을 구현한다.

### 1.2 현재 방식 vs 목표 기반 방식

| 구분 | 현재 방식 | 목표 기반 방식 |
|------|----------|---------------|
| 입력 | 단일 명령 (예: "버튼 클릭해줘") | 목표 (예: "로그인 완료") |
| 실행 | 1회 분석 → 1회 액션 | 반복 (분석 → 결정 → 액션) |
| 종료 | 즉시 완료 | 목표 달성 시 종료 |
| 상태 관리 | 없음 | 액션 히스토리 + 상태 추적 |

### 1.3 활용 시나리오

- 게임 자동화: "일일 퀘스트 완료"
- 반복 작업: "모든 이메일 읽음 처리"
- 테스트 자동화: "회원가입 프로세스 완료"

---

## 2. 시스템 아키텍처

### 2.1 전체 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Browser (UI)                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  [목표 입력] ─────────────────────────────────────────  │    │
│  │  ┌──────────────────────────────────────────────────┐   │    │
│  │  │  목표: 로그인 완료                    [시작] [중지] │   │    │
│  │  └──────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  │  [실행 상태]                                              │    │
│  │  ┌──────────────────────────────────────────────────┐   │    │
│  │  │  Step 3/50 | 진행률: 60% | 상태: 비밀번호 입력 중  │   │    │
│  │  └──────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  │  [화면 + 액션 로그]                                       │    │
│  │  ┌─────────────────────┐  ┌─────────────────────────┐   │    │
│  │  │                     │  │ Step 1: 로그인 버튼 클릭  │   │    │
│  │  │   Screen Canvas     │  │ Step 2: ID 입력 필드 클릭 │   │    │
│  │  │                     │  │ Step 3: 비밀번호 입력...  │   │    │
│  │  └─────────────────────┘  └─────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │ WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Server                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   GoalAutomationRunner                    │   │
│  │                                                           │   │
│  │   ┌─────────┐    ┌──────────┐    ┌─────────────────┐    │   │
│  │   │ Screen  │───▶│ GPT-4o   │───▶│ Decision Engine │    │   │
│  │   │ Capture │    │ Analyzer │    │ + Safety Policy │    │   │
│  │   └─────────┘    └──────────┘    └─────────────────┘    │   │
│  │        │              │                   │              │   │
│  │        ▼              ▼                   ▼              │   │
│  │   ┌─────────────────────────────────────────────────┐   │   │
│  │   │              Execution Context                   │   │   │
│  │   │  - goal: str                                     │   │   │
│  │   │  - action_history: List[Action]                  │   │   │
│  │   │  - current_step: int                             │   │   │
│  │   │  - goal_status: GoalStatus                       │   │   │
│  │   └─────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Action Handler                         │   │
│  │                  (PyAutoGUI 실행)                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 실행 플로우

```
┌─────────────────────────────────────────────────────────────┐
│                     Goal Automation Loop                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  목표 설정 수신  │
                    │ (WebSocket)     │
                    └────────┬────────┘
                              │
                    ┌─────────▼─────────┐
                    │  종료 조건 체크    │◄──────────────────┐
                    │  - 목표 달성?     │                   │
                    │  - 최대 스텝?     │                   │
                    │  - 사용자 중지?   │                   │
                    └─────────┬─────────┘                   │
                              │                              │
                      목표 미달성                            │
                              │                              │
                    ┌─────────▼─────────┐                   │
                    │  Phase 1: 캡처    │                   │
                    │  화면 스크린샷    │                   │
                    └─────────┬─────────┘                   │
                              │                              │
                    ┌─────────▼─────────┐                   │
                    │  Phase 2: 분석    │                   │
                    │  GPT-4o Vision    │                   │
                    │  - 화면 상태      │                   │
                    │  - UI 요소 감지   │                   │
                    │  - 목표 달성 여부  │                   │
                    │  - 추천 액션      │                   │
                    └─────────┬─────────┘                   │
                              │                              │
                    ┌─────────▼─────────┐                   │
                    │  Phase 3: 결정    │                   │
                    │  - 안전 정책 검증  │                   │
                    │  - 반복 클릭 방지  │                   │
                    │  - 최종 액션 결정  │                   │
                    └─────────┬─────────┘                   │
                              │                              │
                    ┌─────────▼─────────┐                   │
                    │  Phase 4: 실행    │                   │
                    │  PyAutoGUI 액션   │                   │
                    └─────────┬─────────┘                   │
                              │                              │
                    ┌─────────▼─────────┐                   │
                    │  상태 업데이트     │                   │
                    │  - 히스토리 기록   │                   │
                    │  - UI 상태 전송    │                   │
                    └─────────┬─────────┘                   │
                              │                              │
                              └──────────────────────────────┘
```

---

## 3. 핵심 컴포넌트

### 3.1 데이터 타입 정의

```python
# src/server/models.py 에 추가

from dataclasses import dataclass
from typing import Literal, Optional, List
from datetime import datetime

@dataclass
class GoalStatus:
    """목표 달성 상태"""
    achieved: bool                      # 목표 달성 여부
    progress_description: str           # 진행 상황 설명
    progress_percent: int               # 진행률 (0-100)
    confidence: float                   # 판단 신뢰도 (0.0-1.0)


@dataclass
class ActionHistoryEntry:
    """액션 히스토리 항목"""
    step: int
    timestamp: datetime
    action_type: str                    # click, type, scroll, wait
    action_params: dict                 # x, y, text, direction 등
    thought: str                        # AI의 사고 과정
    screen_description: str             # 당시 화면 상태


@dataclass
class AutomationContext:
    """자동화 실행 컨텍스트"""
    goal: str                           # 사용자 목표
    started_at: datetime
    current_step: int
    max_steps: int
    action_history: List[ActionHistoryEntry]
    goal_status: GoalStatus
    is_running: bool
    finish_reason: Optional[str]        # goal_achieved, max_steps, user_stopped, error


class GoalAutomationRequest(BaseModel):
    """목표 자동화 요청"""
    type: Literal["goal_automation"] = "goal_automation"
    action: Literal["start", "stop"]
    goal: Optional[str] = None          # start 시 필수
    max_steps: int = 50                 # 최대 반복 횟수


class GoalAutomationStatus(BaseModel):
    """목표 자동화 상태 (WebSocket 전송용)"""
    type: Literal["automation_status"] = "automation_status"
    is_running: bool
    current_step: int
    max_steps: int
    goal: str
    goal_status: dict                   # GoalStatus
    last_action: Optional[dict]         # 마지막 실행 액션
    finish_reason: Optional[str]
```

### 3.2 GPT-4o 프롬프트 수정

```python
# src/server/ui_tars_client.py 수정

GOAL_AUTOMATION_PROMPT = """You are a GUI automation agent. You analyze screenshots and determine the next action to achieve the user's goal.

## Output Format (JSON)
```json
{
  "screen_analysis": {
    "description": "현재 화면 상태 설명",
    "ready_for_action": true/false
  },
  "goal_status": {
    "achieved": true/false,
    "progress_description": "목표 진행 상황",
    "progress_percent": 0-100,
    "confidence": 0.0-1.0
  },
  "recommended_action": {
    "type": "click|type|scroll|wait|none",
    "params": {
      "x": 100, "y": 200,           // click, scroll
      "text": "input text",          // type
      "direction": "up|down"         // scroll
    },
    "reason": "이 액션을 선택한 이유"
  }
}
```

## Action Types
- click: 지정 좌표 클릭
- type: 텍스트 입력
- scroll: 스크롤 (up/down)
- wait: 대기 (로딩 중, 애니메이션 등)
- none: 액션 없음 (목표 달성 또는 불가능)

## Important Rules
1. 목표 달성 여부를 먼저 판단하세요
2. ready_for_action이 false면 wait를 추천하세요
3. 이전 액션 히스토리를 참고하여 반복 액션을 피하세요
4. 좌표는 스크린샷 이미지 기준 절대 픽셀 좌표입니다
5. 목표 달성이 불가능하다고 판단되면 none을 추천하세요

## Context
- Goal: {goal}
- Current Step: {step}/{max_steps}
- Screen Size: {width}x{height}
- Recent Actions: {action_history}
"""
```

### 3.3 Goal Automation Runner

```python
# src/server/goal_runner.py (신규 파일)

import asyncio
import logging
from datetime import datetime
from typing import Optional

from .config import settings
from .models import (
    AutomationContext, GoalStatus, ActionHistoryEntry,
    GoalAutomationStatus, ActionRequest
)
from .screen_controller import ScreenController
from .action_handler import ActionHandler
from .ui_tars_client import UITarsClient

logger = logging.getLogger(__name__)


class GoalAutomationRunner:
    """목표 기반 자동화 실행기"""

    def __init__(
        self,
        screen_controller: ScreenController,
        action_handler: ActionHandler,
        ui_tars_client: UITarsClient
    ):
        self.screen = screen_controller
        self.action = action_handler
        self.ai = ui_tars_client

        self.context: Optional[AutomationContext] = None
        self._stop_requested = False
        self._task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        return self.context is not None and self.context.is_running

    async def start(
        self,
        goal: str,
        max_steps: int,
        websocket,
        interval_seconds: float = 2.0
    ):
        """목표 자동화 시작"""
        if self.is_running:
            raise RuntimeError("Automation already running")

        # 컨텍스트 초기화
        self.context = AutomationContext(
            goal=goal,
            started_at=datetime.now(),
            current_step=0,
            max_steps=max_steps,
            action_history=[],
            goal_status=GoalStatus(
                achieved=False,
                progress_description="시작 대기 중",
                progress_percent=0,
                confidence=0.0
            ),
            is_running=True,
            finish_reason=None
        )

        self._stop_requested = False
        self._task = asyncio.create_task(
            self._run_loop(websocket, interval_seconds)
        )

    def stop(self):
        """자동화 중지 요청"""
        self._stop_requested = True

    async def _run_loop(self, websocket, interval_seconds: float):
        """메인 자동화 루프"""
        try:
            while not self._should_stop():
                self.context.current_step += 1

                # 상태 전송
                await self._send_status(websocket)

                # Phase 1: 화면 캡처
                frame = self.screen.capture_frame()
                if not frame:
                    logger.error("Failed to capture screen")
                    await asyncio.sleep(1)
                    continue

                # Phase 2: AI 분석
                result = await self.ai.analyze_for_goal(
                    screenshot_base64=frame.data,
                    goal=self.context.goal,
                    step=self.context.current_step,
                    max_steps=self.context.max_steps,
                    action_history=self._get_recent_history(5),
                    screen_width=self.screen.screen_width,
                    screen_height=self.screen.screen_height
                )

                if not result.get("success"):
                    logger.error(f"AI analysis failed: {result.get('error')}")
                    await asyncio.sleep(interval_seconds)
                    continue

                # 목표 상태 업데이트
                goal_status = result.get("goal_status", {})
                self.context.goal_status = GoalStatus(
                    achieved=goal_status.get("achieved", False),
                    progress_description=goal_status.get("progress_description", ""),
                    progress_percent=goal_status.get("progress_percent", 0),
                    confidence=goal_status.get("confidence", 0.0)
                )

                # 목표 달성 체크
                if self.context.goal_status.achieved:
                    self.context.finish_reason = "goal_achieved"
                    break

                # Phase 3: 안전 정책 검증 + 액션 결정
                action = self._decide_action(result)

                if action is None:
                    await asyncio.sleep(interval_seconds)
                    continue

                # Phase 4: 액션 실행
                if action["type"] != "wait" and action["type"] != "none":
                    action_request = ActionRequest(**action)
                    await self.action.process_action(action_request)

                # 히스토리 기록
                self._record_action(
                    action=action,
                    thought=result.get("thought", ""),
                    screen_desc=result.get("screen_analysis", {}).get("description", "")
                )

                # 대기
                await asyncio.sleep(interval_seconds)

            # 종료 처리
            if self._stop_requested:
                self.context.finish_reason = "user_stopped"
            elif self.context.current_step >= self.context.max_steps:
                self.context.finish_reason = "max_steps"

        except Exception as e:
            logger.error(f"Automation error: {e}", exc_info=True)
            self.context.finish_reason = "error"

        finally:
            self.context.is_running = False
            await self._send_status(websocket)

    def _should_stop(self) -> bool:
        """종료 조건 체크"""
        if self._stop_requested:
            return True
        if self.context.current_step >= self.context.max_steps:
            return True
        if self.context.goal_status.achieved:
            return True
        return False

    def _decide_action(self, ai_result: dict) -> Optional[dict]:
        """안전 정책 적용 및 최종 액션 결정"""
        recommended = ai_result.get("recommended_action")

        if not recommended:
            return None

        action_type = recommended.get("type")
        params = recommended.get("params", {})

        # 화면 준비 안됨 → 대기
        screen_analysis = ai_result.get("screen_analysis", {})
        if not screen_analysis.get("ready_for_action", True):
            return {"type": "wait", "action_type": "wait"}

        # 반복 클릭 방지
        if action_type == "click":
            if self._is_repeated_click(params.get("x"), params.get("y")):
                logger.warning("Repeated click detected, switching to wait")
                return {"type": "wait", "action_type": "wait"}

        # 액션 변환
        if action_type == "click":
            return {
                "type": "action",
                "action_type": "click",
                "x": params.get("x"),
                "y": params.get("y")
            }
        elif action_type == "type":
            return {
                "type": "action",
                "action_type": "type",
                "text": params.get("text", "")
            }
        elif action_type == "scroll":
            return {
                "type": "action",
                "action_type": "scroll",
                "x": params.get("x", self.screen.screen_width // 2),
                "y": params.get("y", self.screen.screen_height // 2),
                "direction": params.get("direction", "down")
            }

        return None

    def _is_repeated_click(self, x: int, y: int, tolerance: int = 30) -> bool:
        """반복 클릭 감지"""
        recent_clicks = [
            h for h in self.context.action_history[-3:]
            if h.action_type == "click"
        ]

        same_position_count = sum(
            1 for h in recent_clicks
            if abs(h.action_params.get("x", -1000) - x) < tolerance
            and abs(h.action_params.get("y", -1000) - y) < tolerance
        )

        return same_position_count >= 2

    def _record_action(self, action: dict, thought: str, screen_desc: str):
        """액션 히스토리 기록"""
        entry = ActionHistoryEntry(
            step=self.context.current_step,
            timestamp=datetime.now(),
            action_type=action.get("action_type", "unknown"),
            action_params=action,
            thought=thought,
            screen_description=screen_desc
        )
        self.context.action_history.append(entry)

    def _get_recent_history(self, n: int) -> str:
        """최근 N개 액션 히스토리 문자열"""
        recent = self.context.action_history[-n:]
        if not recent:
            return "None"

        lines = []
        for h in recent:
            lines.append(f"Step {h.step}: {h.action_type} - {h.thought}")
        return "\n".join(lines)

    async def _send_status(self, websocket):
        """현재 상태를 WebSocket으로 전송"""
        status = GoalAutomationStatus(
            is_running=self.context.is_running,
            current_step=self.context.current_step,
            max_steps=self.context.max_steps,
            goal=self.context.goal,
            goal_status={
                "achieved": self.context.goal_status.achieved,
                "progress_description": self.context.goal_status.progress_description,
                "progress_percent": self.context.goal_status.progress_percent,
                "confidence": self.context.goal_status.confidence
            },
            last_action=(
                self.context.action_history[-1].__dict__
                if self.context.action_history else None
            ),
            finish_reason=self.context.finish_reason
        )

        await websocket.send_json(status.model_dump())
```

### 3.4 WebSocket 핸들러 수정

```python
# src/server/main.py 에 추가

from .goal_runner import GoalAutomationRunner

# 전역 인스턴스
goal_runner = GoalAutomationRunner(
    screen_controller=screen_controller,
    action_handler=action_handler,
    ui_tars_client=ui_tars_client
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # ... 기존 코드 ...

    try:
        while True:
            data = await websocket.receive_json()

            # 기존 핸들러들 ...

            elif data.get("type") == "goal_automation":
                action = data.get("action")

                if action == "start":
                    goal = data.get("goal")
                    max_steps = data.get("max_steps", 50)

                    if not goal:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Goal is required"
                        })
                        continue

                    try:
                        await goal_runner.start(
                            goal=goal,
                            max_steps=max_steps,
                            websocket=websocket
                        )
                    except RuntimeError as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": str(e)
                        })

                elif action == "stop":
                    goal_runner.stop()
                    await websocket.send_json({
                        "type": "status",
                        "status": "stopping",
                        "message": "Automation stop requested"
                    })
```

### 3.5 프론트엔드 UI

```javascript
// static/js/goal-automation-handler.js (신규 파일)

class GoalAutomationHandler {
    constructor(wsClient) {
        this.wsClient = wsClient;
        this.isRunning = false;

        this.initUI();
        this.bindEvents();
    }

    initUI() {
        // UI 요소 참조
        this.goalInput = document.getElementById('goal-input');
        this.maxStepsInput = document.getElementById('max-steps-input');
        this.startBtn = document.getElementById('start-automation-btn');
        this.stopBtn = document.getElementById('stop-automation-btn');
        this.statusPanel = document.getElementById('automation-status');
        this.progressBar = document.getElementById('automation-progress');
        this.historyLog = document.getElementById('automation-history');
    }

    bindEvents() {
        this.startBtn?.addEventListener('click', () => this.start());
        this.stopBtn?.addEventListener('click', () => this.stop());
    }

    start() {
        const goal = this.goalInput.value.trim();
        if (!goal) {
            alert('목표를 입력하세요');
            return;
        }

        const maxSteps = parseInt(this.maxStepsInput.value) || 50;

        this.wsClient.send({
            type: 'goal_automation',
            action: 'start',
            goal: goal,
            max_steps: maxSteps
        });

        this.setRunningState(true);
    }

    stop() {
        this.wsClient.send({
            type: 'goal_automation',
            action: 'stop'
        });
    }

    handleStatus(data) {
        this.isRunning = data.is_running;
        this.setRunningState(data.is_running);

        // 진행률 업데이트
        const percent = data.goal_status?.progress_percent || 0;
        this.progressBar.style.width = `${percent}%`;
        this.progressBar.textContent = `${percent}%`;

        // 상태 텍스트
        this.statusPanel.innerHTML = `
            <div>Step: ${data.current_step}/${data.max_steps}</div>
            <div>상태: ${data.goal_status?.progress_description || '-'}</div>
            <div>목표: ${data.goal}</div>
        `;

        // 마지막 액션 로그
        if (data.last_action) {
            this.addHistoryEntry(data.last_action);
        }

        // 완료 처리
        if (data.finish_reason) {
            this.handleFinish(data.finish_reason, data.goal_status);
        }
    }

    addHistoryEntry(action) {
        const entry = document.createElement('div');
        entry.className = 'history-entry';
        entry.innerHTML = `
            <span class="step">Step ${action.step}</span>
            <span class="action">${action.action_type}</span>
            <span class="thought">${action.thought}</span>
        `;
        this.historyLog.appendChild(entry);
        this.historyLog.scrollTop = this.historyLog.scrollHeight;
    }

    handleFinish(reason, goalStatus) {
        let message = '';
        switch (reason) {
            case 'goal_achieved':
                message = '목표를 달성했습니다!';
                break;
            case 'max_steps':
                message = '최대 스텝에 도달했습니다.';
                break;
            case 'user_stopped':
                message = '사용자가 중지했습니다.';
                break;
            case 'error':
                message = '오류가 발생했습니다.';
                break;
        }

        alert(message);
        this.setRunningState(false);
    }

    setRunningState(running) {
        this.isRunning = running;
        this.startBtn.disabled = running;
        this.stopBtn.disabled = !running;
        this.goalInput.disabled = running;
        this.maxStepsInput.disabled = running;
    }
}
```

---

## 4. 안전 정책

### 4.1 반복 클릭 방지

| 정책 | 설명 |
|------|------|
| 동일 위치 제한 | 같은 좌표(±30px) 연속 3회 클릭 시 WAIT로 전환 |
| 화면 변화 감지 | 클릭 후 화면 변화 없으면 다른 액션 시도 |

### 4.2 속도 제한

| 정책 | 기본값 | 설명 |
|------|--------|------|
| 최소 간격 | 2초 | 액션 간 최소 대기 시간 |
| 분당 클릭 | 20회 | 분당 최대 클릭 횟수 |

### 4.3 종료 조건

| 조건 | 동작 |
|------|------|
| 목표 달성 | 즉시 종료, 성공 메시지 |
| 최대 스텝 도달 | 종료, 경고 메시지 |
| 사용자 중지 | 즉시 종료 |
| 연속 오류 5회 | 종료, 오류 메시지 |
| AI 신뢰도 < 0.3 연속 3회 | WAIT 후 재시도 |

---

## 5. 구현 순서

### Phase 1: 기본 구조 (1단계)
1. [ ] 데이터 타입 정의 (`models.py`)
2. [ ] GoalAutomationRunner 기본 구조
3. [ ] WebSocket 핸들러 확장

### Phase 2: AI 통합 (2단계)
4. [ ] GPT-4o 프롬프트 수정 (목표 + 히스토리 포함)
5. [ ] 응답 파싱 로직 수정 (goal_status 추출)
6. [ ] analyze_for_goal 메서드 구현

### Phase 3: 안전 정책 (3단계)
7. [ ] 반복 클릭 방지 로직
8. [ ] 속도 제한 로직
9. [ ] 종료 조건 체크 로직

### Phase 4: 프론트엔드 (4단계)
10. [ ] 목표 입력 UI
11. [ ] 진행 상태 표시 UI
12. [ ] 히스토리 로그 UI

### Phase 5: 테스트 (5단계)
13. [ ] Mock 모드 테스트
14. [ ] 실제 API 테스트
15. [ ] E2E 시나리오 테스트

---

## 6. 테스트 시나리오

### 6.1 기본 테스트
```
목표: "화면 중앙의 버튼을 클릭"
예상: 1-2 스텝 내 완료
```

### 6.2 다단계 테스트
```
목표: "설정 메뉴를 열고 다크모드 활성화"
예상: 3-5 스텝 내 완료
1. 설정 아이콘 클릭
2. 다크모드 토글 찾기
3. 토글 클릭
4. 완료 확인
```

### 6.3 반복 방지 테스트
```
목표: "존재하지 않는 버튼 클릭"
예상: 3회 시도 후 대기 상태로 전환
```

---

## 7. 향후 확장

### 7.1 체크포인트/재개
- 중단 시 상태 저장
- 재시작 시 이어서 실행

### 7.2 조건부 분기
- "만약 ~라면 A, 아니면 B" 형태의 복잡한 목표 지원

### 7.3 학습/최적화
- 성공한 액션 패턴 저장
- 유사 목표에 재활용
