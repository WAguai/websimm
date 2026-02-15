from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from .game_models import GameLogicResult, GameFiles


class GameFeatures(BaseModel):
    visual_style: Optional[str] = None
    complexity: Optional[str] = None
    game_elements: Optional[List[str]] = None
    interaction_types: Optional[List[str]] = None


class ContextMetadata(BaseModel):
    timestamp: datetime = datetime.now()
    agent_chain: List[str] = []
    version: str = "1.0"
    usage_stats: Optional[Dict[str, Dict[str, Any]]] = None  # 各Agent的token使用统计

    def add_usage_stats(self, agent_name: str, usage: Dict[str, Any]):
        """添加Agent的token使用统计"""
        if not self.usage_stats:
            self.usage_stats = {}
        self.usage_stats[agent_name] = usage


class GameContext(BaseModel):
    user_prompt: str
    game_logic: Optional[GameLogicResult] = None
    game_features: Optional[GameFeatures] = None
    image_resources: Optional[List[str]] = None
    audio_resources: Optional[List[str]] = None
    files: Optional[GameFiles] = None
    metadata: Optional[ContextMetadata] = None
    enhanced_prompt: Optional[str] = None  # FileGenerateAgent 的增强提示词
    rag_enhanced_prompt: Optional[str] = None  # RAG Agent 检索到的API文档
    
    def add_to_chain(self, agent_name: str):
        """添加agent到执行链中"""
        if not self.metadata:
            self.metadata = ContextMetadata()
        self.metadata.agent_chain.append(agent_name)