from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from ..services.history_service import history_service
from ..services.game_service import game_service
from ..models.history_models import (
    ConversationHistory,
    NewGameRequest,
    HistoryBasedGameRequest,
    GameGenerationResponse,
    ConversationSummaryResponse
)
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(tags=["history"])


# ===== 核心4个API接口 =====

@router.post("/api/game/new", response_model=GameGenerationResponse)
async def generate_new_game(request: NewGameRequest):
    """1. 创建新游戏对话 - 前端无需参数，返回conversation_id和message_id"""
    try:
        conversation_id = str(uuid.uuid4())

        # 调用游戏生成服务（现在自动保存到历史，包括RAG数据）
        result = await game_service.generate_game(
            prompt=request.user_prompt,
            session_id=conversation_id,
            save_to_history=True  # ✅ 改为 True，让 game_service 处理所有保存逻辑
        )

        # game_service 已经保存了完整的数据（包括 rag_enhanced_prompt 和 dev_guidance）
        # 现在我们只需要返回结果

        # 从保存的数据中获取 message_id
        # 由于 game_service 已经保存，我们需要从最新的消息中获取
        conversation = await history_service.get_conversation_by_id(conversation_id)
        latest_message = conversation.messages[-1] if conversation and conversation.messages else None
        message_id = latest_message.message_id if latest_message else str(uuid.uuid4())

        # 构建返回的 game_data（从保存的数据中获取）
        game_data = latest_message.game_data if latest_message and latest_message.game_data else None

        return GameGenerationResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            game_data=game_data,
            usage=None
        )

    except Exception as e:
        logger.error(f"创建新游戏失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建新游戏失败")


@router.post("/api/game/history-based", response_model=GameGenerationResponse)
async def generate_history_based_game(request: HistoryBasedGameRequest):
    """2. 基于历史对话生成游戏 - 需要conversation_id和parent_message_id"""
    try:
        # 生成历史增强prompt
        history_enhanced_prompt = await history_service.generate_history_enhanced_prompt(
            conversation_id=request.conversation_id,
            parent_message_id=request.parent_message_id,
            user_prompt=request.user_prompt
        )

        # 调用游戏生成服务（现在自动保存到历史，包括RAG数据）
        result = await game_service.generate_game(
            prompt=history_enhanced_prompt,
            session_id=request.conversation_id,
            save_to_history=True  # ✅ 改为 True，让 game_service 处理所有保存逻辑
        )

        # game_service 已经保存了完整的数据（包括 rag_enhanced_prompt 和 dev_guidance）
        # 现在我们只需要返回结果

        # 从保存的数据中获取最新的 message_id
        conversation = await history_service.get_conversation_by_id(request.conversation_id)
        latest_message = conversation.messages[-1] if conversation and conversation.messages else None
        message_id = latest_message.message_id if latest_message else str(uuid.uuid4())

        # 构建返回的 game_data（从保存的数据中获取）
        game_data = latest_message.game_data if latest_message and latest_message.game_data else None

        return GameGenerationResponse(
            conversation_id=request.conversation_id,
            message_id=message_id,
            game_data=game_data,
            usage=None
        )

    except Exception as e:
        logger.error(f"基于历史生成游戏失败: {str(e)}")
        raise HTTPException(status_code=500, detail="基于历史生成游戏失败")


@router.get("/api/conversations/list", response_model=List[ConversationSummaryResponse])
async def get_conversations_list(
    limit: int = Query(default=100, ge=1, le=1000)
):
    """3. 获取历史对话列表 - 返回新格式包含完整messages"""
    try:
        conversations_data = await history_service.get_all_conversations_new_format(limit)

        conversations = []
        for conv_data in conversations_data:
            # 转换消息格式
            messages = []
            for msg_data in conv_data.get("messages", []):
                from ..models.history_models import ConversationMessage, GameData

                # 构建游戏数据
                game_data = None
                if msg_data.get("game_data"):
                    gd = msg_data["game_data"]
                    game_data = GameData(
                        title=gd.get("title", ""),
                        game_type=gd.get("game_type", ""),
                        game_logic=gd.get("game_logic", ""),
                        description=gd.get("description", ""),
                        html_content=gd.get("html_content", ""),
                        image_resources=gd.get("image_resources", []),
                        audio_resources=gd.get("audio_resources", []),
                        agent_chain=gd.get("agent_chain", [])
                    )

                # 构建消息
                message = ConversationMessage(
                    message_id=msg_data.get("message_id", ""),
                    user_prompt=msg_data.get("user_prompt", ""),
                    history_enhanced_prompt=msg_data.get("history_enhanced_prompt"),
                    parent_message_id=msg_data.get("parent_message_id"),
                    timestamp=msg_data.get("timestamp", datetime.utcnow()),
                    game_data=game_data,
                    usage=msg_data.get("usage")
                )
                messages.append(message)

            conversations.append(ConversationSummaryResponse(
                intro=conv_data.get("intro", "新对话"),
                conversation_id=conv_data["conversation_id"],
                timestamp=conv_data.get("timestamp", datetime.utcnow()),
                messages=messages
            ))

        return conversations

    except Exception as e:
        logger.error(f"获取对话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取对话列表失败")


@router.get("/api/conversations/{conversation_id}/full", response_model=ConversationHistory)
async def get_full_conversation(conversation_id: str):
    """4. 获取对话详细数据 - 获取完整对话信息"""
    try:
        conversation = await history_service.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取完整对话详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取对话详情失败")