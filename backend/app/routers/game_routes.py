from fastapi import APIRouter, HTTPException, Query
from ..models.game_models import GameGenerationRequest, GameGenerationResponse
from ..models.history_models import GameIterationRequest
from ..services.game_service import game_service
from ..config import settings
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/game", tags=["game"])


@router.get("/models")
async def get_available_models():
    """获取可用的 AI 模型列表，供前端模型选择器使用"""
    return {"models": settings.get_available_models(), "default": settings.default_model}


@router.post("/generate", response_model=GameGenerationResponse)
async def generate_game(
    request: GameGenerationRequest,
    session_id: Optional[str] = Query(None, description="会话ID，用于历史记录关联")
):
    """
    生成游戏接口
    
    接收用户需求，通过多代理协作生成完整的网页游戏
    """
    try:
        logger.info(f"🎮 收到游戏生成请求: {request.prompt}")
        
        # 调用游戏生成服务
        result = await game_service.generate_game(
            prompt=request.prompt,
            session_id=session_id,
            context_messages=request.context
        )
        
        # 返回成功响应
        return GameGenerationResponse(
            success=True,
            data=result,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"❌ 游戏生成失败: {str(e)}")
        
        # 返回错误响应
        return GameGenerationResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now()
        )


@router.post("/iterate", response_model=GameGenerationResponse)
async def iterate_game(iteration_request: GameIterationRequest):
    """
    游戏迭代接口
    
    基于历史版本进行游戏改进和优化
    """
    try:
        logger.info(f"🔄 收到游戏迭代请求: {iteration_request.iteration_prompt}")
        logger.info(f"📚 基础版本ID: {iteration_request.base_version_id}")
        
        # 调用游戏迭代服务
        result = await game_service.iterate_game(iteration_request)
        
        # 返回成功响应
        return GameGenerationResponse(
            success=True,
            data=result,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"❌ 游戏迭代失败: {str(e)}")
        
        # 返回错误响应
        return GameGenerationResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now()
        )


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "game-generation-backend"
    }