from .base_agent import BaseAgent
from ..models.context_models import GameContext, GameFeatures
from ..models.game_models import (
    GameLogicResult, DetailedGameLogic, GameUI, GameArt, GameAudio,
    GameEffects, GameMeta, PowerUp, RequiredAsset, BackgroundMusic, SoundEffect
)
import logging

logger = logging.getLogger(__name__)


class GameLogicAgent(BaseAgent):
    def __init__(self):
        super().__init__("GameLogicAgent")
    
    @property
    def system_message(self) -> str:
        return """
角色：
你是一位资深的网页小游戏策划专家，擅长将创意构思转化为完整可实现的游戏设计文案。用户会提供部分想法、主题或目标群体。你的任务是输出一个结构化的游戏逻辑配置（JSON），它不仅包含玩法，还包括美术风格、音效和动效建议，以便后续开发 Agent 能生成高质量的 HTML5 游戏。

输出要求：
1. 必须输出严格的 JSON 格式，字段命名准确，不能缺少字段。
2. JSON 中的内容应完整覆盖玩法机制、美术、音效、UI 等关键元素。
3. 保持简体中文，除非用户特别指定其他语言。
4. 用户输入不完整时，合理补全，并在 notes_for_dev 中说明假设。

输出格式（JSON Schema）：
{
  "title": "游戏名称（简洁、有趣、契合主题）",
  "gameType": "游戏类型（如：益智、动作、模拟、冒险等）",
  "targetAudience": "目标玩家群体",
  "difficulty": "easy|normal|hard，并说明难度变化逻辑",
  "coreMechanics": ["机制1","机制2"],

  "gameLogic": {
    "controls": "操作方式（触摸/键盘/鼠标等）",
    "loop": "游戏主循环（生成→互动→判定→反馈）",
    "winCondition": "胜利条件",
    "loseCondition": "失败条件",
    "scoreSystem": "得分规则（加分、连击、扣分）",
    "progression": "难度/关卡如何随时间或分数变化",
    "powerups": [
      {"id":"powerup1","effect":"效果说明","spawnRate":"概率"}
    ],
    "randomness": "是否含随机元素，以及控制方式"
  },

  "ui": {
    "hud": ["score","timer","life","combo"],
    "screens": ["start","pause","gameover","victory"],
    "hints": "简短的新手提示"
  },

  "art": {
    "theme": "美术主题（像素、赛博朋克、卡通等）",
    "artStyle": "画风（像素/矢量/手绘/极简等）",
    "colorPalette": ["#色1","#色2","#色3"],
    "spriteScale": "小/中/大",
    "requiredAssets": [
      {"name":"角色","type":"sprite","frames":4,"notes":"需要走动/攻击动作"},
      {"name":"背景","type":"image","notes":"循环平铺"}
    ]
  },

  "audio": {
    "bgm": {"mood":"轻快/紧张/舒缓","loop":true},
    "sfx": [
      {"event":"hit","desc":"命中音效"},
      {"event":"powerup","desc":"获得道具音效"}
    ]
  },

  "fx": {
    "particles": ["击中火花","爆炸特效"],
    "tweens": ["抖动","渐隐渐现"],
    "recommended": "例如：得分时数字飘字"
  },

  "meta": {
    "estimatedPlayTime": "单局预计时长（秒）",
    "mobileOptimized": true,
    "recommendedCanvasSize": [宽,高]
  },

  "examples": ["玩法变体示例1","玩法变体示例2"],
  "notes_for_dev": "额外的实现注意事项或补全的假设",
  "description": "一段吸引人的游戏介绍，概括玩法亮点、创意点、适合人群，语气轻松自然",

  "dev_guidance": {
    "api_recommendations": "推荐使用的API或技术栈（如：Phaser、Canvas、WebGL等），说明为什么推荐",
    "key_algorithms": "需要实现的核心算法（如：碰撞检测、路径寻找、物理模拟等）",
    "implementation_priorities": ["优先级1：最重要的功能","优先级2：次要功能"],
    "technical_challenges": "预计的技术难点和解决建议",
    "optimization_suggestions": "性能优化建议（如：对象池、事件节流等）",
    "code_structure_hints": "代码结构建议（如：建议的类/模块划分）"
  }
}

备注：
1. 用户输入的信息可能包含了历史对话数据，你需要根据历史对话数据对当前的任务前的游戏逻辑进行更新。
2. 特别注意：如果用户输入中包含了RAG检索到的API文档（通常在"=== 相关API文档和参考资料 ==="部分），请在dev_guidance.api_recommendations中优先推荐这些已检索到的API，并给出具体的使用场景和代码示例建议。
3. dev_guidance是给FileGenerateAgent的开发指导，要具体、可操作，帮助它生成高质量的代码。
"""
    
    def _create_game_logic_result(self, game_data: dict) -> GameLogicResult:
        """从JSON数据创建GameLogicResult，支持新旧格式向后兼容"""
        try:
            # 提取基础字段（必需）
            title = game_data.get("title", "")
            game_type = game_data.get("gameType", "")
            description = game_data.get("description", "")

            # 处理game_logic字段
            # 新格式中可能是嵌套对象，旧格式是字符串
            game_logic_raw = game_data.get("gameLogic", "")
            if isinstance(game_logic_raw, dict):
                # 新格式：从详细游戏逻辑对象中提取简化描述
                detailed_logic = game_logic_raw
                game_logic_simple = self._extract_simple_game_logic(detailed_logic)
            else:
                # 旧格式：直接使用字符串
                game_logic_simple = game_logic_raw
                detailed_logic = None

            # 构建基础GameLogicResult
            result_data = {
                "title": title,
                "description": description,
                "game_type": game_type,
                "game_logic": game_logic_simple
            }

            # 添加新的可选字段（如果存在）
            if "targetAudience" in game_data:
                result_data["target_audience"] = game_data["targetAudience"]
            if "difficulty" in game_data:
                result_data["difficulty"] = game_data["difficulty"]
            if "coreMechanics" in game_data:
                result_data["core_mechanics"] = game_data["coreMechanics"]
            if "examples" in game_data:
                result_data["examples"] = game_data["examples"]
            if "notes_for_dev" in game_data:
                result_data["notes_for_dev"] = game_data["notes_for_dev"]

            # 处理复杂嵌套对象
            if detailed_logic and isinstance(game_logic_raw, dict):
                result_data["detailed_game_logic"] = self._parse_detailed_game_logic(detailed_logic)

            if "ui" in game_data:
                result_data["ui"] = self._parse_ui(game_data["ui"])

            if "art" in game_data:
                result_data["art"] = self._parse_art(game_data["art"])

            if "audio" in game_data:
                result_data["audio"] = self._parse_audio(game_data["audio"])

            if "fx" in game_data:
                result_data["fx"] = self._parse_effects(game_data["fx"])

            if "meta" in game_data:
                result_data["meta"] = self._parse_meta(game_data["meta"])

            # 处理dev_guidance（新增字段）
            if "dev_guidance" in game_data:
                dev_guidance = game_data["dev_guidance"]
                if isinstance(dev_guidance, dict):
                    # 将dev_guidance转换为字符串形式存储
                    guidance_parts = []
                    if dev_guidance.get("api_recommendations"):
                        guidance_parts.append(f"API推荐: {dev_guidance['api_recommendations']}")
                    if dev_guidance.get("key_algorithms"):
                        guidance_parts.append(f"核心算法: {dev_guidance['key_algorithms']}")
                    if dev_guidance.get("implementation_priorities"):
                        priorities = dev_guidance['implementation_priorities']
                        guidance_parts.append(f"实现优先级: {', '.join(priorities) if isinstance(priorities, list) else priorities}")
                    if dev_guidance.get("technical_challenges"):
                        guidance_parts.append(f"技术难点: {dev_guidance['technical_challenges']}")
                    if dev_guidance.get("optimization_suggestions"):
                        guidance_parts.append(f"优化建议: {dev_guidance['optimization_suggestions']}")
                    if dev_guidance.get("code_structure_hints"):
                        guidance_parts.append(f"代码结构: {dev_guidance['code_structure_hints']}")

                    result_data["dev_guidance"] = "\n".join(guidance_parts)
                else:
                    result_data["dev_guidance"] = str(dev_guidance)

            return GameLogicResult(**result_data)

        except Exception as e:
            logger.warning(f"解析新格式失败，尝试兼容旧格式: {str(e)}")
            # 回退到旧格式解析
            return GameLogicResult(
                title=game_data.get("title", ""),
                description=game_data.get("description", ""),
                game_type=game_data.get("gameType", ""),
                game_logic=game_data.get("gameLogic", "")
            )

    def _extract_simple_game_logic(self, detailed_logic: dict) -> str:
        """从详细游戏逻辑中提取简化描述"""
        parts = []
        if detailed_logic.get("controls"):
            parts.append(f"操作: {detailed_logic['controls']}")
        if detailed_logic.get("winCondition"):
            parts.append(f"胜利条件: {detailed_logic['winCondition']}")
        if detailed_logic.get("loop"):
            parts.append(f"游戏循环: {detailed_logic['loop']}")
        return "; ".join(parts) if parts else ""

    def _parse_detailed_game_logic(self, data: dict) -> DetailedGameLogic:
        """解析详细游戏逻辑"""
        powerups = []
        for pu in data.get("powerups", []):
            powerups.append(PowerUp(
                id=pu.get("id", ""),
                effect=pu.get("effect", ""),
                spawnRate=pu.get("spawnRate", "")
            ))

        return DetailedGameLogic(
            controls=data.get("controls", ""),
            loop=data.get("loop", ""),
            winCondition=data.get("winCondition", ""),
            loseCondition=data.get("loseCondition", ""),
            scoreSystem=data.get("scoreSystem", ""),
            progression=data.get("progression", ""),
            powerups=powerups,
            randomness=data.get("randomness", "")
        )

    def _parse_ui(self, data: dict) -> GameUI:
        """解析UI数据"""
        return GameUI(
            hud=data.get("hud", []),
            screens=data.get("screens", []),
            hints=data.get("hints", "")
        )

    def _parse_art(self, data: dict) -> GameArt:
        """解析美术数据"""
        assets = []
        for asset in data.get("requiredAssets", []):
            assets.append(RequiredAsset(
                name=asset.get("name", ""),
                type=asset.get("type", ""),
                frames=asset.get("frames"),
                notes=asset.get("notes", "")
            ))

        return GameArt(
            theme=data.get("theme", ""),
            artStyle=data.get("artStyle", ""),
            colorPalette=data.get("colorPalette", []),
            spriteScale=data.get("spriteScale", ""),
            requiredAssets=assets
        )

    def _parse_audio(self, data: dict) -> GameAudio:
        """解析音频数据"""
        bgm_data = data.get("bgm", {})
        bgm = BackgroundMusic(
            mood=bgm_data.get("mood", ""),
            loop=bgm_data.get("loop", True)
        )

        sfx = []
        for sfx_data in data.get("sfx", []):
            sfx.append(SoundEffect(
                event=sfx_data.get("event", ""),
                desc=sfx_data.get("desc", "")
            ))

        return GameAudio(bgm=bgm, sfx=sfx)

    def _parse_effects(self, data: dict) -> GameEffects:
        """解析特效数据"""
        return GameEffects(
            particles=data.get("particles", []),
            tweens=data.get("tweens", []),
            recommended=data.get("recommended", "")
        )

    def _parse_meta(self, data: dict) -> GameMeta:
        """解析元数据"""
        return GameMeta(
            estimatedPlayTime=data.get("estimatedPlayTime", ""),
            mobileOptimized=data.get("mobileOptimized", True),
            recommendedCanvasSize=data.get("recommendedCanvasSize", [800, 600])
        )

    def infer_game_features(self, game_logic_result: GameLogicResult) -> GameFeatures:
        """根据游戏逻辑推断游戏特征，优先使用新的结构化数据"""
        features = GameFeatures()

        # 优先使用新的结构化数据
        if self._has_rich_data(game_logic_result):
            logger.info("🔍 使用新的结构化数据推断游戏特征")
            return self._infer_from_rich_data(game_logic_result)

        # 回退到旧的推断逻辑
        logger.info("🔍 使用传统推断逻辑分析游戏特征")
        return self._infer_from_legacy_data(game_logic_result)

    def _has_rich_data(self, result: GameLogicResult) -> bool:
        """检查是否有新的结构化数据"""
        return (result.art is not None or
                result.audio is not None or
                result.detailed_game_logic is not None or
                result.core_mechanics is not None)

    def _infer_from_rich_data(self, result: GameLogicResult) -> GameFeatures:
        """从新的结构化数据推断特征"""
        features = GameFeatures()

        # 从art数据推断视觉风格
        if result.art:
            if result.art.theme:
                features.visual_style = f"{result.art.theme}风格"
            elif result.art.artStyle:
                features.visual_style = f"{result.art.artStyle}风格"
            else:
                features.visual_style = "现代风格"
        else:
            # 回退到传统推断
            features.visual_style = self._infer_visual_style_legacy(result.game_logic)

        # 从difficulty或game_type推断复杂度
        if result.difficulty:
            if "easy" in result.difficulty.lower():
                features.complexity = "简单"
            elif "hard" in result.difficulty.lower():
                features.complexity = "高"
            else:
                features.complexity = "中等"
        else:
            features.complexity = self._infer_complexity_legacy(result.game_type)

        # 从core_mechanics和详细逻辑推断游戏元素
        elements = []
        if result.core_mechanics:
            elements.extend(result.core_mechanics)

        if result.detailed_game_logic:
            if result.detailed_game_logic.powerups:
                elements.append("道具系统")
            if "score" in result.detailed_game_logic.scoreSystem.lower():
                elements.append("得分系统")

        # 补充传统推断
        legacy_elements = self._infer_game_elements_legacy(result.game_logic)
        for elem in legacy_elements:
            if elem not in elements:
                elements.append(elem)

        features.game_elements = elements

        # 从详细游戏逻辑推断交互类型
        interactions = []
        if result.detailed_game_logic and result.detailed_game_logic.controls:
            controls = result.detailed_game_logic.controls.lower()
            if any(word in controls for word in ['键盘', 'keyboard', '按键']):
                interactions.append("键盘控制")
            if any(word in controls for word in ['鼠标', 'mouse', '点击']):
                interactions.append("鼠标交互")
            if any(word in controls for word in ['触摸', 'touch', '手机']):
                interactions.append("触摸控制")
        else:
            # 回退到传统推断
            interactions = self._infer_interactions_legacy(result.game_logic)

        features.interaction_types = interactions

        return features

    def _infer_from_legacy_data(self, result: GameLogicResult) -> GameFeatures:
        """使用传统逻辑推断特征（向后兼容）"""
        features = GameFeatures()

        features.visual_style = self._infer_visual_style_legacy(result.game_logic)
        features.complexity = self._infer_complexity_legacy(result.game_type)
        features.game_elements = self._infer_game_elements_legacy(result.game_logic)
        features.interaction_types = self._infer_interactions_legacy(result.game_logic)

        return features

    def _infer_visual_style_legacy(self, game_logic: str) -> str:
        """传统视觉风格推断"""
        game_logic_lower = game_logic.lower()
        if any(word in game_logic_lower for word in ['像素', 'pixel', '复古', 'retro']):
            return "像素风格"
        elif any(word in game_logic_lower for word in ['简约', 'minimalist', '简单']):
            return "简约风格"
        elif any(word in game_logic_lower for word in ['卡通', 'cartoon', '可爱']):
            return "卡通风格"
        else:
            return "现代风格"

    def _infer_complexity_legacy(self, game_type: str) -> str:
        """传统复杂度推断"""
        game_type_lower = game_type.lower()
        if game_type_lower in ['益智', 'puzzle']:
            return "中等"
        elif game_type_lower in ['动作', 'action']:
            return "高"
        else:
            return "简单"

    def _infer_game_elements_legacy(self, game_logic: str) -> list:
        """传统游戏元素推断"""
        elements = []
        game_logic_lower = game_logic.lower()

        if any(word in game_logic_lower for word in ['玩家', 'player', '角色']):
            elements.append("玩家角色")
        if any(word in game_logic_lower for word in ['敌人', 'enemy', '怪物']):
            elements.append("敌人")
        if any(word in game_logic_lower for word in ['道具', 'item', '收集']):
            elements.append("道具系统")
        if any(word in game_logic_lower for word in ['得分', 'score', '分数']):
            elements.append("得分系统")

        return elements

    def _infer_interactions_legacy(self, game_logic: str) -> list:
        """传统交互类型推断"""
        interactions = []
        game_logic_lower = game_logic.lower()

        if any(word in game_logic_lower for word in ['键盘', 'keyboard', '按键']):
            interactions.append("键盘控制")
        if any(word in game_logic_lower for word in ['鼠标', 'mouse', '点击']):
            interactions.append("鼠标交互")
        if any(word in game_logic_lower for word in ['触摸', 'touch', '手机']):
            interactions.append("触摸控制")

        return interactions
    
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

            # 收集usage统计
            if response.get('usage'):
                self.add_usage_stats(context, response['usage'])

            game_data = self.extract_json_code_block(response["content"])

            # 创建游戏逻辑结果（支持新旧格式）
            game_logic_result = self._create_game_logic_result(game_data)
            
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