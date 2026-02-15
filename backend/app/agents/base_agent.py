from abc import ABC, abstractmethod
from typing import Any, Dict
from ..services.ai_client import ai_client
from ..models.context_models import GameContext
import json
import re
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """基础Agent类，提供通用功能"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.ai_client = ai_client
    
    def extract_json_code_block(self, markdown: str) -> Dict[str, Any]:
        """从markdown中提取JSON代码块"""
        match = re.search(r'```json\s*([\s\S]*?)\s*```', markdown)
        if not match:
            raise ValueError("未找到 JSON 代码块")
        
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {json_str}")
            raise ValueError(f"JSON格式错误: {str(e)}")
    
    def update_context(self, context: GameContext) -> GameContext:
        """更新上下文，添加当前agent到执行链"""
        context.add_to_chain(self.agent_name)
        return context

    def add_usage_stats(self, context: GameContext, usage: Dict[str, Any]):
        """添加当前Agent的token使用统计"""
        if not context.metadata:
            from ..models.context_models import ContextMetadata
            context.metadata = ContextMetadata()
        if usage:
            context.metadata.add_usage_stats(self.agent_name, usage)
    
    @abstractmethod
    async def process(self, context: GameContext, session_id: str = None) -> GameContext:
        """处理逻辑，子类必须实现"""
        pass
    
    @property
    @abstractmethod
    def system_message(self) -> str:
        """系统提示词，子类必须实现"""
        pass