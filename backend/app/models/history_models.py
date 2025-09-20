from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """MongoDB ObjectId的Pydantic兼容版本"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string')


class GameGenerationHistory(BaseModel):
    """游戏生成历史记录"""
    id: Optional[PyObjectId] = Field(alias="_id")
    session_id: str = Field(..., description="会话ID")
    user_prompt: str = Field(..., description="用户原始输入")
    game_title: str = Field(..., description="游戏标题")
    game_type: str = Field(..., description="游戏类型")
    game_logic: str = Field(..., description="游戏逻辑")
    description: str = Field(..., description="游戏描述")
    
    # 生成的文件和资源
    html_content: str = Field(..., description="生成的HTML内容")
    image_resources: List[str] = Field(default=[], description="图像资源列表")
    audio_resources: List[str] = Field(default=[], description="音频资源列表")
    
    # 元数据
    agent_chain: List[str] = Field(default=[], description="Agent执行链")
    generation_time: datetime = Field(default_factory=datetime.utcnow, description="生成时间")
    version: int = Field(default=1, description="版本号")
    parent_version_id: Optional[PyObjectId] = Field(None, description="父版本ID（用于迭代）")
    
    # 用户反馈和评分
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="用户评分(1-5)")
    user_feedback: Optional[str] = Field(None, description="用户反馈")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ConversationHistory(BaseModel):
    """对话历史记录"""
    id: Optional[PyObjectId] = Field(alias="_id")
    session_id: str = Field(..., description="会话ID")
    messages: List[Dict[str, Any]] = Field(default=[], description="对话消息列表")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class GameIterationRequest(BaseModel):
    """游戏迭代请求"""
    session_id: str = Field(..., description="会话ID")
    base_version_id: str = Field(..., description="基础版本ID")
    iteration_prompt: str = Field(..., description="迭代需求描述")
    keep_elements: List[str] = Field(default=[], description="保留的游戏元素")
    change_elements: List[str] = Field(default=[], description="需要修改的元素")