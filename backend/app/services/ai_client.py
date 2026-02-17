from typing import List, Dict, Any, Optional
from ..config import settings
from ..services.history_service import history_service
import logging

logger = logging.getLogger(__name__)


class AIClient:
    """统一的 AI 客户端，支持 Kimi (OpenAI 兼容) 和 Anthropic"""

    def __init__(self):
        self._openai_client = None
        self._anthropic_client = None

    def _get_openai_client(self):
        """延迟初始化 OpenAI 兼容客户端（用于 Kimi）"""
        if self._openai_client is None and settings.kimi_api_key:
            from openai import OpenAI
            self._openai_client = OpenAI(
                api_key=settings.kimi_api_key,
                base_url=settings.kimi_base_url,
            )
        return self._openai_client

    def _get_anthropic_client(self):
        """延迟初始化 Anthropic 客户端"""
        if self._anthropic_client is None and settings.anthropic_api_key:
            import anthropic
            self._anthropic_client = anthropic.Anthropic(
                api_key=settings.anthropic_api_key,
                base_url=settings.anthropic_base_url,
            )
        return self._anthropic_client

    def _resolve_provider_and_model(self, model: Optional[str] = None) -> tuple:
        """
        解析模型，返回 (provider, model_id)
        provider: 'kimi' | 'anthropic'
        """
        model = model or settings.default_model
        provider = settings.default_model_provider

        # 根据模型 ID 推断 provider
        if model.startswith("kimi-") or model.startswith("moonshot-"):
            provider = "kimi"
        elif model.startswith("claude-"):
            provider = "anthropic"

        return provider, model

    async def chat_completion(
        self,
        system_message: str,
        user_message: str,
        model: str = None,
        previous_chat_id: str = None,
        agent_name: str = None,
        use_streaming: bool = None
    ) -> Dict[str, Any]:
        """
        通用的聊天完成接口，支持 Kimi 和 Anthropic
        """
        provider, model_id = self._resolve_provider_and_model(model)

        if provider == "kimi":
            return await self._chat_completion_kimi(
                system_message=system_message,
                user_message=user_message,
                model=model_id,
                previous_chat_id=previous_chat_id,
                agent_name=agent_name,
                use_streaming=use_streaming,
            )
        else:
            return await self._chat_completion_anthropic(
                system_message=system_message,
                user_message=user_message,
                model=model_id,
                previous_chat_id=previous_chat_id,
                agent_name=agent_name,
                use_streaming=use_streaming,
            )

    async def _chat_completion_kimi(
        self,
        system_message: str,
        user_message: str,
        model: str,
        previous_chat_id: str = None,
        agent_name: str = None,
        use_streaming: bool = None,
    ) -> Dict[str, Any]:
        """Kimi (OpenAI 兼容) 接口"""
        client = self._get_openai_client()
        if not client:
            raise Exception("Kimi API 未配置，请在 .env 中设置 KIMI_API_KEY")

        messages = [{"role": "system", "content": system_message}]

        if previous_chat_id:
            try:
                conv = await history_service.get_conversation_by_id(previous_chat_id) or await history_service.get_conversation_history(previous_chat_id)
                if conv and conv.messages:
                    for msg in conv.messages:
                        messages.append({"role": "user", "content": msg.user_prompt})
                        if msg.game_data:
                            messages.append({"role": "assistant", "content": f"游戏：{msg.game_data.title}\n{msg.game_data.description}"})
            except Exception as e:
                logger.warning(f"加载历史对话失败: {str(e)}")

        messages.append({"role": "user", "content": user_message})
        should_stream = use_streaming if use_streaming is not None else (agent_name == "FileGenerateAgent")

        try:
            if should_stream:
                full_content = ""
                usage_info = None
                stream = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.6,
                    stream=True,
                )
                for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if delta and delta.content:
                            full_content += delta.content
                    if chunk.usage:
                        usage_info = chunk.usage

                return {
                    "content": full_content,
                    "role": "assistant",
                    "model": model,
                    "usage": {
                        "input_tokens": usage_info.prompt_tokens if usage_info else 0,
                        "output_tokens": usage_info.completion_tokens if usage_info else 0,
                    } if usage_info else None
                }
            else:
                completion = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.6,
                )
                choice = completion.choices[0]
                usage = completion.usage
                return {
                    "content": choice.message.content or "",
                    "role": "assistant",
                    "model": model,
                    "usage": {
                        "input_tokens": usage.prompt_tokens if usage else 0,
                        "output_tokens": usage.completion_tokens if usage else 0,
                    } if usage else None
                }
        except Exception as e:
            logger.error(f"Kimi API 调用失败: {str(e)}")
            raise Exception(f"AI 接口调用失败: {str(e)}")

    async def _chat_completion_anthropic(
        self,
        system_message: str,
        user_message: str,
        model: str,
        previous_chat_id: str = None,
        agent_name: str = None,
        use_streaming: bool = None,
    ) -> Dict[str, Any]:
        """Anthropic Claude 接口"""
        client = self._get_anthropic_client()
        if not client:
            raise Exception("Anthropic API 未配置，请在 .env 中设置 ANTHROPIC_API_KEY")

        messages = []
        if previous_chat_id:
            try:
                conv = await history_service.get_conversation_by_id(previous_chat_id) or await history_service.get_conversation_history(previous_chat_id)
                if conv and conv.messages:
                    for msg in conv.messages:
                        messages.append({"role": "user", "content": msg.user_prompt})
                        if msg.game_data:
                            messages.append({"role": "assistant", "content": f"游戏：{msg.game_data.title}\n{msg.game_data.description}"})
            except Exception as e:
                logger.warning(f"加载历史对话失败: {str(e)}")

        messages.append({"role": "user", "content": user_message})
        should_stream = use_streaming if use_streaming is not None else (agent_name == "FileGenerateAgent")

        try:
            if should_stream:
                full_content = ""
                usage_info = None
                with client.messages.stream(
                    model=model,
                    max_tokens=40860,
                    system=system_message,
                    messages=messages
                ) as stream:
                    for event in stream:
                        if event.type == "content_block_delta":
                            if hasattr(event.delta, 'text'):
                                full_content += event.delta.text
                        elif event.type == "message_delta":
                            if hasattr(event.delta, 'usage'):
                                usage_info = event.delta.usage
                return {
                    "content": full_content,
                    "role": "assistant",
                    "model": model,
                    "usage": {
                        "input_tokens": usage_info.input_tokens if usage_info else 0,
                        "output_tokens": usage_info.output_tokens if usage_info else 0,
                    } if usage_info else None
                }
            else:
                completion = client.messages.create(
                    model=model,
                    max_tokens=40860,
                    system=system_message,
                    messages=messages
                )
                return {
                    "content": completion.content[0].text,
                    "role": "assistant",
                    "model": model,
                    "usage": {
                        "input_tokens": completion.usage.input_tokens,
                        "output_tokens": completion.usage.output_tokens,
                    } if completion.usage else None
                }
        except Exception as e:
            logger.error(f"Anthropic API 调用失败: {str(e)}")
            raise Exception(f"AI 接口调用失败: {str(e)}")

    async def get_game_logic(
        self,
        system_message: str,
        user_message: str,
        previous_chat_id: str = None,
        model: str = None,
        use_streaming: bool = True
    ) -> Dict[str, Any]:
        """游戏逻辑生成"""
        return await self.chat_completion(
            system_message,
            user_message,
            model=model,
            previous_chat_id=previous_chat_id,
            agent_name="GameLogicAgent",
            use_streaming=use_streaming
        )

    async def get_game_files(
        self,
        system_message: str,
        user_message: str,
        previous_chat_id: str = None,
        model: str = None,
        use_streaming: bool = True
    ) -> Dict[str, Any]:
        """游戏文件生成"""
        return await self.chat_completion(
            system_message,
            user_message,
            model=model,
            previous_chat_id=previous_chat_id,
            agent_name="FileGenerateAgent",
            use_streaming=use_streaming
        )

    async def get_image_resources(
        self,
        system_message: str,
        user_message: str,
        previous_chat_id: str = None,
        model: str = None
    ) -> Dict[str, Any]:
        """图像资源生成"""
        return await self.chat_completion(
            system_message,
            user_message,
            model=model,
            previous_chat_id=previous_chat_id,
            agent_name="ImageResourceAgent"
        )

    async def get_audio_resources(
        self,
        system_message: str,
        user_message: str,
        previous_chat_id: str = None,
        model: str = None
    ) -> Dict[str, Any]:
        """音频资源生成"""
        return await self.chat_completion(
            system_message,
            user_message,
            model=model,
            previous_chat_id=previous_chat_id,
            agent_name="AudioResourceAgent"
        )


# 全局 AI 客户端实例
ai_client = AIClient()
