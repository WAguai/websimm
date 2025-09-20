import openai
from typing import List, Dict, Any
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )


    async def chat_completion(
        self,
        system_message: str,
        user_message: str,
        model: str = None,
        previous_chat_id: str = None
    ) -> Dict[str, Any]:
        """
        通用的聊天完成接口
        """
        try:
            model = model or settings.default_model
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
            
            logger.info(f"发送AI请求 - 模型: {model}, 消息长度: {len(messages)}")
            
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages
            )
            
            response = {
                "content": completion.choices[0].message.content,
                "role": completion.choices[0].message.role,
                "model": model,
                "usage": completion.usage.dict() if completion.usage else None
            }
            
            logger.info(f"AI响应成功 - 内容长度: {len(response['content'])}")
            return response
            
        except Exception as e:
            print(settings.openai_api_key)
            logger.error(f"AI请求失败: {str(e)}")
            raise Exception(f"AI接口调用失败: {str(e)}")
    
    async def get_game_logic(
        self,
        system_message: str,
        user_message: str,
        previous_chat_id: str = None
    ) -> Dict[str, Any]:
        """游戏逻辑生成"""
        return await self.chat_completion(system_message, user_message, previous_chat_id=previous_chat_id)
    
    async def get_game_files(
        self,
        system_message: str,
        user_message: str,
        previous_chat_id: str = None
    ) -> Dict[str, Any]:
        """游戏文件生成"""
        return await self.chat_completion(system_message, user_message, previous_chat_id=previous_chat_id)
    
    async def get_image_resources(
        self,
        system_message: str,
        user_message: str,
        previous_chat_id: str = None
    ) -> Dict[str, Any]:
        """图像资源生成"""
        return await self.chat_completion(system_message, user_message, previous_chat_id=previous_chat_id)
    
    async def get_audio_resources(
        self,
        system_message: str,
        user_message: str,
        previous_chat_id: str = None
    ) -> Dict[str, Any]:
        """音频资源生成"""
        return await self.chat_completion(system_message, user_message, previous_chat_id=previous_chat_id)


# 全局AI客户端实例
ai_client = AIClient()