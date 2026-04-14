import re
from typing import Dict, Any, List

from ..models.context_models import GameContext


class SkillRegistry:
    """可复用技能注册表：为关键任务提供模板与校验能力"""

    def get_guidance_for_capability(self, capability: str, context: GameContext) -> List[str]:
        guidance: List[str] = []
        if capability == "game_code_generation":
            guidance.extend(
                [
                    self.generate_html_template(),
                    self.inject_game_loop(),
                    self.build_collision_system(),
                    self.create_score_system(),
                ]
            )
        return guidance

    def validate_for_capability(self, capability: str, context: GameContext) -> Dict[str, Any]:
        if capability == "game_code_generation":
            return {
                "html_valid": self.validate_html(context),
                "gameplay_loop_valid": self.validate_gameplay_loop(context),
                "js_syntax_valid": self.validate_js_syntax(context),
            }
        return {"ok": True}

    # -----------------------------
    # Code-related skills
    # -----------------------------
    def generate_html_template(self) -> str:
        return (
            "Skill: generate_html_template -> 产物必须含DOCTYPE/html/head/body/canvas/script完整结构。"
        )

    def inject_game_loop(self) -> str:
        return (
            "Skill: inject_game_loop -> 必须实现稳定主循环（requestAnimationFrame或框架update生命周期）。"
        )

    def build_collision_system(self) -> str:
        return (
            "Skill: build_collision_system -> 碰撞检测需含边界检查，避免NaN和越界。"
        )

    def create_score_system(self) -> str:
        return (
            "Skill: create_score_system -> 提供实时分数更新、展示与胜负逻辑联动。"
        )

    # -----------------------------
    # Validation skills
    # -----------------------------
    def validate_html(self, context: GameContext) -> bool:
        html = context.files.html if context.files else ""
        checks = ["<!DOCTYPE", "<html", "<head", "<body", "<script"]
        return bool(html) and all(token.lower() in html.lower() for token in checks)

    def validate_gameplay_loop(self, context: GameContext) -> bool:
        html = context.files.html if context.files else ""
        logic = context.game_logic.game_logic.lower() if context.game_logic else ""
        has_loop_code = "requestanimationframe" in html.lower() or "new Phaser.Game".lower() in html.lower()
        has_loop_logic = "循环" in logic or "loop" in logic
        return has_loop_code and has_loop_logic

    def validate_js_syntax(self, context: GameContext) -> bool:
        """轻量语法检查：括号和关键字完整性（非完整AST解析）"""
        html = context.files.html if context.files else ""
        script_blocks = re.findall(
            r"<script[^>]*>([\s\S]*?)</script>",
            html,
            flags=re.IGNORECASE,
        )
        if not script_blocks:
            return False
        js_code = "\n".join(script_blocks)
        has_function_shape = ("function" in js_code) or ("=>" in js_code)
        return js_code.count("{") == js_code.count("}") and has_function_shape

