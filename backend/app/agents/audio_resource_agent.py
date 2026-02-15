from .base_agent import BaseAgent
from ..models.context_models import GameContext
from ..models.game_models import AudioResourceResult
from ..services.resource_generation_service import resource_generation_service
import logging

logger = logging.getLogger(__name__)


class AudioResourceAgent(BaseAgent):
    def __init__(self):
        super().__init__("AudioResourceAgent")
    
    @property
    def system_message(self) -> str:
        return """
        你是一位专业的游戏音效设计专家，擅长为网页游戏生成合适的音频资源。
        基于游戏类型和特征，为游戏生成音效资源列表。
        
        请按照以下格式输出（JSON）：
        {
          "audioResources": ["音频URL1", "音频URL2", ...],
          "reasoning": "资源选择的理由说明"
        }
        
        注意：当前使用占位音频，实际项目中可替换为真实资源。
        """
    
    async def process(self, context: GameContext, session_id: str = None) -> GameContext:
        """处理音频资源生成"""
        logger.info(f"🔊 {self.agent_name}: 开始生成音频资源...")
        
        try:
            if not context.game_logic:
                raise ValueError("缺少游戏逻辑信息")
            
            # 优先使用新的结构化音频数据，否则回退到推断数据
            if context.game_logic.audio:
                logger.info("🔊 使用新的音频配置数据生成音频资源")
                audio_data = context.game_logic.audio
                game_type = context.game_logic.game_type
                game_elements = self._extract_audio_elements_from_config(audio_data)
            else:
                logger.info("🔊 使用传统推断数据生成音频资源")
                # 传统方式：从推断特征获取信息
                game_type = context.game_logic.game_type
                game_elements = context.game_features.game_elements if context.game_features else []
            
            # 使用高质量资源生成服务
            audio_resources = resource_generation_service.generate_audio_resources(
                game_type, game_elements
            )
            
            # 更新上下文
            context.audio_resources = audio_resources
            context = self.update_context(context)
            
            logger.info(f"✅ {self.agent_name}: 音频资源生成完成")
            logger.info(f"📊 生成资源数量: {len(audio_resources)}")
            logger.info(f"🎮 游戏元素: {', '.join(game_elements)}")
            
            return context
            
        except Exception as e:
            logger.error(f"❌ {self.agent_name}: 处理失败 - {str(e)}")
            raise Exception(f"音频资源生成失败: {str(e)}")

    def _extract_audio_elements_from_config(self, audio_data):
        """从音频配置数据中提取音频元素"""
        elements = []

        # 从背景音乐配置提取元素
        if audio_data.bgm:
            if audio_data.bgm.mood:
                elements.append(f"{audio_data.bgm.mood}背景音乐")

        # 从音效配置提取元素
        for sfx in audio_data.sfx:
            if sfx.event:
                elements.append(f"{sfx.event}音效")

        # 添加基础音效类型
        basic_elements = ["游戏音效", "环境音", "UI音效"]
        for elem in basic_elements:
            if elem not in elements:
                elements.append(elem)

        return elements if elements else ["基础游戏音效"]
