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
from .models import ActionRequest
from .screen_controller import ScreenController
from .action_handler import ActionHandler

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

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
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
