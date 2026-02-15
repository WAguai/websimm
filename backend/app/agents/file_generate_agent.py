from .base_agent import BaseAgent
from ..models.context_models import GameContext
from ..models.game_models import GameFiles
from ..services.rag_service import get_rag_service
import logging

logger = logging.getLogger(__name__)


class FileGenerateAgent(BaseAgent):
    def __init__(self, enable_rag: bool = True):
        """
        初始化文件生成Agent

        Args:
            enable_rag: 是否启用RAG增强（默认True）
        """
        super().__init__("FileGenerateAgent")

        # RAG支持
        self.enable_rag = enable_rag
        self.rag_service = None
        if enable_rag:
            try:
                self.rag_service = get_rag_service()
                logger.info("✅ FileGenerateAgent: RAG服务已初始化")
            except Exception as e:
                logger.warning(f"⚠️  FileGenerateAgent: RAG服务初始化失败: {str(e)}")
                self.enable_rag = False
    
    @property
    def system_message(self) -> str:
        return """
-角色：
  你是一位资深的HTML5游戏开发专家，专精于生成**高质量、可运行、无bug**的网页游戏。
  你的代码必须做到：打开即玩，无需调试，逻辑完整，用户体验流畅。

-核心原则 - 代码质量第一：
  ✅ 生成的游戏必须可以直接运行，不能有任何bug
  ✅ 所有游戏逻辑必须完整实现，不要有TODO或占位符
  ✅ 必须有完善的错误处理和边界检查
  ✅ 游戏状态转换必须清晰可靠（开始→游戏中→暂停→结束）
  ✅ 用户交互必须响应灵敏且符合直觉

-🔴 框架使用要求（如果指定）：
  如果dev_guidance中推荐了特定框架：
    1. 必须在HTML中引入正确版本的CDN（如Phaser 3.x）
    2. 必须使用该框架的官方API，不要用原生替代
    3. 遵循框架的最佳实践和代码结构
    4. 示例：Phaser游戏必须有config对象和Scene生命周期

-输出格式（严格遵守）：
  {
    "html": "完整的HTML文件内容，包含DOCTYPE、CSS、JS"
  }

-代码质量清单（每一项都必须做到）：

  📦 1. 完整性：
    - 包含完整的HTML结构（DOCTYPE, html, head, body）
    - 包含所有必需的CSS样式（布局、UI、动画）
    - 包含完整的游戏逻辑（无TODO、无占位符、无伪代码）
    - 游戏可以正常开始、运行、结束、重启

  🎮 2. 游戏循环：
    - 实现稳定的游戏循环（requestAnimationFrame或框架方法）
    - 正确的时间步进（deltaTime处理）
    - 帧率控制和性能优化
    - 正确的渲染顺序（清屏→绘制背景→游戏对象→UI）

  🎯 3. 核心机制：
    - 玩家控制：键盘/鼠标输入处理正确且响应灵敏
    - 碰撞检测：精确可靠，有边界检查
    - 物理模拟：如果有重力/速度，计算必须正确
    - 得分系统：计算准确，实时更新显示
    - 胜负判定：条件清晰，触发可靠

  🛡️ 4. 错误处理：
    - 所有数组访问前检查length
    - 所有除法前检查除数不为0
    - 所有对象访问前检查是否存在
    - Canvas操作前检查context是否有效
    - 边界检查：防止游戏对象超出有效范围导致NaN

  🎨 5. 用户界面：
    - 清晰的开始界面（标题、说明、开始按钮）
    - 实时HUD（分数、生命值、时间等）
    - 明确的游戏结束提示（分数、重玩按钮）
    - 必须有暂停功能（P键或按钮）
    - 操作说明必须可见且准确

  ⚙️ 6. 状态管理：
    - 游戏状态：MENU, PLAYING, PAUSED, GAME_OVER
    - 状态转换逻辑清晰，不能卡在某个状态
    - 每个状态下的输入和渲染行为明确
    - 重启功能必须正确重置所有变量

  🎲 7. 游戏平衡：
    - 难度曲线合理（不要一开始就不可能完成）
    - 速度和时间参数经过测试（不要太快或太慢）
    - 碰撞箱大小合理（不要太严格或太宽松）
    - 随机元素有适当限制（不要完全随机导致不可玩）

  ⚡ 8. 性能优化：
    - 避免在游戏循环中创建新对象（使用对象池）
    - 避免不必要的重复计算（缓存常用值）
    - 合理的渲染批次（减少绘制调用）
    - 移除或隐藏屏幕外的对象

  📝 9. 代码质量：
    - 使用ES6+语法（const/let、箭头函数、class）
    - 变量命名清晰有意义
    - 关键逻辑有简短注释
    - 代码结构清晰（初始化→游戏循环→工具函数）
    - 避免全局变量污染（使用立即执行函数或class）

  🔧 10. 常见错误避免：
    ❌ 不要忘记清空Canvas（ctx.clearRect）
    ❌ 不要在循环中splice数组（从后向前遍历或标记删除）
    ❌ 不要使用未定义的变量或函数
    ❌ 不要让游戏对象的位置变成NaN（检查所有数学运算）
    ❌ 不要忘记处理游戏重启时的状态清理
    ❌ 不要让事件监听器重复绑定（先移除再绑定或使用once）
    ❌ 不要使用同步sleep（使用定时器或时间差）
    ❌ 不要让碰撞检测遗漏边界情况

-HTML结构模板：
  ```html
  <!DOCTYPE html>
  <html lang="zh-CN">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>游戏标题</title>
      <!-- 如果使用框架，在这里引入CDN -->
      <style>
          /* 完整的CSS样式 */
          body { margin: 0; padding: 0; overflow: hidden; }
          #gameCanvas { display: block; margin: 0 auto; }
          /* UI样式、按钮、文本等 */
      </style>
  </head>
  <body>
      <!-- 游戏UI容器 -->
      <div id="gameContainer">
          <canvas id="gameCanvas"></canvas>
          <!-- HUD、按钮等UI元素 -->
      </div>

      <script>
          // 游戏代码结构建议：
          // 1. 常量定义
          // 2. 游戏类或对象
          // 3. 初始化函数
          // 4. 游戏循环
          // 5. 工具函数
          // 6. 启动游戏

          // 确保所有代码完整且可运行！
      </script>
  </body>
  </html>
  ```

-最终检查清单（生成前自查）：
  □ 游戏可以正常开始
  □ 玩家可以控制角色/对象
  □ 碰撞检测工作正常
  □ 得分系统正确计算
  □ 游戏有明确的胜负条件
  □ 游戏结束后可以重启
  □ 没有console.error或undefined
  □ 所有变量都有初始值
  □ 没有TODO或占位符
  □ 代码可以直接在浏览器运行

-特别提醒：
  生成的游戏必须是"生产就绪"的质量，用户打开HTML文件就能流畅游玩，无需任何修改或调试！
  如果不确定某个功能能否正确实现，选择简化但可靠的方案，而不是复杂但有bug的方案。
"""
    
    def build_enhanced_prompt(self, context: GameContext) -> str:
        """构建增强的提示词，优先使用新的结构化数据"""
        if not context.game_logic:
            raise ValueError('GameLogic 结果不存在，无法生成游戏文件')

        game_logic_result = context.game_logic

        # 检查是否有新的结构化数据
        has_rich_data = self._has_rich_game_data(game_logic_result)

        if has_rich_data:
            logger.info("🚀 使用新的结构化数据构建增强提示词")
            return self._build_rich_prompt(game_logic_result, context)
        else:
            logger.info("📝 使用传统数据构建基础提示词")
            return self._build_legacy_prompt(game_logic_result, context)

    def _has_rich_game_data(self, game_logic_result) -> bool:
        """检查是否有丰富的结构化数据"""
        return (game_logic_result.detailed_game_logic is not None or
                game_logic_result.ui is not None or
                game_logic_result.art is not None or
                game_logic_result.audio is not None or
                game_logic_result.fx is not None or
                game_logic_result.meta is not None)

    def _build_rich_prompt(self, game_logic_result, context: GameContext) -> str:
        """基于丰富结构化数据构建高质量提示词"""
        prompt_parts = []

        # 基础游戏信息
        prompt_parts.append("请基于以下详细游戏设计生成完整的HTML5游戏：")
        prompt_parts.append(f"\n🎮 游戏名称：{game_logic_result.title}")
        prompt_parts.append(f"🎯 游戏类型：{game_logic_result.game_type}")
        prompt_parts.append(f"📝 游戏描述：{game_logic_result.description}")

        if game_logic_result.target_audience:
            prompt_parts.append(f"👥 目标玩家：{game_logic_result.target_audience}")
        if game_logic_result.difficulty:
            prompt_parts.append(f"⚡ 难度等级：{game_logic_result.difficulty}")

        # 详细游戏逻辑
        if game_logic_result.detailed_game_logic:
            prompt_parts.append("\n🎲 游戏机制详情：")
            logic = game_logic_result.detailed_game_logic
            prompt_parts.append(f"- 操作方式：{logic.controls}")
            prompt_parts.append(f"- 游戏循环：{logic.loop}")
            prompt_parts.append(f"- 胜利条件：{logic.winCondition}")
            prompt_parts.append(f"- 失败条件：{logic.loseCondition}")
            prompt_parts.append(f"- 得分系统：{logic.scoreSystem}")
            prompt_parts.append(f"- 难度递进：{logic.progression}")
            prompt_parts.append(f"- 随机要素：{logic.randomness}")

            if logic.powerups:
                prompt_parts.append("- 道具系统：")
                for powerup in logic.powerups:
                    prompt_parts.append(f"  • {powerup.id}: {powerup.effect} (生成概率: {powerup.spawnRate})")

        # UI设计要求
        if game_logic_result.ui:
            prompt_parts.append("\n🖼️ UI设计要求：")
            ui = game_logic_result.ui
            prompt_parts.append(f"- HUD元素：{', '.join(ui.hud)}")
            prompt_parts.append(f"- 界面流程：{', '.join(ui.screens)}")
            prompt_parts.append(f"- 新手提示：{ui.hints}")

        # 美术风格指导
        if game_logic_result.art:
            prompt_parts.append("\n🎨 美术风格指导：")
            art = game_logic_result.art
            prompt_parts.append(f"- 主题风格：{art.theme}")
            prompt_parts.append(f"- 画风类型：{art.artStyle}")
            prompt_parts.append(f"- 色彩搭配：{', '.join(art.colorPalette)}")
            prompt_parts.append(f"- 精灵尺寸：{art.spriteScale}")

            if art.requiredAssets:
                prompt_parts.append("- 必需资源：")
                for asset in art.requiredAssets:
                    frames_info = f" ({asset.frames}帧)" if asset.frames else ""
                    prompt_parts.append(f"  • {asset.name} ({asset.type}){frames_info}: {asset.notes}")

        # 音效配置
        if game_logic_result.audio:
            prompt_parts.append("\n🔊 音效配置：")
            audio = game_logic_result.audio
            prompt_parts.append(f"- 背景音乐：{audio.bgm.mood}风格, 循环播放: {audio.bgm.loop}")
            if audio.sfx:
                prompt_parts.append("- 音效事件：")
                for sfx in audio.sfx:
                    prompt_parts.append(f"  • {sfx.event}: {sfx.desc}")

        # 特效要求
        if game_logic_result.fx:
            prompt_parts.append("\n✨ 特效要求：")
            fx = game_logic_result.fx
            if fx.particles:
                prompt_parts.append(f"- 粒子效果：{', '.join(fx.particles)}")
            if fx.tweens:
                prompt_parts.append(f"- 动画过渡：{', '.join(fx.tweens)}")
            prompt_parts.append(f"- 推荐特效：{fx.recommended}")

        # 技术规格
        if game_logic_result.meta:
            prompt_parts.append("\n⚙️ 技术规格：")
            meta = game_logic_result.meta
            prompt_parts.append(f"- 预计游戏时长：{meta.estimatedPlayTime}")
            prompt_parts.append(f"- 移动端优化：{meta.mobileOptimized}")
            prompt_parts.append(f"- 推荐画布尺寸：{meta.recommendedCanvasSize[0]}x{meta.recommendedCanvasSize[1]}")

        # 核心机制（如果有）
        if game_logic_result.core_mechanics:
            prompt_parts.append(f"\n🔧 核心机制：{', '.join(game_logic_result.core_mechanics)}")

        # 开发注意事项
        if game_logic_result.notes_for_dev:
            prompt_parts.append(f"\n📋 开发注意事项：{game_logic_result.notes_for_dev}")

        # 用户需求
        prompt_parts.append(f"\n💡 用户原始需求：{context.user_prompt}")

        # 开发指导意见（如果有）- 放在最显眼的位置
        if hasattr(context.game_logic, 'dev_guidance') and context.game_logic.dev_guidance:
            prompt_parts.append("\n" + "=" * 60)
            prompt_parts.append("🔴🔴🔴 开发指导意见（必须遵循！）🔴🔴🔴")
            prompt_parts.append("=" * 60)
            prompt_parts.append(context.game_logic.dev_guidance)
            prompt_parts.append("=" * 60)
            prompt_parts.append("\n⚠️ 请务必按照上述开发指导意见实现代码！")
            prompt_parts.append("⚠️ 特别是API推荐和技术栈的选择，必须严格遵守！")
            prompt_parts.append("=" * 60)

        # 实现要求
        prompt_parts.append("\n🚀 实现要求：")
        prompt_parts.append("- 严格按照上述设计规格实现")
        prompt_parts.append("- 确保所有specified的UI元素都被实现")
        prompt_parts.append("- 色彩搭配必须使用指定的调色板")
        prompt_parts.append("- 特效和动画要与游戏风格保持一致")
        prompt_parts.append("- 代码质量高，注释清晰，可直接运行")
        prompt_parts.append("- 如果有开发指导意见，必须严格遵循指定的API和框架！")

        return "\n".join(prompt_parts)

    def _build_legacy_prompt(self, game_logic_result, context: GameContext) -> str:
        """传统提示词构建（向后兼容）"""
        enhanced_prompt = f"""请基于以下游戏设计生成完整的HTML、CSS、JavaScript代码：

            游戏名称：{game_logic_result.title}
            游戏类型：{game_logic_result.game_type}
            核心玩法：{game_logic_result.game_logic}
            游戏描述：{game_logic_result.description}"""

        # 添加推断的游戏特征信息
        if context.game_features:
            enhanced_prompt += "\n\n游戏特征分析："
            if context.game_features.visual_style:
                enhanced_prompt += f"\n- 视觉风格：{context.game_features.visual_style}"
            if context.game_features.complexity:
                enhanced_prompt += f"\n- 复杂度：{context.game_features.complexity}"
            if context.game_features.game_elements:
                enhanced_prompt += f"\n- 游戏元素：{', '.join(context.game_features.game_elements)}"
            if context.game_features.interaction_types:
                enhanced_prompt += f"\n- 交互类型：{', '.join(context.game_features.interaction_types)}"

        # 添加用户原始需求
        enhanced_prompt += f"\n\n用户原始需求：{context.user_prompt}"
        enhanced_prompt += "\n\n请生成完整可运行的代码文件，确保代码质量和用户体验。"

        return enhanced_prompt
    
    async def process(self, context: GameContext, session_id: str = None) -> GameContext:
        """处理游戏文件生成"""
        logger.info(f"📄 {self.agent_name}: 开始生成游戏文件...")

        try:
            # 构建增强提示词
            enhanced_prompt = self.build_enhanced_prompt(context)
            logger.info(f"🔧 增强提示词长度: {len(enhanced_prompt)}")

            # RAG检索增强（如果启用）
            rag_context = ""
            if self.enable_rag and self.rag_service:
                logger.info("🔍 FileGenerateAgent: 开始RAG检索相关实现示例...")
                try:
                    # 构建检索查询：结合游戏类型和技术栈
                    game_type = context.game_logic.game_type if context.game_logic else "游戏"
                    search_query = f"{game_type} HTML5 Canvas JavaScript 实现代码示例"

                    # 如果GameLogicAgent有指导意见，也加入查询
                    if hasattr(context.game_logic, 'dev_guidance') and context.game_logic.dev_guidance:
                        search_query += f" {context.game_logic.dev_guidance}"

                    logger.info(f"🔍 RAG查询: {search_query[:100]}...")

                    # 执行检索
                    rag_results = self.rag_service.retrieve_for_context(
                        query=search_query,
                        n_results=3
                    )

                    if rag_results:
                        rag_context = f"\n\n=== 参考实现和API文档 ===\n{rag_results}\n"
                        logger.info(f"✅ FileGenerateAgent: RAG检索成功，获得 {len(rag_results)} 字符的参考内容")
                    else:
                        logger.info("ℹ️  FileGenerateAgent: 未检索到相关内容")

                except Exception as e:
                    logger.warning(f"⚠️  FileGenerateAgent: RAG检索失败: {str(e)}")

            # 将RAG上下文添加到增强提示词
            final_prompt = enhanced_prompt + rag_context

            # 将增强提示词保存到上下文中（用于后续保存到数据库）
            context.enhanced_prompt = enhanced_prompt

            # 调用AI生成游戏文件（注意：不传递 previous_chat_id，因为我们不希望保存这个agent的历史）
            print("file enhanced_prompt",final_prompt[:500])
            response = await self.ai_client.get_game_files(
                self.system_message,
                final_prompt
            )
            print("file",response)

            logger.info(f"📄 {self.agent_name} 响应长度: {len(response['content'])}")

            # 收集usage统计
            if response.get('usage'):
                self.add_usage_stats(context, response['usage'])

            # 解析响应
            files_data = self.extract_json_code_block(response["content"])

            # 创建游戏文件（只包含HTML）
            game_files = GameFiles(
                html=files_data["html"]
            )
            
            # 更新上下文
            context.files = game_files
            context = self.update_context(context)
            
            logger.info(f"✅ {self.agent_name}: 游戏文件生成完成")
            logger.info(f"📊 HTML文件大小: {len(game_files.html)} 字符")
            
            return context
            
        except Exception as e:
            logger.error(f"❌ {self.agent_name}: 处理失败 - {str(e)}")
            raise Exception(f"游戏文件生成失败: {str(e)}")