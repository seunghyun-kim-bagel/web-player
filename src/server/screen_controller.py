"""
Web Player - 화면 캡처 및 스트리밍 컨트롤러
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
        self._lock = asyncio.Lock()

        logger.info(
            f"ScreenController initialized: "
            f"{self.screen_width}x{self.screen_height} @ {self.fps} FPS, "
            f"quality: {self.quality}%"
        )

    async def start_streaming(self, websocket: WebSocket):
        """
        화면 스트리밍 시작

        Args:
            websocket: 연결된 WebSocket 클라이언트
        """
        async with self._lock:
            if self.is_streaming:
                logger.warning("Streaming already in progress")
                return

            self.is_streaming = True

        logger.info("Screen streaming started")
        self.frame_count = 0
        start_time = time.time()

        try:
            while self.is_streaming:
                loop_start = time.time()
                interval = 1.0 / self.fps

                # 화면 캡처
                frame = self.capture_frame()

                if frame:
                    try:
                        # 프레임 전송
                        await websocket.send_json(frame.model_dump())
                        self.frame_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send frame: {e}")
                        break

                # FPS 유지를 위한 대기
                elapsed = time.time() - loop_start
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            logger.info("Streaming cancelled")
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
        finally:
            async with self._lock:
                self.is_streaming = False

            elapsed_total = time.time() - start_time
            actual_fps = self.frame_count / elapsed_total if elapsed_total > 0 else 0
            logger.info(
                f"Screen streaming stopped. "
                f"Total frames: {self.frame_count}, "
                f"Duration: {elapsed_total:.1f}s, "
                f"Actual FPS: {actual_fps:.1f}"
            )

    def capture_frame(self) -> Optional[ScreenFrame]:
        """
        단일 프레임 캡처

        Returns:
            ScreenFrame 또는 None (실패 시)
        """
        try:
            with mss.mss() as sct:
                # 주 모니터 캡처 (monitors[1]이 주 모니터)
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
                    quality=self.quality,
                    optimize=True
                )
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

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

    def get_screen_info(self) -> dict:
        """화면 정보 반환"""
        return {
            "width": self.screen_width,
            "height": self.screen_height,
            "fps": self.fps,
            "quality": self.quality,
            "is_streaming": self.is_streaming,
            "frame_count": self.frame_count
        }
