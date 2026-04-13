from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from ..models.game_models import GameGenerationRequest, GameGenerationResponse
from ..models.history_models import GameIterationRequest
from ..services.game_service import game_service
from ..config import settings
import logging
from datetime import datetime
from typing import Optional, AsyncGenerator
import json

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


@router.post("/generate/stream")
async def generate_game_stream(
    request: GameGenerationRequest,
    session_id: Optional[str] = Query(None, description="会话ID，用于历史记录关联"),
):
    """
    流式生成游戏接口（SSE）

    注意：目前按阶段推送事件（start/result/error），后续可细化到每个Agent或token级别
    """

    async def event_generator() -> AsyncGenerator[bytes, None]:
        # 1. 立即推送开始事件，降低首字节延迟
        started_event = {"event": "started", "timestamp": datetime.now().isoformat()}
        yield f"data: {json.dumps(started_event, ensure_ascii=False)}\n\n".encode("utf-8")

        try:
            logger.info(f"🎮 [SSE] 收到游戏生成请求: {request.prompt}")
            result = await game_service.generate_game(
                prompt=request.prompt,
                session_id=session_id,
                context_messages=request.context,
            )

            response_payload = {
                "success": True,
                "data": result.model_dump() if hasattr(result, "model_dump") else result.__dict__,
                "timestamp": datetime.now().isoformat(),
            }
            yield f"data: {json.dumps({'event': 'result', **response_payload}, ensure_ascii=False)}\n\n".encode(
                "utf-8"
            )
        except Exception as e:
            logger.error(f"❌ [SSE] 游戏生成失败: {str(e)}")
            error_event = {
                "event": "error",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n".encode("utf-8")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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