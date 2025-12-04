"""
Web Player - Pydantic 데이터 모델
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


class ConfigRequest(BaseModel):
    """설정 변경 요청"""
    type: Literal["config"] = "config"
    setting: str
    value: int
