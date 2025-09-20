from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..services.history_service import history_service
from ..models.history_models import GameGenerationHistory, GameIterationRequest

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/games/{session_id}", response_model=List[GameGenerationHistory])
async def get_session_games(
    session_id: str,
    limit: int = Query(default=10, ge=1, le=100)
):
    """获取会话的游戏历史记录"""
    try:
        histories = await history_service.get_session_history(session_id, limit)
        return histories
    except Exception as e:
        logger.error(f"获取会话历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取历史记录失败")


@router.get("/games/{session_id}/latest", response_model=Optional[GameGenerationHistory])
async def get_latest_game(session_id: str):
    """获取会话的最新游戏版本"""
    try:
        latest = await history_service.get_latest_version(session_id)
        return latest
    except Exception as e:
        logger.error(f"获取最新版本失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取最新版本失败")


@router.get("/game/{game_id}", response_model=GameGenerationHistory)
async def get_game_by_id(game_id: str):
    """根据ID获取游戏记录"""
    try:
        game = await history_service.get_game_by_id(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="游戏记录未找到")
        return game
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的游戏ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取游戏记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取游戏记录失败")


@router.post("/game/{game_id}/feedback")
async def update_game_feedback(
    game_id: str,
    rating: Optional[int] = None,
    feedback: Optional[str] = None
):
    """更新游戏的用户反馈"""
    try:
        if rating is not None and (rating < 1 or rating > 5):
            raise HTTPException(status_code=400, detail="评分必须在1-5之间")
        
        success = await history_service.update_user_feedback(
            game_id, rating, feedback
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="游戏记录未找到或更新失败")
        
        return {"message": "反馈更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新反馈失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新反馈失败")


@router.get("/conversations/{session_id}")
async def get_conversation_history(session_id: str):
    """获取对话历史"""
    try:
        conversation = await history_service.get_conversation_history(session_id)
        return conversation
    except Exception as e:
        logger.error(f"获取对话历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取对话历史失败")


@router.get("/health")
async def history_health_check():
    """历史服务健康检查"""
    try:
        # 测试MongoDB连接
        await history_service.client.admin.command('ping')
        return {
            "status": "healthy",
            "mongodb": "connected",
            "message": "历史服务运行正常"
        }
    except Exception as e:
        logger.error(f"历史服务健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "mongodb": "disconnected",
                "error": str(e)
            }
        )