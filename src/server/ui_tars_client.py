"""
Web Player - UI-TARS 클라이언트
OpenAI Vision API를 사용하여 화면 분석 및 액션 생성
"""
import base64
import logging
import re
from typing import Optional, List, Dict, Any
from io import BytesIO

from openai import OpenAI
from PIL import Image

from .config import settings

logger = logging.getLogger(__name__)

# UI-TARS 시스템 프롬프트 (단일 명령용)
UITARS_SYSTEM_PROMPT = """You are a GUI agent. You are given a task and a screenshot. You need to perform the next action to complete the task.

## Output Format
```
Thought: ...
Action: ...
```

## Action Space

click(start_box='(x,y)')
left_double(start_box='(x,y)')
right_single(start_box='(x,y)')
drag(start_box='(x1,y1)', end_box='(x2,y2)')
hotkey(key='ctrl c')
type(content='xxx')
scroll(start_box='(x,y)', direction='down')
hover(start_box='(x,y)')
finished(content='xxx')

## Coordinate System
- Coordinates are absolute pixel positions on the screen
- Format: (x, y) where x is horizontal, y is vertical
- Origin (0,0) is top-left corner

## Note
- Use Korean in `Thought` part.
- Write a small plan and finally summarize your next action in `Thought` part.
- For click actions, specify the exact pixel coordinates.
- If the task is completed, use finished() action.
"""


# 목표 기반 자동화 프롬프트
GOAL_AUTOMATION_PROMPT = """You are a GUI automation agent. You analyze screenshots and determine the next action to achieve the user's goal.

## Your Task
1. Analyze the current screen state
2. Determine if the goal has been achieved
3. If not achieved, recommend the next action to progress toward the goal
4. Consider the action history to avoid repetitive or stuck behaviors

## Output Format (JSON only, no markdown code blocks)
{
  "screen_analysis": {
    "description": "Current screen state description in Korean",
    "ready_for_action": true
  },
  "goal_status": {
    "achieved": false,
    "progress_description": "Progress toward goal in Korean",
    "progress_percent": 0,
    "confidence": 0.8
  },
  "recommended_action": {
    "type": "click",
    "params": {
      "x": 100,
      "y": 200
    },
    "reason": "Reason for this action in Korean"
  },
  "thought": "Your reasoning process in Korean"
}

## Action Types
- click: Click at coordinates {"x": int, "y": int}
- double_click: Double click {"x": int, "y": int}
- type: Type text {"text": "string"}
- scroll: Scroll {"x": int, "y": int, "direction": "up"|"down"}
- hotkey: Keyboard shortcut {"key": "ctrl c"}
- wait: Wait for screen to stabilize {}
- none: No action needed (goal achieved or impossible) {}

## Important Rules
1. Coordinates are absolute pixel positions on the screenshot
2. Always check if the goal is achieved FIRST
3. If screen shows loading/animation, set ready_for_action to false
4. Consider action history to avoid clicking the same spot repeatedly
5. Set confidence (0.0-1.0) based on how certain you are
6. Use Korean for all descriptions and reasoning
7. Return ONLY valid JSON, no markdown formatting
"""


class UITarsClient:
    """UI-TARS 모델 클라이언트"""

    def __init__(self, api_key: Optional[str] = None, model: str = None, mock_mode: bool = None):
        """
        Args:
            api_key: OpenAI API 키 (없으면 환경변수에서 로드)
            model: 사용할 모델 (기본값: gpt-4o)
            mock_mode: Mock 모드 활성화 (테스트용)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.uitars_model
        self.mock_mode = mock_mode if mock_mode is not None else settings.uitars_mock_mode
        self.client = None

        if self.mock_mode:
            logger.info("UITarsClient initialized in MOCK mode (for testing)")
        elif self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"UITarsClient initialized with model: {self.model}")
        else:
            logger.warning("OpenAI API key not configured. UI-TARS features disabled.")

    def is_available(self) -> bool:
        """UI-TARS 기능 사용 가능 여부"""
        return self.client is not None or self.mock_mode

    async def analyze_and_act(
        self,
        screenshot_base64: str,
        instruction: str,
        screen_width: int,
        screen_height: int
    ) -> Dict[str, Any]:
        """
        화면 분석 및 액션 생성

        Args:
            screenshot_base64: Base64 인코딩된 스크린샷
            instruction: 사용자 명령
            screen_width: 화면 너비
            screen_height: 화면 높이

        Returns:
            {
                "success": bool,
                "thought": str,
                "action_type": str,
                "action_params": dict,
                "raw_response": str
            }
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "OpenAI API key not configured",
                "thought": None,
                "action_type": None,
                "action_params": {}
            }

        # Mock 모드: 테스트용 가짜 응답 생성
        if self.mock_mode:
            return self._generate_mock_response(instruction, screen_width, screen_height)

        try:
            # OpenAI Vision API 호출
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": UITARS_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Screen size: {screen_width}x{screen_height}\n\nUser Instruction: {instruction}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{screenshot_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1024,
                temperature=0.1
            )

            raw_response = response.choices[0].message.content
            logger.info(f"UI-TARS raw response: {raw_response}")

            # 응답 파싱
            parsed = self._parse_response(raw_response, screen_width, screen_height)
            parsed["raw_response"] = raw_response
            parsed["success"] = True

            return parsed

        except Exception as e:
            logger.error(f"UI-TARS API error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "thought": None,
                "action_type": None,
                "action_params": {}
            }

    def _generate_mock_response(
        self,
        instruction: str,
        screen_width: int,
        screen_height: int
    ) -> Dict[str, Any]:
        """
        Mock 모드용 가짜 응답 생성 (테스트용)

        자연어 명령을 분석하여 적절한 액션을 생성합니다.
        """
        import re

        instruction_lower = instruction.lower()

        # 기본 응답
        result = {
            "success": True,
            "thought": f"[MOCK] 명령을 분석했습니다: {instruction}",
            "action_type": None,
            "action_params": {},
            "raw_response": f"[MOCK MODE] Instruction: {instruction}"
        }

        # 클릭 관련 명령 분석
        if "클릭" in instruction_lower or "click" in instruction_lower:
            # 좌표 추출 시도
            coord_match = re.search(r'\(?\s*(\d+)\s*,\s*(\d+)\s*\)?', instruction)

            if coord_match:
                x, y = int(coord_match.group(1)), int(coord_match.group(2))
            elif "중앙" in instruction_lower or "center" in instruction_lower:
                x, y = screen_width // 2, screen_height // 2
            elif "왼쪽" in instruction_lower or "left" in instruction_lower:
                x, y = screen_width // 4, screen_height // 2
            elif "오른쪽" in instruction_lower or "right" in instruction_lower:
                x, y = (screen_width * 3) // 4, screen_height // 2
            elif "위" in instruction_lower or "top" in instruction_lower:
                x, y = screen_width // 2, screen_height // 4
            elif "아래" in instruction_lower or "bottom" in instruction_lower:
                x, y = screen_width // 2, (screen_height * 3) // 4
            else:
                x, y = screen_width // 2, screen_height // 2

            if "더블" in instruction_lower or "double" in instruction_lower:
                result["action_type"] = "left_double"
            elif "우클릭" in instruction_lower or "right" in instruction_lower and "click" in instruction_lower:
                result["action_type"] = "right_single"
            else:
                result["action_type"] = "click"

            result["action_params"] = {"start_box": {"x": x, "y": y}}
            result["thought"] = f"[MOCK] 화면의 ({x}, {y}) 위치를 클릭합니다."

        # 스크롤 명령 분석
        elif "스크롤" in instruction_lower or "scroll" in instruction_lower:
            direction = "down"
            if "위" in instruction_lower or "up" in instruction_lower:
                direction = "up"

            result["action_type"] = "scroll"
            result["action_params"] = {
                "start_box": {"x": screen_width // 2, "y": screen_height // 2},
                "direction": direction
            }
            result["thought"] = f"[MOCK] 화면을 {direction} 방향으로 스크롤합니다."

        # 타이핑 명령 분석
        elif "입력" in instruction_lower or "타이핑" in instruction_lower or "type" in instruction_lower:
            # 따옴표 안의 텍스트 추출
            text_match = re.search(r'["\']([^"\']+)["\']', instruction)
            if text_match:
                text = text_match.group(1)
            else:
                text = "Hello World"

            result["action_type"] = "type"
            result["action_params"] = {"content": text}
            result["thought"] = f"[MOCK] '{text}'를 입력합니다."

        # 단축키 명령 분석
        elif "단축키" in instruction_lower or "hotkey" in instruction_lower or "ctrl" in instruction_lower or "cmd" in instruction_lower:
            key_match = re.search(r'(ctrl|cmd|alt|shift)[\s+]+(\w+)', instruction_lower)
            if key_match:
                key = f"{key_match.group(1)} {key_match.group(2)}"
            else:
                key = "ctrl c"

            result["action_type"] = "hotkey"
            result["action_params"] = {"key": key}
            result["thought"] = f"[MOCK] 단축키 {key}를 실행합니다."

        # 기본: 화면 중앙 클릭
        else:
            x, y = screen_width // 2, screen_height // 2
            result["action_type"] = "click"
            result["action_params"] = {"start_box": {"x": x, "y": y}}
            result["thought"] = f"[MOCK] 명령을 이해하지 못해 화면 중앙 ({x}, {y})을 클릭합니다."

        logger.info(f"[MOCK] Generated response: {result['action_type']} - {result['action_params']}")
        return result

    def _parse_response(
        self,
        response: str,
        screen_width: int,
        screen_height: int
    ) -> Dict[str, Any]:
        """
        UI-TARS 응답 파싱

        Args:
            response: 모델 응답 텍스트
            screen_width: 화면 너비
            screen_height: 화면 높이

        Returns:
            파싱된 액션 정보
        """
        result = {
            "thought": None,
            "action_type": None,
            "action_params": {}
        }

        # Thought 추출
        thought_match = re.search(r"Thought:\s*(.+?)(?=Action:|$)", response, re.DOTALL)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()

        # Action 추출
        action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", response, re.DOTALL)
        if not action_match:
            logger.warning("No action found in response")
            return result

        action_str = action_match.group(1).strip()

        # 액션 타입과 파라미터 파싱
        func_match = re.match(r"(\w+)\((.*)\)", action_str, re.DOTALL)
        if not func_match:
            logger.warning(f"Failed to parse action: {action_str}")
            return result

        result["action_type"] = func_match.group(1)
        params_str = func_match.group(2)

        # 파라미터 파싱
        params = {}

        # start_box, end_box 좌표 파싱
        box_pattern = r"(start_box|end_box)=['\"]?\((\d+),\s*(\d+)\)['\"]?"
        for match in re.finditer(box_pattern, params_str):
            box_name = match.group(1)
            x = int(match.group(2))
            y = int(match.group(3))
            params[box_name] = {"x": x, "y": y}

        # key 파라미터 파싱
        key_match = re.search(r"key=['\"]([^'\"]+)['\"]", params_str)
        if key_match:
            params["key"] = key_match.group(1)

        # content 파라미터 파싱
        content_match = re.search(r"content=['\"]([^'\"]*)['\"]", params_str)
        if content_match:
            params["content"] = content_match.group(1)

        # direction 파라미터 파싱
        direction_match = re.search(r"direction=['\"]([^'\"]+)['\"]", params_str)
        if direction_match:
            params["direction"] = direction_match.group(1)

        result["action_params"] = params

        logger.info(f"Parsed action: {result['action_type']} with params: {params}")

        return result

    def convert_to_action_request(self, parsed_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        파싱된 응답을 ActionRequest 형식으로 변환

        Args:
            parsed_response: _parse_response()의 결과

        Returns:
            ActionRequest 호환 딕셔너리
        """
        action_type = parsed_response.get("action_type")
        params = parsed_response.get("action_params", {})

        if not action_type:
            return None

        # 액션 타입 매핑
        action_map = {
            "click": "click",
            "left_double": "double_click",
            "right_single": "right_click",
            "drag": "drag",
            "hotkey": "hotkey",
            "type": "type",
            "scroll": "scroll",
            "hover": "hover",
            "finished": "finished"
        }

        mapped_action = action_map.get(action_type, action_type)

        result = {
            "type": "action",
            "action_type": mapped_action
        }

        # 좌표 변환
        if "start_box" in params:
            result["x"] = params["start_box"]["x"]
            result["y"] = params["start_box"]["y"]

        if "end_box" in params:
            result["start_x"] = params.get("start_box", {}).get("x")
            result["start_y"] = params.get("start_box", {}).get("y")
            result["end_x"] = params["end_box"]["x"]
            result["end_y"] = params["end_box"]["y"]

        # 기타 파라미터
        if "key" in params:
            result["key"] = params["key"]

        if "content" in params:
            result["text"] = params["content"]

        if "direction" in params:
            result["direction"] = params["direction"]

        return result

    async def analyze_for_goal(
        self,
        screenshot_base64: str,
        goal: str,
        step: int,
        max_steps: int,
        action_history: str,
        screen_width: int,
        screen_height: int
    ) -> Dict[str, Any]:
        """
        목표 기반 화면 분석

        Args:
            screenshot_base64: Base64 인코딩된 스크린샷
            goal: 달성할 목표
            step: 현재 스텝
            max_steps: 최대 스텝
            action_history: 이전 액션 히스토리 문자열
            screen_width: 화면 너비
            screen_height: 화면 높이

        Returns:
            {
                "success": bool,
                "screen_analysis": dict,
                "goal_status": dict,
                "recommended_action": dict,
                "thought": str,
                "error": str (optional)
            }
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "OpenAI API key not configured"
            }

        # Mock 모드
        if self.mock_mode:
            return self._generate_mock_goal_response(
                goal, step, max_steps, screen_width, screen_height
            )

        try:
            user_message = f"""## Context
- Goal: {goal}
- Current Step: {step}/{max_steps}
- Screen Size: {screen_width}x{screen_height}

## Recent Action History
{action_history}

Analyze the screenshot and provide the next action to achieve the goal."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": GOAL_AUTOMATION_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_message
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{screenshot_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2048,
                temperature=0.1
            )

            raw_response = response.choices[0].message.content
            logger.info(f"Goal analysis raw response: {raw_response[:500]}...")

            # JSON 파싱
            parsed = self._parse_goal_response(raw_response)
            parsed["success"] = True
            parsed["raw_response"] = raw_response

            return parsed

        except Exception as e:
            logger.error(f"Goal analysis error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _parse_goal_response(self, response: str) -> Dict[str, Any]:
        """목표 기반 응답 JSON 파싱"""
        import json

        result = {
            "screen_analysis": {"description": "", "ready_for_action": True},
            "goal_status": {
                "achieved": False,
                "progress_description": "",
                "progress_percent": 0,
                "confidence": 0.0
            },
            "recommended_action": None,
            "thought": ""
        }

        try:
            # JSON 블록 추출 시도
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)

                result["screen_analysis"] = parsed.get("screen_analysis", result["screen_analysis"])
                result["goal_status"] = parsed.get("goal_status", result["goal_status"])
                result["recommended_action"] = parsed.get("recommended_action")
                result["thought"] = parsed.get("thought", "")

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # 파싱 실패시 기본값 유지

        return result

    def _generate_mock_goal_response(
        self,
        goal: str,
        step: int,
        max_steps: int,
        screen_width: int,
        screen_height: int
    ) -> Dict[str, Any]:
        """Mock 모드용 목표 기반 응답 생성"""
        goal_lower = goal.lower()

        # 목표 달성 시뮬레이션 (5스텝 이상이면 달성)
        achieved = step >= 5
        progress = min(step * 20, 100)

        # 기본 클릭 위치
        x = screen_width // 2 + (step * 50) % (screen_width // 2)
        y = screen_height // 2 + (step * 30) % (screen_height // 2)

        return {
            "success": True,
            "screen_analysis": {
                "description": f"[MOCK] Step {step}: 화면 분석 중...",
                "ready_for_action": True
            },
            "goal_status": {
                "achieved": achieved,
                "progress_description": f"[MOCK] 목표 '{goal}' 진행 중 ({progress}%)",
                "progress_percent": progress,
                "confidence": 0.8 if achieved else 0.6
            },
            "recommended_action": None if achieved else {
                "type": "click",
                "params": {"x": x, "y": y},
                "reason": f"[MOCK] Step {step}: 다음 위치 클릭"
            },
            "thought": f"[MOCK] Step {step}/{max_steps}: 목표 '{goal}' 향해 진행 중",
            "raw_response": "[MOCK MODE]"
        }


# 전역 인스턴스
ui_tars_client = UITarsClient()
