from ..models.context_models import GameContext, ContextMetadata
from ..models.game_models import GameGenerationResult
from ..models.history_models import GameIterationRequest, GameData
from ..agents.game_logic_agent import GameLogicAgent
from ..agents.file_generate_agent import FileGenerateAgent
from ..agents.image_resource_agent import ImageResourceAgent
from ..agents.audio_resource_agent import AudioResourceAgent
from ..agents.rag_agent import RAGAgent
from ..agents.orchestrator_agent import OrchestratorAgent
from ..agents.review_agent import ReviewAgent
from ..services.history_service import history_service
from ..services.dag_execution_engine import DAGExecutionEngine

import logging
from typing import List, Dict, Optional
import uuid

logger = logging.getLogger(__name__)


class GameService:
    """游戏生成服务 - 协调多个Agent协作"""

    def __init__(self, enable_rag: bool = True):
        """
        初始化游戏服务

        Args:
            enable_rag: 是否启用RAG增强（默认True）
        """
        self.orchestrator_agent = OrchestratorAgent(enable_rag=enable_rag)
        self.game_logic_agent = GameLogicAgent()
        self.game_code_agent = FileGenerateAgent()
        self.asset_agent = ImageResourceAgent()
        self.audio_agent = AudioResourceAgent()
        # 在保持实现复用的前提下，统一为新架构命名
        self.game_code_agent.agent_name = "GameCodeAgent"
        self.asset_agent.agent_name = "AssetAgent"
        self.audio_agent.agent_name = "AudioAgent"
        self.review_agent = ReviewAgent()

        # RAG支持
        self.enable_rag = enable_rag
        self.rag_agent = None
        if enable_rag:
            try:
                self.rag_agent = RAGAgent()
                logger.info("✅ RAG Agent已初始化")
            except Exception as e:
                logger.warning(f"⚠️  RAG Agent初始化失败，将不使用RAG: {str(e)}")
                self.enable_rag = False

        self.execution_engine = DAGExecutionEngine(
            orchestrator=self.orchestrator_agent,
            game_logic_agent=self.game_logic_agent,
            game_code_agent=self.game_code_agent,
            asset_agent=self.asset_agent,
            audio_agent=self.audio_agent,
            review_agent=self.review_agent,
            rag_agent=self.rag_agent,
        )
    
    async def generate_game(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        context_messages: List[Dict] = None,
        save_to_history: bool = True,
        model: Optional[str] = None
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
        logger.info("🚀 开始多代理游戏生成流程...")
        logger.info(f"📝 用户需求: {prompt}")

        try:
            if not session_id:
                session_id = str(uuid.uuid4())

            context = GameContext(
                user_prompt=prompt,
                model=model,
                request={"user_prompt": prompt, "model": model},
                metadata=ContextMetadata(),
            )
            context.write_artifact(
                name="original_user_prompt",
                producer="OrchestratorAgent",
                content=prompt,
                status="final",
            )

            plan = await self.orchestrator_agent.plan(context, session_id=session_id)
            context.plan = plan
            context = await self.execution_engine.execute(context, plan, session_id=session_id)

            if not context.game_logic or not context.files:
                raise ValueError("执行完成但缺少关键产物（logic或html）")

            review_report = context.metadata.review_report if context.metadata else None
            validation_passed = bool(review_report and review_report.get("status") == "pass")

            result = GameGenerationResult(
                files=context.files,
                title=context.game_logic.title,
                description=context.game_logic.description,
                game_type=context.game_logic.game_type,
                game_logic=context.game_logic.game_logic,
                image_resources=context.image_resources or [],
                audio_resources=context.audio_resources or [],
                validation_passed=validation_passed,
                review_report=review_report,
            )

            if save_to_history:
                try:
                    structured_game_logic = None
                    if hasattr(context.game_logic, "__dict__"):
                        structured_game_logic = {
                            key: value
                            for key, value in context.game_logic.__dict__.items()
                            if key not in ["title", "description", "game_logic", "game_type"]
                        }

                    enhanced_prompt = context.enhanced_prompt if hasattr(context, "enhanced_prompt") else None
                    rag_enhanced_prompt = context.rag_enhanced_prompt if hasattr(context, "rag_enhanced_prompt") else None
                    dev_guidance = getattr(context.game_logic, "dev_guidance", None)

                    game_data = GameData(
                        title=context.game_logic.title,
                        game_type=context.game_logic.game_type,
                        game_logic=context.game_logic.game_logic,
                        description=context.game_logic.description,
                        html_content=context.files.html,
                        image_resources=context.image_resources or [],
                        audio_resources=context.audio_resources or [],
                        agent_chain=context.metadata.agent_chain if context.metadata else [],
                        structured_game_logic=structured_game_logic,
                        target_audience=getattr(context.game_logic, "target_audience", None),
                        difficulty=getattr(context.game_logic, "difficulty", None),
                        core_mechanics=getattr(context.game_logic, "core_mechanics", None),
                        notes_for_dev=getattr(context.game_logic, "notes_for_dev", None),
                        examples=getattr(context.game_logic, "examples", None),
                        enhanced_prompt=enhanced_prompt,
                        usage_stats=context.metadata.usage_stats if context.metadata else None,
                        rag_enhanced_prompt=rag_enhanced_prompt,
                        dev_guidance=dev_guidance,
                    )

                    conversation_id, message_id = await history_service.create_new_game_message(
                        conversation_id=session_id,
                        user_prompt=prompt,
                        game_data=game_data,
                        usage=None,
                    )

                    logger.info(
                        f"💾 游戏消息已保存: conversation_id={conversation_id}, message_id={message_id}"
                    )
                    result.session_id = session_id
                except Exception as e:
                    logger.warning(f"⚠️  保存游戏对话失败: {str(e)}")

            logger.info("=" * 50)
            logger.info("🎉 游戏生成完成!")
            logger.info(f"📊 执行链: {' -> '.join(context.metadata.agent_chain if context.metadata else [])}")
            logger.info(f"🎮 游戏标题: {context.game_logic.title}")
            logger.info(f"🎯 游戏类型: {context.game_logic.game_type}")
            logger.info(f"✅ Review通过: {validation_passed}")
            logger.info(f"📁 HTML文件大小: {len(context.files.html)} 字符")
            logger.info(f"🎨 图像资源: {len(context.image_resources or [])} 个")
            logger.info(f"🔊 音频资源: {len(context.audio_resources or [])} 个")
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
            # 获取历史对话上下文
            conversation_history = await history_service.get_conversation_history(
                iteration_request.session_id
            )

            if not conversation_history or not conversation_history.messages:
                raise ValueError(f"未找到会话历史: {iteration_request.session_id}")

            # 从对话历史中获取最新的游戏数据作为基础版本
            base_game_data = None
            for message in reversed(conversation_history.messages):
                if message.game_data:
                    base_game_data = message.game_data
                    break

            if not base_game_data:
                raise ValueError(f"未找到基础游戏数据: {iteration_request.session_id}")

            # 构建增强的提示词，包含历史信息
            enhanced_prompt = self._build_iteration_prompt(
                iteration_request, base_game_data, conversation_history
            )
            
            logger.info(f"📖 增强提示词已构建，长度: {len(enhanced_prompt)} 字符")
            
            # 使用增强提示词生成新版本（不重复保存历史）
            result = await self.generate_game(
                enhanced_prompt,
                iteration_request.session_id,
                conversation_history.messages if conversation_history else None,
                save_to_history=False
            )
            
            # 保存迭代历史
            try:
                # 构建游戏数据对象（从result重构）
                game_data = GameData(
                    title=result.title,
                    game_type=result.game_type,
                    game_logic=result.game_logic,
                    description=result.description,
                    html_content=result.files.html if result.files else "",
                    image_resources=result.image_resources,
                    audio_resources=result.audio_resources,
                    agent_chain=["OrchestratorAgent", "GameLogicAgent", "GameCodeAgent", "AssetAgent", "AudioAgent", "ReviewAgent"]
                )

                # 生成迭代助手回复
                assistant_response = f"游戏迭代完成！\n\n基于您的要求：{iteration_request.iteration_prompt}\n\n{result.description}"

                # 保存迭代对话
                conversation_id, message_id = await history_service.create_new_game_message(
                    conversation_id=iteration_request.session_id,
                    user_prompt=iteration_request.iteration_prompt,
                    game_data=game_data,
                    usage=None
                )

                logger.info(f"💾 迭代对话历史已保存: conversation_id={conversation_id}, message_id={message_id}")
            except Exception as e:
                logger.warning(f"⚠️  保存迭代对话失败: {str(e)}")
            
            logger.info(f"🎉 游戏迭代完成!")
            return result
            
        except Exception as e:
            logger.error(f"❌ 游戏迭代失败: {str(e)}")
            raise Exception(f"游戏迭代过程中出现错误: {str(e)}")
    
    def _build_iteration_prompt(
        self,
        iteration_request: GameIterationRequest,
        base_game_data: GameData,
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
        prompt_parts.append(f"游戏标题: {base_game_data.title}")
        prompt_parts.append(f"游戏类型: {base_game_data.game_type}")
        prompt_parts.append(f"游戏逻辑: {base_game_data.game_logic}")
        prompt_parts.append(f"游戏描述: {base_game_data.description}")
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
                role = msg.role
                content = msg.content
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