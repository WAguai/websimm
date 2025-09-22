from .base_agent import BaseAgent
from ..models.context_models import GameContext
from ..models.game_models import GameFiles
import logging

logger = logging.getLogger(__name__)


class FileGenerateAgent(BaseAgent):
    def __init__(self):
        super().__init__("FileGenerateAgent")
    
    @property
    def system_message(self) -> str:
        return """
-角色：
  你是一位专业的前端开发工程师，擅长将游戏设计转化为可运行的HTML5网页游戏代码。
  用户将向你提供游戏的设计文档，包括游戏名称、类型、核心玩法和描述。
  你的任务是基于这些信息，生成一个包含所有代码的完整HTML文件。
  请按照以下格式输出结构化的代码文件：

-输出格式如下,不要有多余的参数：
  {
    "html": "完整的HTML文件内容，包含内嵌的CSS样式和JavaScript代码"
  }

-技术要求：
  1. 生成一个完整的HTML文件，包含DOCTYPE、html、head、body等完整结构
  2. CSS样式直接写在<style>标签内，包含游戏界面样式、动画效果、响应式设计等
  3. JavaScript代码直接写在<script>标签内，包含游戏循环、事件处理、碰撞检测等核心功能
  4. 使用Canvas API进行游戏渲染
  5. 实现基本的游戏循环（update/render）
  6. 添加键盘/鼠标事件处理
  7. 包含得分系统和游戏状态管理
  8. 代码应该是可直接在浏览器中打开运行的完整实现
  9. 使用现代JavaScript语法（ES6+）
  10. 确保代码具有良好的可读性和注释
  11. 文件应该是自包含的，不依赖外部资源

-HTML结构示例：
  ```html
  <!DOCTYPE html>
  <html lang="zh-CN">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>游戏标题</title>
      <style>
          /* 所有CSS样式 */
      </style>
  </head>
  <body>
      <!-- 游戏界面HTML -->
      <script>
          // 所有JavaScript代码
      </script>
  </body>
  </html>
  ```

-备注：
  请确保输出结构完全符合上述JSON格式，字段命名准确。
  生成的HTML文件应该是完整可运行的，不要使用占位符或TODO注释。
  用户可以直接保存为.html文件并在浏览器中打开运行。
"""
    
    def build_enhanced_prompt(self, context: GameContext) -> str:
        """构建增强的提示词"""
        if not context.game_logic:
            raise ValueError('GameLogic 结果不存在，无法生成游戏文件')
        
        game_logic_result = context.game_logic
        
        # 构建基础提示词
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

            # 调用AI生成游戏文件（注意：不传递 previous_chat_id，因为我们不希望保存这个agent的历史）
            response = await self.ai_client.get_game_files(
                self.system_message,
                enhanced_prompt
            )
            print("file",response)

            logger.info(f"📄 {self.agent_name} 响应长度: {len(response['content'])}")

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