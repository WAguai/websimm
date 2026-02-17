from pydantic import BaseModel, Field, field_serializer
from typing import List, Optional, Dict, Any, Annotated
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler


class PyObjectId(str):
    """MongoDB ObjectId的Pydantic兼容版本 - 简化为字符串"""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic v2 schema定义"""
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.no_info_plain_validator_function(
                cls._validate,
                serialization=core_schema.plain_serializer_function_ser_schema(
                    lambda x: str(x)
                )
            ),
        ])

    @classmethod
    def _validate(cls, v):
        """验证ObjectId"""
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return v
            raise ValueError('Invalid ObjectId')
        raise ValueError('Invalid ObjectId type')




class GameData(BaseModel):
    """游戏数据 - 兼容新旧数据格式"""
    # ===== 向后兼容：保持原有基础字段 =====
    title: str = Field(..., description="游戏标题")
    game_type: str = Field(..., description="游戏类型")
    game_logic: str = Field(..., description="游戏逻辑")
    description: str = Field(..., description="游戏描述")
    html_content: str = Field(..., description="生成的HTML内容")
    image_resources: List[str] = Field(default=[], description="图像资源列表")
    audio_resources: List[str] = Field(default=[], description="音频资源列表")
    agent_chain: List[str] = Field(default=[], description="Agent执行链")
    generation_time: datetime = Field(default_factory=datetime.utcnow, description="生成时间")

    # ===== 新增：详细结构化数据字段（可选，存储完整的GameLogicResult） =====
    structured_game_logic: Optional[Dict[str, Any]] = Field(None, description="详细结构化游戏逻辑数据")
    target_audience: Optional[str] = Field(None, description="目标玩家群体")
    difficulty: Optional[str] = Field(None, description="难度等级")
    core_mechanics: Optional[List[str]] = Field(None, description="核心机制")
    notes_for_dev: Optional[str] = Field(None, description="开发注意事项")
    examples: Optional[List[str]] = Field(None, description="玩法变体示例")

    # ===== 扩展字段，存储增强提示词等信息 =====
    enhanced_prompt: Optional[str] = Field(None, description="发送给FileGenerateAgent的增强提示词")
    usage_stats: Optional[Dict[str, Any]] = Field(None, description="各Agent的token使用统计")

    # ===== RAG相关字段 =====
    rag_enhanced_prompt: Optional[str] = Field(None, description="RAG检索到的API文档和资源")
    dev_guidance: Optional[str] = Field(None, description="GameLogicAgent为FileGenerateAgent提供的开发指导意见")


class ConversationMessage(BaseModel):
    """对话消息"""
    message_id: str = Field(..., description="消息ID")
    user_prompt: str = Field(..., description="用户原始输入")
    history_enhanced_prompt: Optional[str] = Field(None, description="历史增强后的prompt")
    parent_message_id: Optional[str] = Field(None, description="父消息ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")
    game_data: Optional[GameData] = Field(None, description="游戏数据")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token使用情况")


class ConversationHistory(BaseModel):
    """对话历史记录"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    conversation_id: str = Field(..., description="对话ID")
    title: str = Field(default="新对话", description="对话标题")
    messages: List[ConversationMessage] = Field(default=[], description="对话消息列表")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class GameIterationRequest(BaseModel):
    """游戏迭代请求"""
    session_id: str = Field(..., description="会话ID")
    iteration_prompt: str = Field(..., description="迭代需求描述")
    keep_elements: List[str] = Field(default=[], description="保留的游戏元素")
    change_elements: List[str] = Field(default=[], description="需要修改的元素")


class GameSummary(BaseModel):
    """游戏摘要"""
    user_prompt: str = Field(..., description="用户输入")
    game_title: str = Field(..., description="游戏标题")
    game_description: str = Field(..., description="游戏描述")
    generation_time: datetime = Field(..., description="生成时间")


class ConversationWithGamesSummary(BaseModel):
    """带游戏信息的对话摘要"""
    session_id: str = Field(..., description="会话ID")
    title: str = Field(..., description="对话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    games: List[GameSummary] = Field(default=[], description="游戏摘要列表")




class ConversationCreateRequest(BaseModel):
    """创建对话请求"""
    session_id: str = Field(..., description="会话ID")
    messages: List[Dict[str, Any]] = Field(default=[], description="初始消息列表")


class ConversationUpdateRequest(BaseModel):
    """更新对话请求"""
    messages: List[Dict[str, Any]] = Field(..., description="消息列表")


class NewGameRequest(BaseModel):
    """新游戏生成请求"""
    user_prompt: str = Field(..., description="用户输入")
    model: Optional[str] = Field(None, description="模型ID，如 kimi-k2-turbo-preview")


class HistoryBasedGameRequest(BaseModel):
    """基于历史对话的游戏生成请求"""
    conversation_id: str = Field(..., description="对话ID")
    parent_message_id: str = Field(..., description="父消息ID")
    user_prompt: str = Field(..., description="用户输入")
    model: Optional[str] = Field(None, description="模型ID，如 kimi-k2-turbo-preview")


class GameGenerationResponse(BaseModel):
    """游戏生成响应"""
    conversation_id: str = Field(..., description="对话ID")
    message_id: str = Field(..., description="消息ID")
    game_data: GameData = Field(..., description="游戏数据")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token使用情况")


class ConversationSummaryResponse(BaseModel):
    """对话摘要响应"""
    intro: str = Field(..., description="对话简介（第一条消息的游戏标题）")
    conversation_id: str = Field(..., description="对话ID")
    timestamp: datetime = Field(..., description="创建时间")
    messages: List[ConversationMessage] = Field(..., description="消息列表")


