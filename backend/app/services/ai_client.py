import anthropic
from typing import List, Dict, Any
from ..config import settings
from ..services.history_service import history_service
import logging

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
        )


    async def chat_completion(
        self,
        system_message: str,
        user_message: str,
        model: str = None,
        previous_chat_id: str = None,
        agent_name: str = None
    ) -> Dict[str, Any]:
        """
        通用的聊天完成接口，支持对话历史
        """
        try:
            model = model or settings.default_model

            # 构建消息列表
            messages = []

            # 加载历史对话（如果有）
            if previous_chat_id:
                try:
                    conversation_history = await history_service.get_conversation_history(previous_chat_id)
                    if conversation_history and conversation_history.messages:
                        # 只加载非 file_generate_agent 的历史消息
                        for msg in conversation_history.messages:
                            if msg.get("agent_name") != "FileGenerateAgent":
                                # 只保留 user 和 assistant 角色的消息
                                if msg.get("role") in ["user", "assistant"]:
                                    messages.append({
                                        "role": msg["role"],
                                        "content": msg["content"]
                                    })
                    logger.info(f"加载历史对话: {len(messages)} 条消息")
                except Exception as e:
                    logger.warning(f"加载历史对话失败，继续执行: {str(e)}")

            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})

            logger.info(f"发送AI请求 - 模型: {model}, 消息长度: {len(messages)}")

            completion = self.client.messages.create(
                model=model,
                max_tokens=10240,
                system=system_message,
                messages=messages
            )

            response = {
                "content": completion.content[0].text,
                "role": "assistant",
                "model": model,
                "usage": {
                    "input_tokens": completion.usage.input_tokens,
                    "output_tokens": completion.usage.output_tokens
                } if completion.usage else None
            }

            # 注意：对话历史现在由game_service统一管理，不在此处保存
            if previous_chat_id and agent_name != "FileGenerateAgent":
                logger.debug(f"Agent {agent_name} 执行完成，对话历史由上层统一管理")

            logger.info(f"AI响应成功 - 内容长度: {len(response['content'])}")
            return response

        except Exception as e:
            logger.error(f"AI请求失败: {str(e)}")
            raise Exception(f"AI接口调用失败: {str(e)}")
    
    async def get_game_logic(
        self,
        system_message: str,
        user_message: str,
        previous_chat_id: str = None
    ) -> Dict[str, Any]:
        """游戏逻辑生成"""
        return await self.chat_completion(
            system_message,
            user_message,
            previous_chat_id=previous_chat_id,
            agent_name="GameLogicAgent"
        )
    
    async def get_game_files(
        self,
        system_message: str,
        user_message: str,
         previous_chat_id: str = None
    ) -> Dict[str, Any]:
        """游戏文件生成"""
        return await self.chat_completion(
            system_message,
            user_message,
            previous_chat_id=previous_chat_id,
            agent_name="FileGenerateAgent"
        )
    
    async def get_image_resources(
        self,
        system_message: str,
        user_message: str,
        previous_chat_id: str = None
    ) -> Dict[str, Any]:
        """图像资源生成"""
        return await self.chat_completion(
            system_message,
            user_message,
            previous_chat_id=previous_chat_id,
            agent_name="ImageResourceAgent"
        )
    
    async def get_audio_resources(
        self,
        system_message: str,
        user_message: str,
        previous_chat_id: str = None
    ) -> Dict[str, Any]:
        """音频资源生成"""
        return await self.chat_completion(
            system_message,
            user_message,
            previous_chat_id=previous_chat_id,
            agent_name="AudioResourceAgent"
        )


# 全局AI客户端实例
ai_client = AIClient()