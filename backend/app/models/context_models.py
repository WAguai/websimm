from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .game_models import GameLogicResult, GameFiles


class GameFeatures(BaseModel):
    visual_style: Optional[str] = None
    complexity: Optional[str] = None
    game_elements: Optional[List[str]] = None
    interaction_types: Optional[List[str]] = None


class ContextMetadata(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_chain: List[str] = Field(default_factory=list)
    version: str = "1.0"
    usage_stats: Optional[Dict[str, Dict[str, Any]]] = None  # 各Agent的token使用统计
    plan: Optional[List[Dict[str, Any]]] = None  # PlanningAgent 生成的执行计划（ReAct / Plan-and-Execute）
    task_status: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # DAG任务执行状态
    review_report: Optional[Dict[str, Any]] = None  # ReviewAgent审查结果
    replan_count: int = 0

    def add_usage_stats(self, agent_name: str, usage: Dict[str, Any]):
        """添加Agent的token使用统计"""
        if not self.usage_stats:
            self.usage_stats = {}
        self.usage_stats[agent_name] = usage


class Artifact(BaseModel):
    name: str
    version: int = 1
    producer: str
    status: str = "draft"  # draft / validated / final / rejected
    content: Any
    created_at: datetime = Field(default_factory=datetime.now)


class GameContext(BaseModel):
    user_prompt: str
    model: Optional[str] = None  # 模型ID，如 kimi-k2-turbo-preview
    request: Dict[str, Any] = Field(default_factory=dict)  # 输入层
    plan: Optional[Dict[str, Any]] = None
    game_logic: Optional[GameLogicResult] = None
    game_features: Optional[GameFeatures] = None
    image_resources: Optional[List[str]] = None
    audio_resources: Optional[List[str]] = None
    files: Optional[GameFiles] = None
    metadata: Optional[ContextMetadata] = None
    enhanced_prompt: Optional[str] = None  # FileGenerateAgent 的增强提示词
    rag_enhanced_prompt: Optional[str] = None  # RAG Agent 检索到的API文档
    artifacts: Dict[str, Artifact] = Field(default_factory=dict)  # 中间/最终产物层
    task_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # 运行时元数据层
    review_reports: List[Dict[str, Any]] = Field(default_factory=list)
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)

    def add_to_chain(self, agent_name: str):
        """添加agent到执行链中"""
        if not self.metadata:
            self.metadata = ContextMetadata()
        self.metadata.agent_chain.append(agent_name)

    def read_artifact(self, name: str, version: Optional[int] = None) -> Optional[Artifact]:
        artifact = self.artifacts.get(name)
        if not artifact:
            return None
        if version is not None and artifact.version != version:
            return None
        return artifact

    def write_artifact(
        self,
        name: str,
        producer: str,
        content: Any,
        status: str = "draft",
    ) -> Artifact:
        old = self.artifacts.get(name)
        next_version = (old.version + 1) if old else 1
        artifact = Artifact(
            name=name,
            version=next_version,
            producer=producer,
            status=status,
            content=content,
        )
        self.artifacts[name] = artifact
        return artifact

    def mark_artifact_status(self, name: str, status: str) -> None:
        artifact = self.artifacts.get(name)
        if not artifact:
            return
        artifact.status = status

    def append_execution_log(self, event: Dict[str, Any]) -> None:
        self.execution_log.append({"timestamp": datetime.now().isoformat(), **event})