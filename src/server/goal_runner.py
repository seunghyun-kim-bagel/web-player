"""
Web Player - Goal Automation Runner
목표 기반 자동화 실행기
"""
import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING

from .models import (
    GoalStatus, ActionHistoryEntry, GoalAutomationStatus, ActionRequest
)

if TYPE_CHECKING:
    from .screen_controller import ScreenController
    from .action_handler import ActionHandler
    from .ui_tars_client import UITarsClient

logger = logging.getLogger(__name__)


class GoalAutomationRunner:
    """목표 기반 자동화 실행기"""

    def __init__(
        self,
        screen_controller: "ScreenController",
        action_handler: "ActionHandler",
        ui_tars_client: "UITarsClient"
    ):
        self.screen = screen_controller
        self.action = action_handler
        self.ai = ui_tars_client

        # 실행 상태
        self.goal: str = ""
        self.current_step: int = 0
        self.max_steps: int = 50
        self.action_history: List[ActionHistoryEntry] = []
        self.goal_status: GoalStatus = GoalStatus()
        self.is_running: bool = False
        self.finish_reason: Optional[str] = None

        # 제어
        self._stop_requested: bool = False
        self._task: Optional[asyncio.Task] = None

    def _reset(self):
        """상태 초기화"""
        self.current_step = 0
        self.action_history = []
        self.goal_status = GoalStatus()
        self.finish_reason = None
        self._stop_requested = False

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

        self._reset()
        self.goal = goal
        self.max_steps = max_steps
        self.is_running = True

        logger.info(f"Goal automation started: {goal} (max_steps={max_steps})")

        self._task = asyncio.create_task(
            self._run_loop(websocket, interval_seconds)
        )

    def stop(self):
        """자동화 중지 요청"""
        logger.info("Goal automation stop requested")
        self._stop_requested = True

    async def _run_loop(self, websocket, interval_seconds: float):
        """메인 자동화 루프"""
        try:
            while not self._should_stop():
                self.current_step += 1
                logger.info(f"Step {self.current_step}/{self.max_steps}")

                # 상태 전송
                await self._send_status(websocket)

                # Phase 1: 화면 캡처
                frame = self.screen.capture_frame()
                if not frame:
                    logger.error("Failed to capture screen")
                    await asyncio.sleep(1)
                    continue

                # Phase 2: AI 분석 (목표 기반)
                result = await self.ai.analyze_for_goal(
                    screenshot_base64=frame.data,
                    goal=self.goal,
                    step=self.current_step,
                    max_steps=self.max_steps,
                    action_history=self._format_history(5),
                    screen_width=self.screen.screen_width,
                    screen_height=self.screen.screen_height
                )

                if not result.get("success"):
                    logger.error(f"AI analysis failed: {result.get('error')}")
                    await asyncio.sleep(interval_seconds)
                    continue

                # 목표 상태 업데이트
                goal_data = result.get("goal_status", {})
                self.goal_status = GoalStatus(
                    achieved=goal_data.get("achieved", False),
                    progress_description=goal_data.get("progress_description", ""),
                    progress_percent=goal_data.get("progress_percent", 0),
                    confidence=goal_data.get("confidence", 0.0)
                )

                logger.info(f"Goal status: {self.goal_status.progress_description} ({self.goal_status.progress_percent}%)")

                # 목표 달성 체크
                if self.goal_status.achieved and self.goal_status.confidence >= 0.7:
                    logger.info("Goal achieved!")
                    self.finish_reason = "goal_achieved"
                    break

                # Phase 3: 안전 정책 + 액션 결정
                action = self._decide_action(result)

                if action is None:
                    logger.info("No action to execute, waiting...")
                    await asyncio.sleep(interval_seconds)
                    continue

                # Phase 4: 액션 실행
                action_type = action.get("action_type", "unknown")
                if action_type not in ("wait", "none"):
                    try:
                        action_request = ActionRequest(**action)
                        await self.action.process_action(action_request)
                        logger.info(f"Action executed: {action_type}")
                    except Exception as e:
                        logger.error(f"Action execution error: {e}")

                # 히스토리 기록
                self._record_action(
                    action=action,
                    thought=result.get("thought", ""),
                    screen_desc=result.get("screen_analysis", {}).get("description", "")
                )

                # 상태 전송
                await self._send_status(websocket)

                # 대기
                await asyncio.sleep(interval_seconds)

            # 종료 처리
            if self._stop_requested:
                self.finish_reason = "user_stopped"
            elif self.current_step >= self.max_steps:
                self.finish_reason = "max_steps"

            logger.info(f"Goal automation finished: {self.finish_reason}")

        except Exception as e:
            logger.error(f"Automation error: {e}", exc_info=True)
            self.finish_reason = "error"

        finally:
            self.is_running = False
            await self._send_status(websocket)

    def _should_stop(self) -> bool:
        """종료 조건 체크"""
        if self._stop_requested:
            return True
        if self.current_step >= self.max_steps:
            return True
        if self.goal_status.achieved and self.goal_status.confidence >= 0.7:
            return True
        return False

    def _decide_action(self, ai_result: dict) -> Optional[dict]:
        """안전 정책 적용 및 최종 액션 결정"""
        recommended = ai_result.get("recommended_action")

        if not recommended:
            return None

        action_type = recommended.get("type", "none")
        params = recommended.get("params", {})

        # 화면 준비 안됨 → 대기
        screen_analysis = ai_result.get("screen_analysis", {})
        if not screen_analysis.get("ready_for_action", True):
            logger.info("Screen not ready, waiting...")
            return None

        # 반복 클릭 방지
        if action_type == "click":
            x, y = params.get("x"), params.get("y")
            if x is not None and y is not None:
                if self._is_repeated_click(x, y):
                    logger.warning("Repeated click detected, skipping")
                    return None

        # 액션 변환
        if action_type == "click":
            return {
                "type": "action",
                "action_type": "click",
                "x": params.get("x"),
                "y": params.get("y")
            }
        elif action_type == "double_click":
            return {
                "type": "action",
                "action_type": "double_click",
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
        elif action_type == "hotkey":
            return {
                "type": "action",
                "action_type": "hotkey",
                "key": params.get("key", "")
            }

        return None

    def _is_repeated_click(self, x: int, y: int, tolerance: int = 30) -> bool:
        """반복 클릭 감지 (같은 위치 연속 3회)"""
        recent_clicks = [
            h for h in self.action_history[-3:]
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
            step=self.current_step,
            timestamp=time.time(),
            action_type=action.get("action_type", "unknown"),
            action_params=action,
            thought=thought,
            screen_description=screen_desc
        )
        self.action_history.append(entry)

    def _format_history(self, n: int) -> str:
        """최근 N개 액션 히스토리 문자열"""
        recent = self.action_history[-n:]
        if not recent:
            return "None"

        lines = []
        for h in recent:
            lines.append(f"Step {h.step}: {h.action_type} - {h.thought}")
        return "\n".join(lines)

    async def _send_status(self, websocket):
        """현재 상태를 WebSocket으로 전송"""
        try:
            status = GoalAutomationStatus(
                is_running=self.is_running,
                current_step=self.current_step,
                max_steps=self.max_steps,
                goal=self.goal,
                goal_status=self.goal_status,
                last_action=(
                    self.action_history[-1]
                    if self.action_history else None
                ),
                finish_reason=self.finish_reason
            )
            await websocket.send_json(status.model_dump())
        except Exception as e:
            logger.error(f"Failed to send status: {e}")

    def get_status(self) -> GoalAutomationStatus:
        """현재 상태 반환"""
        return GoalAutomationStatus(
            is_running=self.is_running,
            current_step=self.current_step,
            max_steps=self.max_steps,
            goal=self.goal,
            goal_status=self.goal_status,
            last_action=(
                self.action_history[-1]
                if self.action_history else None
            ),
            finish_reason=self.finish_reason
        )
