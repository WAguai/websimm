import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from ..agents.audio_resource_agent import AudioResourceAgent
from ..agents.file_generate_agent import FileGenerateAgent
from ..agents.game_logic_agent import GameLogicAgent
from ..agents.image_resource_agent import ImageResourceAgent
from ..agents.orchestrator_agent import OrchestratorAgent
from ..agents.rag_agent import RAGAgent
from ..agents.review_agent import ReviewAgent
from ..agents.skills import SkillRegistry
from ..models.context_models import GameContext

logger = logging.getLogger(__name__)


class DAGExecutionEngine:
    """DAG任务执行引擎：支持并行、失败重试与重规划"""

    def __init__(
        self,
        orchestrator: OrchestratorAgent,
        game_logic_agent: GameLogicAgent,
        game_code_agent: FileGenerateAgent,
        asset_agent: ImageResourceAgent,
        audio_agent: AudioResourceAgent,
        review_agent: ReviewAgent,
        rag_agent: Optional[RAGAgent] = None,
        max_retries: int = 2,
        max_replans: int = 2,
    ):
        self.orchestrator = orchestrator
        self.game_logic_agent = game_logic_agent
        self.game_code_agent = game_code_agent
        self.asset_agent = asset_agent
        self.audio_agent = audio_agent
        self.review_agent = review_agent
        self.rag_agent = rag_agent
        self.max_retries = max_retries
        self.max_replans = max_replans
        self.skills = SkillRegistry()

    async def execute(
        self,
        context: GameContext,
        plan: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> GameContext:
        tasks = {task["task_id"]: dict(task) for task in plan.get("tasks", [])}
        if not tasks:
            raise ValueError("ExecutionPlan为空，无法执行")

        if not context.metadata:
            raise ValueError("GameContext.metadata 未初始化")

        context.metadata.plan = list(tasks.values())
        status = context.metadata.task_status
        context.task_states = status
        for task_id in tasks:
            status.setdefault(task_id, {"status": "pending", "attempt": 0, "issues": []})

        while True:
            pending_ids = [task_id for task_id, s in status.items() if s["status"] == "pending"]
            if not pending_ids:
                break

            ready_ids = self._get_ready_task_ids(pending_ids, tasks, status)
            if not ready_ids:
                failed = [tid for tid, s in status.items() if s["status"] == "failed"]
                if not failed:
                    raise RuntimeError("DAG死锁：存在pending任务但无可执行节点")
                await self._do_replan(context, plan, tasks, status, failed, ["dependency failed"])
                continue

            ready_tasks = [tasks[task_id] for task_id in ready_ids]
            parallel_tasks = [task for task in ready_tasks if task.get("parallelizable")]
            sequential_tasks = [task for task in ready_tasks if not task.get("parallelizable")]

            if parallel_tasks:
                await asyncio.gather(
                    *(self._execute_one_task(task, context, status, session_id) for task in parallel_tasks)
                )
            for task in sequential_tasks:
                await self._execute_one_task(task, context, status, session_id)

            review_failed_task = self._find_failed_review_task(tasks, status)
            hard_failed = [tid for tid, s in status.items() if s["status"] == "failed"]
            if review_failed_task or hard_failed:
                issues = []
                if review_failed_task:
                    report = context.metadata.review_report or {}
                    issues.extend(report.get("issues", []))
                await self._do_replan(context, plan, tasks, status, hard_failed, issues or ["task failed"])

        return context

    def _get_ready_task_ids(
        self,
        pending_ids: List[str],
        tasks: Dict[str, Dict[str, Any]],
        status: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        ready = []
        for task_id in pending_ids:
            depends_on = tasks[task_id].get("depends_on", [])
            if all(status.get(dep, {}).get("status") == "success" for dep in depends_on):
                ready.append(task_id)
        return ready

    async def _execute_one_task(
        self,
        task: Dict[str, Any],
        context: GameContext,
        status: Dict[str, Dict[str, Any]],
        session_id: Optional[str],
    ) -> None:
        task_id = task["task_id"]
        capability = task["capability"]
        record = status[task_id]
        record["status"] = "running"
        record["attempt"] += 1
        context.append_execution_log(
            {"task_id": task_id, "capability": capability, "event": "running", "attempt": record["attempt"]}
        )

        try:
            self._apply_skill_guidance(capability, context)
            await self._dispatch_task(capability, context, session_id)
            accepted, issues = self._check_acceptance(capability, context)
            if not accepted:
                raise ValueError("; ".join(issues))

            record["status"] = "success"
            record["issues"] = []
            context.append_execution_log(
                {"task_id": task_id, "capability": capability, "event": "success"}
            )
        except Exception as e:
            record["issues"] = [str(e)]
            if record["attempt"] <= self.max_retries:
                logger.warning(f"⚠️ 任务重试: {task_id} attempt={record['attempt']} error={e}")
                record["status"] = "pending"
                context.append_execution_log(
                    {"task_id": task_id, "capability": capability, "event": "retry", "error": str(e)}
                )
            else:
                record["status"] = "failed"
                logger.error(f"❌ 任务失败: {task_id} error={e}")
                context.append_execution_log(
                    {"task_id": task_id, "capability": capability, "event": "failed", "error": str(e)}
                )

    def _apply_skill_guidance(self, capability: str, context: GameContext) -> None:
        guidance = self.skills.get_guidance_for_capability(capability, context)
        if not guidance:
            return

        context.write_artifact(
            name="skills_guidance",
            producer="SkillRegistry",
            content=guidance,
            status="validated",
        )
        if capability == "game_code_generation":
            base_prompt_artifact = context.read_artifact("original_user_prompt")
            base_prompt = (
                base_prompt_artifact.content
                if base_prompt_artifact
                else context.user_prompt
            )
            context.user_prompt = (
                f"{base_prompt}\n\n=== Skills Guidance ===\n- " + "\n- ".join(guidance)
            )

    async def _dispatch_task(self, capability: str, context: GameContext, session_id: Optional[str]) -> None:
        if capability == "retrieve_reference_context":
            if not self.rag_agent:
                context.write_artifact(
                    name="reference_context",
                    producer="RAGAgent",
                    content="",
                    status="rejected",
                )
                return
            rag_text = await self.rag_agent.retrieve_for_prompt(context.user_prompt, n_results=3)
            context.rag_enhanced_prompt = rag_text
            context.write_artifact(
                name="reference_context",
                producer="RAGAgent",
                content=rag_text,
                status="validated" if rag_text else "rejected",
            )
            context.add_to_chain("RAGAgent")
            return

        if capability == "game_logic_generation":
            base_prompt_artifact = context.read_artifact("original_user_prompt")
            base_prompt = (
                base_prompt_artifact.content
                if base_prompt_artifact
                else context.user_prompt
            )
            rag_artifact = context.read_artifact("reference_context")
            rag_text = (
                rag_artifact.content
                if rag_artifact and rag_artifact.content
                else context.rag_enhanced_prompt
            )
            if rag_text:
                context.user_prompt = (
                    f"{base_prompt}\n\n{rag_text}\n\n请基于以上上下文生成完整逻辑。"
                )
            else:
                context.user_prompt = base_prompt
            await self.game_logic_agent.process(context, session_id)
            if context.game_logic:
                context.write_artifact(
                    name="logic_spec",
                    producer="GameLogicAgent",
                    content=context.game_logic.model_dump() if hasattr(context.game_logic, "model_dump") else context.game_logic,
                    status="validated",
                )
            return

        if capability == "game_code_generation":
            await self.game_code_agent.process(context, session_id)
            if context.files:
                context.write_artifact(
                    name="html_code",
                    producer="GameCodeAgent",
                    content=context.files.html,
                    status="validated",
                )
            return

        if capability == "asset_generation":
            await self.asset_agent.process(context, session_id)
            context.write_artifact(
                name="asset_manifest",
                producer="AssetAgent",
                content=context.image_resources or [],
                status="validated" if context.image_resources else "rejected",
            )
            return

        if capability == "audio_generation":
            await self.audio_agent.process(context, session_id)
            context.write_artifact(
                name="audio_manifest",
                producer="AudioAgent",
                content=context.audio_resources or [],
                status="validated" if context.audio_resources else "rejected",
            )
            return

        if capability == "review_and_validate":
            await self.review_agent.process(context, session_id)
            context.write_artifact(
                name="review_report",
                producer="ReviewAgent",
                content=context.metadata.review_report if context.metadata else {},
                status="final" if context.metadata and context.metadata.review_report and context.metadata.review_report.get("status") == "pass" else "rejected",
            )
            if context.metadata and context.metadata.review_report:
                context.review_reports.append(context.metadata.review_report)
            return

        raise ValueError(f"未知 capability: {capability}")

    def _check_acceptance(self, capability: str, context: GameContext) -> Tuple[bool, List[str]]:
        issues: List[str] = []
        if capability == "retrieve_reference_context":
            return True, []
        if capability == "game_logic_generation":
            if not context.game_logic or not context.game_logic.game_logic:
                issues.append("logic_complete")
        elif capability == "game_code_generation":
            if not context.files or not context.files.html:
                issues.append("code_generated")
            validators = self.skills.validate_for_capability("game_code_generation", context)
            if not validators.get("html_valid"):
                issues.append("html_structure_valid")
        elif capability == "asset_generation":
            if not context.image_resources:
                issues.append("assets_ready")
        elif capability == "audio_generation":
            if not context.audio_resources:
                issues.append("audio_ready")
        elif capability == "review_and_validate":
            report = context.metadata.review_report if context.metadata else None
            if not report or report.get("status") != "pass":
                issues.append("review_passed")
        return len(issues) == 0, issues

    async def _do_replan(
        self,
        context: GameContext,
        original_plan: Dict[str, Any],
        tasks: Dict[str, Dict[str, Any]],
        status: Dict[str, Dict[str, Any]],
        failed_task_ids: List[str],
        issues: List[str],
    ) -> None:
        if not failed_task_ids:
            return
        if context.metadata.replan_count >= self.max_replans:
            raise RuntimeError(
                f"重规划次数超过上限({self.max_replans})，最后错误: {issues[:3]}"
            )

        blocked = self._collect_downstream_tasks(tasks, failed_task_ids)
        replan = self.orchestrator.replan(
            current_plan=original_plan,
            failed_task_ids=failed_task_ids,
            blocked_task_ids=blocked,
            issues=issues,
        )
        replan_ids = {task["task_id"] for task in replan.get("tasks", [])}
        if not replan_ids:
            raise RuntimeError("replan未返回可执行任务")

        for task_id in replan_ids:
            if task_id in status:
                status[task_id]["status"] = "pending"
                status[task_id]["issues"] = []
                status[task_id]["attempt"] = 0

        context.metadata.replan_count += 1
        logger.warning(
            f"🔁 触发Replan #{context.metadata.replan_count}, tasks={sorted(list(replan_ids))}"
        )

    def _collect_downstream_tasks(
        self,
        tasks: Dict[str, Dict[str, Any]],
        failed_task_ids: List[str],
    ) -> List[str]:
        downstream: Set[str] = set()
        queue = list(failed_task_ids)
        while queue:
            current = queue.pop(0)
            for task_id, task in tasks.items():
                if current in task.get("depends_on", []) and task_id not in downstream:
                    downstream.add(task_id)
                    queue.append(task_id)
        return list(downstream)

    def _find_failed_review_task(
        self,
        tasks: Dict[str, Dict[str, Any]],
        status: Dict[str, Dict[str, Any]],
    ) -> Optional[str]:
        for task_id, task in tasks.items():
            if task["capability"] == "review_and_validate":
                if status.get(task_id, {}).get("status") == "failed":
                    return task_id
        return None

