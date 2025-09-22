from .base_agent import BaseAgent
from ..models.context_models import GameContext, GameFeatures
from ..models.game_models import GameLogicResult
import logging

logger = logging.getLogger(__name__)


class GameLogicAgent(BaseAgent):
    def __init__(self):
        super().__init__("GameLogicAgent")
    
    @property
    def system_message(self) -> str:
        return """
-角色：
  你是一位资深的网页小游戏策划专家，擅长将创意构思转化为完整可实现的游戏设计文案。
  用户将向你提供部分想法、玩法构想、主题方向或目标玩家群体的信息。
  你的任务是基于这些信息，设计一个具有创新性、趣味性和可实现性的网页小游戏概念，并输出结构化内容。
  请按照以下格式输出一个完整的游戏逻辑说明（JSON）：

-输出格式：
  {
    "title": "简洁、有趣且契合主题的游戏名称",
    "gameType": "游戏所属类型，如：益智、动作、模拟、文字冒险等",
    "gameLogic": "简洁明了地描述核心玩法机制，包括玩家的操作方式、规则循环和获胜条件",
    "description": "一段吸引人的游戏介绍，概括玩法亮点、创意点、适合人群，语气轻松自然"
  }

-备注：
  如果用户输入的信息不完整，请根据已有内容合理补全设计。
  请确保输出结构完全符合上述 JSON 格式，字段命名准确。
  所有文本建议使用简体中文，除非用户特别指定其他语言。
  用户输入的信息可能包含了历史对话数据，你需要根据历史对话数据对当前的任务前的游戏逻辑进行更新。
"""
    
    def infer_game_features(self, game_logic_result: GameLogicResult) -> GameFeatures:
        """根据游戏逻辑推断游戏特征"""
        features = GameFeatures()
        
        game_type = game_logic_result.game_type.lower()
        game_logic = game_logic_result.game_logic.lower()
        
        # 推断视觉风格
        if any(word in game_logic for word in ['像素', 'pixel', '复古', 'retro']):
            features.visual_style = "像素风格"
        elif any(word in game_logic for word in ['简约', 'minimalist', '简单']):
            features.visual_style = "简约风格"
        elif any(word in game_logic for word in ['卡通', 'cartoon', '可爱']):
            features.visual_style = "卡通风格"
        else:
            features.visual_style = "现代风格"
        
        # 推断复杂度
        if game_type in ['益智', 'puzzle']:
            features.complexity = "中等"
        elif game_type in ['动作', 'action']:
            features.complexity = "高"
        else:
            features.complexity = "简单"
        
        # 推断游戏元素
        elements = []
        if any(word in game_logic for word in ['玩家', 'player', '角色']):
            elements.append("玩家角色")
        if any(word in game_logic for word in ['敌人', 'enemy', '怪物']):
            elements.append("敌人")
        if any(word in game_logic for word in ['道具', 'item', '收集']):
            elements.append("道具系统")
        if any(word in game_logic for word in ['得分', 'score', '分数']):
            elements.append("得分系统")
        
        features.game_elements = elements
        
        # 推断交互类型
        interactions = []
        if any(word in game_logic for word in ['键盘', 'keyboard', '按键']):
            interactions.append("键盘控制")
        if any(word in game_logic for word in ['鼠标', 'mouse', '点击']):
            interactions.append("鼠标交互")
        if any(word in game_logic for word in ['触摸', 'touch', '手机']):
            interactions.append("触摸控制")
        
        features.interaction_types = interactions
        
        return features
    
    async def process(self, context: GameContext, session_id: str = None) -> GameContext:
        """处理游戏逻辑生成"""
        logger.info(f"🎮 {self.agent_name}: 开始生成游戏逻辑...")

        try:
            # 调用AI生成游戏逻辑
            print("logic user_prompt：", context.user_prompt)
            response = await self.ai_client.get_game_logic(
                self.system_message,
                context.user_prompt,
                previous_chat_id=session_id
            )
            
            # 解析响应
            print("logic",response)
            game_data = self.extract_json_code_block(response["content"])
            print(game_data)
            
            # 创建游戏逻辑结果
            game_logic_result = GameLogicResult(
                title=game_data["title"],
                description=game_data["description"],
                game_type=game_data["gameType"],
                game_logic=game_data["gameLogic"]
            )
            
            # 推断游戏特征
            game_features = self.infer_game_features(game_logic_result)
            
            # 更新上下文
            context.game_logic = game_logic_result
            context.game_features = game_features
            context = self.update_context(context)
            
            logger.info(f"✅ {self.agent_name}: 游戏逻辑生成完成")
            logger.info(f"📊 游戏信息 - 标题: {game_logic_result.title}, 类型: {game_logic_result.game_type}")
            
            return context
            
        except Exception as e:
            logger.error(f"❌ {self.agent_name}: 处理失败 - {str(e)}")
            raise Exception(f"游戏逻辑生成失败: {str(e)}")