import logging
from typing import Any, Dict, List, Optional, Set

from .base_agent import BaseAgent
from .capabilities import CAPABILITY_SPECS
from ..models.context_models import GameContext

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """主调度Agent：负责规划、重规划和调度策略决策"""

    def __init__(self, enable_rag: bool = True):
        super().__init__("OrchestratorAgent")
        self.enable_rag = enable_rag
        self.capability_by_name = {item["name"]: item for item in CAPABILITY_SPECS}

    @property
    def system_message(self) -> str:
        return (
            "你是多Agent系统的Orchestrator。基于用户需求输出严格JSON执行计划。"
            "计划必须是DAG，且每个任务包含task_id/capability/agent/depends_on/"
            "parallelizable/inputs/outputs/acceptance。"
        )

    async def process(self, context: GameContext, session_id: str = None) -> GameContext:
        """实现BaseAgent抽象方法：生成计划并回写到上下文"""
        execution_plan = await self.plan(context, session_id=session_id)
        context.plan = execution_plan
        if context.metadata:
            context.metadata.plan = execution_plan.get("tasks", [])
        context = self.update_context(context)
        return context

    async def plan(self, context: GameContext, session_id: Optional[str] = None) -> Dict[str, Any]:
        capabilities_json = {
            "capabilities": CAPABILITY_SPECS,
            "constraints": {
                "strategy": "dag",
                "must_include_review": True,
                "parallel_required": ["asset_generation", "audio_generation"],
                "max_task_count": 8,
            },
        }

        prompt = (
            f"用户需求:\n{context.user_prompt}\n\n"
            f"可用能力:\n{capabilities_json}\n\n"
            "请严格按给定 schema 输出，不要额外包裹 execution_plan 字段。"
        )
        try:
            capability_names = list(self.capability_by_name.keys())
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "execution_plan",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["goal", "strategy", "tasks"],
                        "properties": {
                            "goal": {"type": "string"},
                            "strategy": {"type": "string", "enum": ["dag"]},
                            "tasks": {
                                "type": "array",
                                "minItems": 1,
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": [
                                        "task_id",
                                        "capability",
                                        "agent",
                                        "depends_on",
                                        "parallelizable",
                                        "inputs",
                                        "outputs",
                                        "acceptance",
                                    ],
                                    "properties": {
                                        "task_id": {"type": "string"},
                                        "capability": {
                                            "type": "string",
                                            "enum": capability_names,
                                        },
                                        "agent": {"type": "string"},
                                        "depends_on": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "parallelizable": {"type": "boolean"},
                                        "inputs": {"type": "object"},
                                        "outputs": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "acceptance": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            }
            response = await self.ai_client.chat_completion(
                system_message=self.system_message,
                user_message=prompt,
                model=context.model,
                previous_chat_id=session_id,
                agent_name=self.agent_name,
                use_streaming=False,
                response_format=response_format,
            )
            plan = self.extract_json_code_block(response["content"])
            validated = self._normalize_and_validate_plan(plan)
            logger.info("✅ OrchestratorAgent: 动态规划完成")
            return validated
        except Exception as e:
            logger.warning(f"⚠️ 动态规划失败，使用兜底DAG: {e}")
            return self._fallback_plan(context.user_prompt)

    def replan(
        self,
        current_plan: Dict[str, Any],
        failed_task_ids: List[str],
        blocked_task_ids: List[str],
        issues: List[str],
    ) -> Dict[str, Any]:
        """只重规划失败节点及其依赖节点，保留成功产物"""
        tasks = current_plan.get("tasks", [])
        id_to_task = {task["task_id"]: task for task in tasks}

        impacted: Set[str] = set(failed_task_ids)
        for task_id in blocked_task_ids:
            impacted.add(task_id)
            task = id_to_task.get(task_id, {})
            impacted.update(task.get("depends_on", []))

        replan_tasks = []
        for task in tasks:
            if task["task_id"] in impacted:
                refreshed = dict(task)
                refreshed["replanned"] = True
                refreshed["replan_reason"] = issues[:3]
                replan_tasks.append(refreshed)

        logger.info(
            f"🔁 OrchestratorAgent: replan tasks={len(replan_tasks)} impacted={sorted(list(impacted))}"
        )
        return {
            "goal": current_plan.get("goal", "生成HTML5小游戏"),
            "strategy": "dag",
            "tasks": replan_tasks,
        }

    def _normalize_and_validate_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        tasks = plan.get("tasks", [])
        if not isinstance(tasks, list) or not tasks:
            raise ValueError("ExecutionPlan.tasks 为空")

        normalized = []
        task_ids = set()
        for index, task in enumerate(tasks):
            task_id = task.get("task_id") or f"t{index + 1}"
            capability = task.get("capability")
            if capability not in self.capability_by_name:
                raise ValueError(f"未知 capability: {capability}")

            default_agent = self.capability_by_name[capability]["default_agent"]
            norm = {
                "task_id": task_id,
                "capability": capability,
                "agent": task.get("agent") or default_agent,
                "depends_on": task.get("depends_on") or [],
                "parallelizable": bool(task.get("parallelizable", False)),
                "inputs": task.get("inputs") or {},
                "outputs": task.get("outputs") or self.capability_by_name[capability]["outputs"],
                "acceptance": task.get("acceptance") or self.capability_by_name[capability]["acceptance"],
            }
            task_ids.add(task_id)
            normalized.append(norm)

        has_review = any(t["capability"] == "review_and_validate" for t in normalized)
        if not has_review:
            normalized.append(
                {
                    "task_id": "t_review",
                    "capability": "review_and_validate",
                    "agent": "ReviewAgent",
                    "depends_on": [t["task_id"] for t in normalized if t["capability"] != "retrieve_reference_context"],
                    "parallelizable": False,
                    "inputs": {},
                    "outputs": ["review_report"],
                    "acceptance": ["review_passed"],
                }
            )

        if not self.enable_rag:
            normalized = [t for t in normalized if t["capability"] != "retrieve_reference_context"]
            for task in normalized:
                task["depends_on"] = [dep for dep in task["depends_on"] if dep in {n["task_id"] for n in normalized}]

        return {
            "goal": plan.get("goal", "生成一个HTML5小游戏"),
            "strategy": "dag",
            "tasks": normalized,
        }

    def _fallback_plan(self, prompt: str) -> Dict[str, Any]:
        tasks = []
        if self.enable_rag:
            tasks.append(
                {
                    "task_id": "t_rag",
                    "capability": "retrieve_reference_context",
                    "agent": "RAGAgent",
                    "depends_on": [],
                    "parallelizable": True,
                    "inputs": {"query": prompt},
                    "outputs": ["reference_context"],
                    "acceptance": ["reference_context_ready"],
                }
            )

        tasks.extend(
            [
                {
                    "task_id": "t_logic",
                    "capability": "game_logic_generation",
                    "agent": "GameLogicAgent",
                    "depends_on": [],
                    "parallelizable": False,
                    "inputs": {},
                    "outputs": ["logic_spec"],
                    "acceptance": ["logic_complete"],
                },
                {
                    "task_id": "t_code",
                    "capability": "game_code_generation",
                    "agent": "GameCodeAgent",
                    "depends_on": ["t_logic"],
                    "parallelizable": False,
                    "inputs": {},
                    "outputs": ["html_code"],
                    "acceptance": ["code_generated", "html_structure_valid"],
                },
                {
                    "task_id": "t_asset",
                    "capability": "asset_generation",
                    "agent": "AssetAgent",
                    "depends_on": ["t_logic"],
                    "parallelizable": True,
                    "inputs": {},
                    "outputs": ["image_manifest"],
                    "acceptance": ["assets_ready"],
                },
                {
                    "task_id": "t_audio",
                    "capability": "audio_generation",
                    "agent": "AudioAgent",
                    "depends_on": ["t_logic"],
                    "parallelizable": True,
                    "inputs": {},
                    "outputs": ["audio_manifest"],
                    "acceptance": ["audio_ready"],
                },
                {
                    "task_id": "t_review",
                    "capability": "review_and_validate",
                    "agent": "ReviewAgent",
                    "depends_on": ["t_code", "t_asset", "t_audio"],
                    "parallelizable": False,
                    "inputs": {},
                    "outputs": ["review_report"],
                    "acceptance": ["review_passed"],
                },
            ]
        )
        return {
            "goal": "生成一个HTML5小游戏",
            "strategy": "dag",
            "tasks": tasks,
        }

