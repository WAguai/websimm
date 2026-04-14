import logging
from typing import Any, Dict, List

from .base_agent import BaseAgent
from .skills import SkillRegistry
from ..models.context_models import GameContext
from ..models.context_models import ContextMetadata

logger = logging.getLogger(__name__)


class ReviewAgent(BaseAgent):
    """审查/整合Agent：校验可运行性、完整性和需求匹配"""

    def __init__(self):
        super().__init__("ReviewAgent")
        self.skills = SkillRegistry()

    @property
    def system_message(self) -> str:
        return (
            "你是ReviewAgent，负责校验HTML结构、JS主循环、资源引用和需求匹配，"
            "输出严格JSON：{status, issues, suggestions}。"
        )

    async def process(self, context: GameContext, session_id: str = None) -> GameContext:
        issues: List[str] = []
        suggestions: List[str] = []

        if not context.game_logic:
            issues.append("logic_spec missing")
        if not context.files or not context.files.html:
            issues.append("html_code missing")
        if not context.image_resources:
            issues.append("asset manifest missing")
        if not context.audio_resources:
            issues.append("audio manifest missing")

        skill_validation = self.skills.validate_for_capability("game_code_generation", context)
        if not skill_validation.get("html_valid"):
            issues.append("html structure invalid")
            suggestions.append("调用 generate_html_template skill 修复基础结构")
        if not skill_validation.get("gameplay_loop_valid"):
            issues.append("main loop missing")
            suggestions.append("调用 inject_game_loop skill 补全主循环")
        if not skill_validation.get("js_syntax_valid"):
            issues.append("javascript syntax suspicious")
            suggestions.append("调用 validate_js_syntax skill 逐段校验脚本")

        review_report: Dict[str, Any] = {
            "status": "pass" if not issues else "fail",
            "issues": issues,
            "suggestions": suggestions,
        }

        if not context.metadata:
            context.metadata = ContextMetadata()
        context.metadata.review_report = review_report
        context = self.update_context(context)
        logger.info(f"🧪 ReviewAgent: {review_report['status']} issues={len(issues)}")
        return context

