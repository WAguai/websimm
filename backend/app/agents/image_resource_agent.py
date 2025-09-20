from .base_agent import BaseAgent
from ..models.context_models import GameContext
from ..models.game_models import ImageResourceResult
from ..services.resource_generation_service import resource_generation_service
import logging

logger = logging.getLogger(__name__)


class ImageResourceAgent(BaseAgent):
    def __init__(self):
        super().__init__("ImageResourceAgent")
    
    @property
    def system_message(self) -> str:
        return """
            你是一位专业的游戏美术资源专家，擅长为网页游戏生成合适的图像资源。
            基于游戏类型和特征，为游戏生成占位图像资源列表。

            请按照以下格式输出（JSON）：
            {
            "imageResources": ["图像URL1", "图像URL2", ...],
            "reasoning": "资源选择的理由说明"
            }

            注意：当前使用占位图像，实际项目中可替换为真实资源。
            """
    
    async def process(self, context: GameContext) -> GameContext:
        """处理图像资源生成"""
        logger.info(f"🎨 {self.agent_name}: 开始生成图像资源...")
        
        try:
            if not context.game_logic:
                raise ValueError("缺少游戏逻辑信息")
            
            # 获取游戏信息
            game_type = context.game_logic.game_type
            visual_style = context.game_features.visual_style if context.game_features else "现代风格"
            game_elements = context.game_features.game_elements if context.game_features else []
            
            # 使用高质量资源生成服务
            image_resources = resource_generation_service.generate_game_images(
                game_type, visual_style, game_elements
            )
            
            # 更新上下文
            context.image_resources = image_resources
            context = self.update_context(context)
            
            logger.info(f"✅ {self.agent_name}: 图像资源生成完成")
            logger.info(f"📊 生成资源数量: {len(image_resources)}")
            logger.info(f"🎨 视觉风格: {visual_style}")
            logger.info(f"🎮 游戏元素: {', '.join(game_elements)}")
            
            return context
            
        except Exception as e:
            logger.error(f"❌ {self.agent_name}: 处理失败 - {str(e)}")
            raise Exception(f"图像资源生成失败: {str(e)}")
