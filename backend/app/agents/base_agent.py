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
        """从markdown中提取JSON代码块

        兼容两种情况：
        1. 标准 ```json ... ``` 代码块
        2. 直接返回的纯 JSON 文本（如 Kimi 返回的就是纯 JSON）
        """
        # 优先解析 ```json``` 代码块
        match = re.search(r'```json\s*([\s\S]*?)\s*```', markdown)
        if match:
            json_str = match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {json_str}")
                raise ValueError(f"JSON格式错误: {str(e)}")

        # 如果没有代码块，尝试整体解析为 JSON
        text = markdown.strip()
        # 简单保护：必须至少以 { 开头，以 } 结尾才尝试
        if text.startswith("{") and text.endswith("}"):
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败(纯文本): {text[:2000]}...")

                # 针对常见的小错误做一次“自愈”处理（例如字符串里包含未转义的引号）
                # 目前已知 Kimi 有时会在说明文字里写出类似：得分数字 "+10" 向上渐隐...
                # 这种行直接删掉字段影响不大，可以先移除再尝试一次
                lines = text.splitlines()
                sanitized_lines = [
                    line for line in lines
                    if '"recommended"' not in line  # 删除有问题的 recommended 行
                ]
                sanitized = "\n".join(sanitized_lines)
                try:
                    return json.loads(sanitized)
                except json.JSONDecodeError:
                    # 仍然失败就交给后面的通用兜底逻辑
                    logger.error("JSON自愈失败，继续尝试其他解析方式")

        # 再尝试从文本中提取第一个大括号块
        obj_match = re.search(r'\{[\s\S]*\}', markdown)
        if obj_match:
            candidate = obj_match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                logger.error(f"JSON解析失败(大括号提取): {candidate[:2000]}...")

        raise ValueError("未找到 JSON 代码块，也无法从文本中解析 JSON")

    def extract_html_file_block(self, markdown: str) -> Dict[str, Any]:
        """从 AI 响应中提取 HTML 游戏文件内容

        FileGenerateAgent 期望格式为 {"html": "..."}，但 Kimi 等模型可能返回：
        1. ```json {"html": "..."} ```
        2. ```html <!DOCTYPE html>... ```
        3. 纯 HTML 文本（<!DOCTYPE 或 <html 开头）
        """
        # 1. 先尝试标准 JSON 解析（含 {"html":"..."}）
        try:
            data = self.extract_json_code_block(markdown)
            if isinstance(data, dict) and "html" in data:
                return data
        except ValueError:
            pass

        # 2. 尝试 ```html ... ``` 代码块
        html_match = re.search(r'```html\s*([\s\S]*?)\s*```', markdown, re.IGNORECASE)
        if html_match:
            return {"html": html_match.group(1).strip()}

        # 3. 纯 HTML 文本（以 DOCTYPE 或 <html 开头）
        text = markdown.strip()
        if text.upper().startswith("<!DOCTYPE") or text.lower().startswith("<html"):
            return {"html": text}

        raise ValueError("未找到 JSON 代码块或 HTML 代码块，无法解析游戏文件")
    
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