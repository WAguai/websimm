from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class GameFiles(BaseModel):
    html: str  # 包含所有代码的完整HTML文件


class GameLogicResult(BaseModel):
    title: str
    description: str
    game_logic: str
    game_type: str


class GameFileResult(BaseModel):
    files: GameFiles


class ImageResourceResult(BaseModel):
    image_resources: List[str]
    reasoning: str


class AudioResourceResult(BaseModel):
    audio_resources: List[str]
    reasoning: str


class GameGenerationResult(BaseModel):
    files: GameFiles
    title: str
    description: str
    game_type: str
    game_logic: str
    image_resources: List[str]
    audio_resources: List[str]
    session_id: Optional[str] = None
    record_id: Optional[str] = None


# API请求模型
class GameGenerationRequest(BaseModel):
    prompt: str
    context: Optional[List[dict]] = []


# API响应模型
class GameGenerationResponse(BaseModel):
    success: bool
    data: Optional[GameGenerationResult] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.now()