from ..models.context_models import GameContext, ContextMetadata
from ..models.game_models import GameGenerationResult
from ..models.history_models import GameIterationRequest
from ..agents.game_logic_agent import GameLogicAgent
from ..agents.file_generate_agent import FileGenerateAgent
from ..agents.image_resource_agent import ImageResourceAgent
from ..agents.audio_resource_agent import AudioResourceAgent
from ..services.history_service import history_service

import logging
from typing import List, Dict, Optional
import uuid

logger = logging.getLogger(__name__)


class GameService:
    """游戏生成服务 - 协调多个Agent协作"""
    
    def __init__(self):
        self.game_logic_agent = GameLogicAgent()
        self.file_generate_agent = FileGenerateAgent()
        self.image_resource_agent = ImageResourceAgent()
        self.audio_resource_agent = AudioResourceAgent()
    
    async def generate_game(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        context_messages: List[Dict] = None
    ) -> GameGenerationResult:
        """
        多代理协作生成游戏
        
        Args:
            prompt: 用户输入的游戏需求
            session_id: 会话ID（可选，用于历史记录）
            context_messages: 上下文消息（可选）
        
        Returns:
            GameGenerationResult: 完整的游戏生成结果
        """
        logger.info(f"🚀 开始多代理游戏生成流程...")
        logger.info(f"📝 用户需求: {prompt}")
        
        try:
            # 生成会话ID（如果未提供）
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # 初始化上下文
            context = GameContext(
                user_prompt=prompt,
                metadata=ContextMetadata()
            )
            
            # 1. 🎮 游戏逻辑 Agent 处理
            logger.info("=" * 50)
            context = await self.game_logic_agent.process(context)
            
            # 2. 📄 文件生成 Agent 处理
            logger.info("=" * 50)
            context = await self.file_generate_agent.process(context)
            
            # 3. 🎨 图像资源 Agent 处理
            logger.info("=" * 50)
            context = await self.image_resource_agent.process(context)
            
            # 4. 🔊 音效资源 Agent 处理
            logger.info("=" * 50)
            context = await self.audio_resource_agent.process(context)
            
            # 构建最终结果
            result = GameGenerationResult(
                files=context.files,
                description=context.game_logic.description,
                game_logic=context.game_logic.game_logic,
                image_resources=context.image_resources,
                audio_resources=context.audio_resources
            )
            
            # 保存历史记录
            try:
                record_id = await history_service.save_game_generation(
                    session_id, context, result
                )
                logger.info(f"💾 历史记录已保存: {record_id}")
                result.session_id = session_id
                result.record_id = record_id
            except Exception as e:
                logger.warning(f"⚠️  保存历史记录失败: {str(e)}")
            
            logger.info("=" * 50)
            logger.info(f"🎉 游戏生成完成!")
            logger.info(f"📊 执行链: {' -> '.join(context.metadata.agent_chain)}")
            logger.info(f"🎮 游戏标题: {context.game_logic.title}")
            logger.info(f"🎯 游戏类型: {context.game_logic.game_type}")
            logger.info(f"📁 HTML文件大小: {len(context.files.html)} 字符")
            logger.info(f"🎨 图像资源: {len(context.image_resources)} 个")
            logger.info(f"🔊 音频资源: {len(context.audio_resources)} 个")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 多代理游戏生成失败: {str(e)}")
            raise Exception(f"游戏生成过程中出现错误: {str(e)}")
    
    async def iterate_game(
        self,
        iteration_request: GameIterationRequest
    ) -> GameGenerationResult:
        """
        游戏迭代 - 基于历史版本进行改进
        
        Args:
            iteration_request: 迭代请求
        
        Returns:
            GameGenerationResult: 迭代后的游戏结果
        """
        logger.info(f"🔄 开始游戏迭代流程...")
        logger.info(f"📝 迭代需求: {iteration_request.iteration_prompt}")
        logger.info(f"📚 基础版本: {iteration_request.base_version_id}")
        
        try:
            # 获取基础版本
            base_game = await history_service.get_game_by_id(iteration_request.base_version_id)
            if not base_game:
                raise ValueError(f"未找到基础游戏版本: {iteration_request.base_version_id}")
            
            # 获取历史对话上下文
            conversation_history = await history_service.get_conversation_history(
                iteration_request.session_id
            )
            
            # 构建增强的提示词，包含历史信息
            enhanced_prompt = self._build_iteration_prompt(
                iteration_request, base_game, conversation_history
            )
            
            logger.info(f"📖 增强提示词已构建，长度: {len(enhanced_prompt)} 字符")
            
            # 使用增强提示词生成新版本
            result = await self.generate_game(
                enhanced_prompt,
                iteration_request.session_id,
                conversation_history.messages if conversation_history else None
            )
            
            # 保存迭代历史（带父版本关联）
            try:
                await history_service.save_game_generation(
                    iteration_request.session_id, 
                    context=None,  # 这里需要从result重构context，暂时传None
                    result=result,
                    parent_version_id=iteration_request.base_version_id
                )
                logger.info(f"💾 迭代历史记录已保存")
            except Exception as e:
                logger.warning(f"⚠️  保存迭代历史失败: {str(e)}")
            
            logger.info(f"🎉 游戏迭代完成!")
            return result
            
        except Exception as e:
            logger.error(f"❌ 游戏迭代失败: {str(e)}")
            raise Exception(f"游戏迭代过程中出现错误: {str(e)}")
    
    def _build_iteration_prompt(
        self,
        iteration_request: GameIterationRequest,
        base_game,
        conversation_history
    ) -> str:
        """构建迭代提示词"""
        prompt_parts = []
        
        # 基础信息
        prompt_parts.append("=== 游戏迭代需求 ===")
        prompt_parts.append(f"用户需求: {iteration_request.iteration_prompt}")
        prompt_parts.append("")
        
        # 历史游戏信息
        prompt_parts.append("=== 基础游戏版本信息 ===")
        prompt_parts.append(f"游戏标题: {base_game.game_title}")
        prompt_parts.append(f"游戏类型: {base_game.game_type}")
        prompt_parts.append(f"游戏逻辑: {base_game.game_logic}")
        prompt_parts.append(f"游戏描述: {base_game.description}")
        prompt_parts.append("")
        
        # 保留和修改的元素
        if iteration_request.keep_elements:
            prompt_parts.append("=== 需要保留的元素 ===")
            prompt_parts.extend([f"- {element}" for element in iteration_request.keep_elements])
            prompt_parts.append("")
        
        if iteration_request.change_elements:
            prompt_parts.append("=== 需要修改的元素 ===")
            prompt_parts.extend([f"- {element}" for element in iteration_request.change_elements])
            prompt_parts.append("")
        
        # 历史对话上下文（最近5条）
        if conversation_history and conversation_history.messages:
            prompt_parts.append("=== 历史对话上下文 ===")
            recent_messages = conversation_history.messages[-5:]  # 最近5条
            for msg in recent_messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                if len(content) > 200:
                    content = content[:200] + "..."
                prompt_parts.append(f"{role}: {content}")
            prompt_parts.append("")
        
        # 迭代指导
        prompt_parts.append("=== 迭代指导 ===")
        prompt_parts.append("请基于上述信息和用户的迭代需求，对游戏进行改进。")
        prompt_parts.append("保持游戏的核心玩法不变的同时，优化用户提到的问题。")
        prompt_parts.append("如果用户指定了需要保留的元素，请确保在新版本中保持这些元素。")
        prompt_parts.append("如果用户指定了需要修改的元素，请重点改进这些部分。")
        
        return "\n".join(prompt_parts)


# 全局游戏服务实例
game_service = GameService()