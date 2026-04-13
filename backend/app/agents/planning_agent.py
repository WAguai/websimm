from .base_agent import BaseAgent
from ..models.context_models import GameContext
import logging

logger = logging.getLogger(__name__)


class PlanningAgent(BaseAgent):
    """
    PlanningAgent - 使用 ReAct / Plan-and-Execute 思路，
    在真正调用其他 Agent 之前先生成执行计划。
    """

    def __init__(self):
        super().__init__("PlanningAgent")

    @property
    def system_message(self) -> str:
        return """
你是一个高级规划 Agent，负责为后续的游戏生成多 Agent 流程设计执行计划。

请基于用户的游戏需求，使用 ReAct（Thought / Action / Observation）风格先思考再给出 JSON 计划：

1. 先在心里思考（你可以在reasoning字段里简要说明），但最终输出必须是一个 JSON 代码块。
2. JSON 中列出将要调用的 Agent 列表和顺序，以及每一步的目的。
3. 如果任务简单，可以关闭部分 Agent（例如关闭 RAG 或资源生成）。

输出格式示例（严格 JSON）：
```json
{
  "reasoning": "先用RAG补充API知识，再设计游戏逻辑，最后生成代码和资源。",
  "steps": [
    {"agent": "RAGAgent", "enabled": true, "purpose": "检索与游戏相关的Phaser/Canvas API文档"},
    {"agent": "GameLogicAgent", "enabled": true, "purpose": "设计完整的游戏玩法与配置JSON"},
    {"agent": "FileGenerateAgent", "enabled": true, "purpose": "基于逻辑与RAG结果生成HTML5游戏代码"},
    {"agent": "ImageResourceAgent", "enabled": true, "purpose": "生成（或占位）图片资源列表"},
    {"agent": "AudioResourceAgent", "enabled": true, "purpose": "生成（或占位）音频资源列表"}
  ]
}
```

注意：
- 必须输出一个合法的 JSON 代码块（使用```json ... ```包裹）。
- steps.agent 字段必须使用现有 Agent 名称：RAGAgent, GameLogicAgent, FileGenerateAgent, ImageResourceAgent, AudioResourceAgent。
- enabled 可以根据任务复杂度选择 true/false。
"""

    async def process(self, context: GameContext, session_id: str = None) -> GameContext:
        """生成执行计划并写入 context.metadata.plan"""
        logger.info(f"🧠 {self.agent_name}: 开始规划执行链...")

        try:
            response = await self.ai_client.chat_completion(
                system_message=self.system_message,
                user_message=context.user_prompt,
                model=context.model,
                previous_chat_id=session_id,
                agent_name=self.agent_name,
                use_streaming=False,
            )

            # 提取 JSON 计划
            plan_data = self.extract_json_code_block(response["content"])
            steps = plan_data.get("steps", [])

            if not context.metadata:
                from ..models.context_models import ContextMetadata

                context.metadata = ContextMetadata()

            context.metadata.plan = steps
            context = self.update_context(context)

            logger.info(f"✅ {self.agent_name}: 规划完成，步骤数: {len(steps)}")
            return context

        except Exception as e:
            logger.warning(f"⚠️ {self.agent_name}: 规划失败，继续使用默认执行链: {e}")
            # 即使规划失败，也不影响后续默认流程
            return self.update_context(context)

