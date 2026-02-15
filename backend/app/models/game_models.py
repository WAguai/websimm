from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class GameFiles(BaseModel):
    html: str  # 包含所有代码的完整HTML文件


# ===== 新增：复杂游戏逻辑数据模型 =====

class PowerUp(BaseModel):
    id: str
    effect: str
    spawnRate: str

class DetailedGameLogic(BaseModel):
    controls: str
    loop: str
    winCondition: str
    loseCondition: str
    scoreSystem: str
    progression: str
    powerups: List[PowerUp] = []
    randomness: str

class GameUI(BaseModel):
    hud: List[str]
    screens: List[str]
    hints: str

class RequiredAsset(BaseModel):
    name: str
    type: str
    frames: Optional[int] = None
    notes: str

class GameArt(BaseModel):
    theme: str
    artStyle: str
    colorPalette: List[str]
    spriteScale: str
    requiredAssets: List[RequiredAsset]

class BackgroundMusic(BaseModel):
    mood: str
    loop: bool

class SoundEffect(BaseModel):
    event: str
    desc: str

class GameAudio(BaseModel):
    bgm: BackgroundMusic
    sfx: List[SoundEffect]

class GameEffects(BaseModel):
    particles: List[str]
    tweens: List[str]
    recommended: str

class GameMeta(BaseModel):
    estimatedPlayTime: str
    mobileOptimized: bool
    recommendedCanvasSize: List[int]


class GameLogicResult(BaseModel):
    # ===== 向后兼容：保持原有简单字段 =====
    title: str
    description: str
    game_logic: str  # 简化版的游戏逻辑描述（从detailed_game_logic提取）
    game_type: str

    # ===== 新增：详细结构化数据（可选） =====
    target_audience: Optional[str] = None
    difficulty: Optional[str] = None
    core_mechanics: Optional[List[str]] = None
    detailed_game_logic: Optional[DetailedGameLogic] = None
    ui: Optional[GameUI] = None
    art: Optional[GameArt] = None
    audio: Optional[GameAudio] = None
    fx: Optional[GameEffects] = None
    meta: Optional[GameMeta] = None
    examples: Optional[List[str]] = None
    notes_for_dev: Optional[str] = None

    # ===== 新增：开发指导意见 =====
    dev_guidance: Optional[str] = None  # GameLogicAgent为FileGenerateAgent提供的开发指导


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