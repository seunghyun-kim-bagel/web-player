"""
Web Player - FastAPI Application
"""
import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .models import ActionRequest, AICommandRequest, AICommandResponse, GoalAutomationRequest
from .screen_controller import ScreenController
from .action_handler import ActionHandler
from .ui_tars_client import UITarsClient
from .goal_runner import GoalAutomationRunner

# Logging setup
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Web Player",
    description="UI-TARS Remote Desktop Control System",
    version="1.0.0"
)

# Static files
static_path = Path(__file__).parent.parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Controllers
screen_controller = ScreenController()
action_handler = ActionHandler(
    screen_width=screen_controller.screen_width,
    screen_height=screen_controller.screen_height
)
ui_tars_client = UITarsClient()
goal_runner = GoalAutomationRunner(
    screen_controller=screen_controller,
    action_handler=action_handler,
    ui_tars_client=ui_tars_client
)


@app.get("/")
async def root():
    html_path = static_path / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Web Player</h1><p>Please create static/index.html</p>")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "web-player",
        "version": "1.0.0",
        "screen": {
            "width": screen_controller.screen_width,
            "height": screen_controller.screen_height
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = id(websocket)
    logger.info(f"Client connected: {client_id}")

    await websocket.send_json({
        "type": "status",
        "status": "connected",
        "message": "Connection established"
    })

    streaming_task = asyncio.create_task(
        screen_controller.start_streaming(websocket)
    )

    try:
        while True:
            data = await websocket.receive_json()
            logger.debug(f"Received: {data}")

            if data.get("type") == "action":
                try:
                    action = ActionRequest(**data)
                    result = await action_handler.process_action(action)
                    await websocket.send_json(result.model_dump())
                except Exception as e:
                    logger.error(f"Action error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "code": "ACTION_ERROR"
                    })

            elif data.get("type") == "ai_command":
                # AI 명령 처리
                try:
                    instruction = data.get("instruction", "")
                    logger.info(f"AI command received: {instruction}")

                    if not ui_tars_client.is_available():
                        await websocket.send_json(
                            AICommandResponse(
                                success=False,
                                error="OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
                            ).model_dump()
                        )
                        continue

                    # 현재 화면 캡처
                    frame = screen_controller.capture_frame()
                    if not frame:
                        await websocket.send_json(
                            AICommandResponse(
                                success=False,
                                error="Failed to capture screen"
                            ).model_dump()
                        )
                        continue

                    # UI-TARS 분석
                    result = await ui_tars_client.analyze_and_act(
                        screenshot_base64=frame.data,
                        instruction=instruction,
                        screen_width=screen_controller.screen_width,
                        screen_height=screen_controller.screen_height
                    )

                    if result.get("success") and result.get("action_type"):
                        # 액션 변환 및 실행
                        action_request = ui_tars_client.convert_to_action_request(result)

                        if action_request and result.get("action_type") != "finished":
                            # 실제 액션 실행
                            action = ActionRequest(**action_request)
                            action_result = await action_handler.process_action(action)
                            logger.info(f"Action executed: {action_result}")

                    # 응답 전송
                    await websocket.send_json(
                        AICommandResponse(
                            success=result.get("success", False),
                            thought=result.get("thought"),
                            action_type=result.get("action_type"),
                            action_params=result.get("action_params"),
                            error=result.get("error")
                        ).model_dump()
                    )

                except Exception as e:
                    logger.error(f"AI command error: {e}", exc_info=True)
                    await websocket.send_json(
                        AICommandResponse(
                            success=False,
                            error=str(e)
                        ).model_dump()
                    )

            elif data.get("type") == "config":
                setting = data.get("setting")
                value = data.get("value")
                if setting == "quality":
                    screen_controller.quality = max(10, min(100, value))
                elif setting == "fps":
                    screen_controller.fps = max(1, min(60, value))
                await websocket.send_json({
                    "type": "status",
                    "status": "config_updated",
                    "message": f"{setting} set to {value}"
                })

            elif data.get("type") == "goal_automation":
                # 목표 기반 자동화
                try:
                    action = data.get("action")
                    logger.info(f"Goal automation action: {action}")

                    if action == "start":
                        goal = data.get("goal")
                        max_steps = data.get("max_steps", 50)

                        if not goal:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Goal is required",
                                "code": "MISSING_GOAL"
                            })
                            continue

                        if not ui_tars_client.is_available():
                            await websocket.send_json({
                                "type": "error",
                                "message": "OpenAI API key not configured",
                                "code": "API_NOT_CONFIGURED"
                            })
                            continue

                        await goal_runner.start(
                            goal=goal,
                            max_steps=max_steps,
                            websocket=websocket
                        )

                    elif action == "stop":
                        goal_runner.stop()
                        await websocket.send_json({
                            "type": "status",
                            "status": "stopping",
                            "message": "Goal automation stop requested"
                        })

                    elif action == "status":
                        status = goal_runner.get_status()
                        await websocket.send_json(status.model_dump())

                except RuntimeError as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "code": "AUTOMATION_ERROR"
                    })
                except Exception as e:
                    logger.error(f"Goal automation error: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "code": "AUTOMATION_ERROR"
                    })

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # Stop goal automation if running
        if goal_runner.is_running:
            goal_runner.stop()
        screen_controller.stop_streaming()
        streaming_task.cancel()
        try:
            await streaming_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.server.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
