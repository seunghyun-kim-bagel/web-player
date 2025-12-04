"""
Web Player - 액션 처리
"""
import logging
from typing import Optional

import pyautogui

from .models import ActionRequest, ActionResponse

logger = logging.getLogger(__name__)

# PyAutoGUI 안전 설정
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class ActionHandler:
    """액션 처리 핸들러"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        logger.info(f"ActionHandler initialized: {screen_width}x{screen_height}")

    async def process_action(self, action: ActionRequest) -> ActionResponse:
        """액션 처리"""
        try:
            self._validate_action(action)
            action_type = action.action_type

            if action_type == "click":
                self._handle_click(action.x, action.y)
            elif action_type == "double_click":
                self._handle_double_click(action.x, action.y)
            elif action_type == "right_click":
                self._handle_right_click(action.x, action.y)
            elif action_type == "drag":
                self._handle_drag(action.start_x, action.start_y, action.end_x, action.end_y)
            elif action_type == "type":
                self._handle_type(action.text)
            elif action_type == "hotkey":
                self._handle_hotkey(action.key)
            elif action_type == "scroll":
                self._handle_scroll(action.x, action.y, action.direction)
            elif action_type == "hover":
                self._handle_hover(action.x, action.y)
            else:
                raise ValueError(f"Unknown action type: {action_type}")

            logger.info(f"Action executed: {action_type}")
            return ActionResponse(status="success")

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return ActionResponse(status="error", code="INVALID_INPUT", message=str(e))
        except Exception as e:
            logger.error(f"Action processing error: {e}", exc_info=True)
            return ActionResponse(status="error", code="EXECUTION_ERROR", message=str(e))

    def _validate_action(self, action: ActionRequest):
        """액션 검증"""
        if action.x is not None:
            if not (0 <= action.x <= self.screen_width):
                raise ValueError(f"X coordinate {action.x} out of bounds (0-{self.screen_width})")
        if action.y is not None:
            if not (0 <= action.y <= self.screen_height):
                raise ValueError(f"Y coordinate {action.y} out of bounds (0-{self.screen_height})")
        if action.action_type == "drag":
            for coord, name in [(action.start_x, "start_x"), (action.start_y, "start_y"),
                               (action.end_x, "end_x"), (action.end_y, "end_y")]:
                if coord is None:
                    raise ValueError(f"Drag action requires {name}")
        if action.action_type == "type" and not action.text:
            raise ValueError("Type action requires text")
        if action.action_type == "hotkey" and not action.key:
            raise ValueError("Hotkey action requires key")

    def _handle_click(self, x: int, y: int):
        pyautogui.click(x, y, button='left')
        logger.debug(f"Click at ({x}, {y})")

    def _handle_double_click(self, x: int, y: int):
        pyautogui.doubleClick(x, y, button='left')
        logger.debug(f"Double click at ({x}, {y})")

    def _handle_right_click(self, x: int, y: int):
        pyautogui.click(x, y, button='right')
        logger.debug(f"Right click at ({x}, {y})")

    def _handle_drag(self, start_x: int, start_y: int, end_x: int, end_y: int):
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=0.5)
        logger.debug(f"Drag from ({start_x}, {start_y}) to ({end_x}, {end_y})")

    def _handle_type(self, text: str):
        try:
            import pyperclip
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
        except ImportError:
            pyautogui.write(text, interval=0.05)
        logger.debug(f"Typed: {text[:50]}...")

    def _handle_hotkey(self, key: str):
        keys = key.lower().split()
        key_map = {
            'ctrl': 'ctrl', 'control': 'ctrl', 'cmd': 'command', 'command': 'command',
            'alt': 'alt', 'option': 'alt', 'shift': 'shift', 'enter': 'enter',
            'return': 'enter', 'tab': 'tab', 'escape': 'escape', 'esc': 'escape',
            'space': 'space', 'backspace': 'backspace', 'delete': 'delete',
            'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right',
            'arrowup': 'up', 'arrowdown': 'down', 'arrowleft': 'left', 'arrowright': 'right',
        }
        converted_keys = [key_map.get(k, k) for k in keys]
        if len(converted_keys) == 1:
            pyautogui.press(converted_keys[0])
        else:
            pyautogui.hotkey(*converted_keys)
        logger.debug(f"Hotkey: {converted_keys}")

    def _handle_scroll(self, x: Optional[int], y: Optional[int], direction: Optional[str]):
        direction = direction or "down"
        clicks = 5 if direction == "up" else -5
        if x is not None and y is not None:
            pyautogui.scroll(clicks, x=x, y=y)
        else:
            pyautogui.scroll(clicks)
        logger.debug(f"Scroll {direction}")

    def _handle_hover(self, x: int, y: int):
        pyautogui.moveTo(x, y)
        logger.debug(f"Hover at ({x}, {y})")
