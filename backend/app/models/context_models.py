from pydantic import BaseModel
from typing import List, Optional
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


class GameContext(BaseModel):
    user_prompt: str
    game_logic: Optional[GameLogicResult] = None
    game_features: Optional[GameFeatures] = None
    image_resources: Optional[List[str]] = None
    audio_resources: Optional[List[str]] = None
    files: Optional[GameFiles] = None
    metadata: Optional[ContextMetadata] = None
    
    def add_to_chain(self, agent_name: str):
        """添加agent到执行链中"""
        if not self.metadata:
            self.metadata = ContextMetadata()
        self.metadata.agent_chain.append(agent_name)