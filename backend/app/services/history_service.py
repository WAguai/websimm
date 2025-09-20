from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from ..models.history_models import (
    GameGenerationHistory, 
    ConversationHistory, 
    GameIterationRequest
)
from ..models.context_models import GameContext
from ..models.game_models import GameGenerationResult
from ..config import settings

import logging

logger = logging.getLogger(__name__)


class HistoryService:
    """历史数据管理服务"""
    
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db: AsyncIOMotorDatabase = None
        self.games_collection = None
        self.conversations_collection = None
    
    async def connect(self):
        """连接MongoDB"""
        try:
            # MongoDB连接字符串应该在config中配置
            mongo_url = getattr(settings, 'mongo_url', 'mongodb://localhost:27017')
            db_name = getattr(settings, 'mongo_db_name', 'game_generation')
            
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[db_name]
            self.games_collection = self.db.game_history
            self.conversations_collection = self.db.conversation_history
            
            # 测试连接
            await self.client.admin.command('ping')
            logger.info("✅ MongoDB连接成功")
            
            # 创建索引
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"❌ MongoDB连接失败: {str(e)}")
            raise
    
    async def _create_indexes(self):
        """创建数据库索引"""
        try:
            # 游戏历史索引
            await self.games_collection.create_index("session_id")
            await self.games_collection.create_index("generation_time")
            await self.games_collection.create_index([("session_id", 1), ("version", -1)])
            
            # 对话历史索引
            await self.conversations_collection.create_index("session_id")
            await self.conversations_collection.create_index("created_at")
            
            logger.info("✅ 数据库索引创建完成")
        except Exception as e:
            logger.error(f"❌ 索引创建失败: {str(e)}")
    
    async def save_game_generation(
        self, 
        session_id: str, 
        context: GameContext, 
        result: GameGenerationResult,
        parent_version_id: Optional[str] = None
    ) -> str:
        """保存游戏生成记录"""
        try:
            # 获取当前session的版本号
            version = await self._get_next_version(session_id)
            
            # 创建历史记录
            history = GameGenerationHistory(
                session_id=session_id,
                user_prompt=context.user_prompt,
                game_title=context.game_logic.title,
                game_type=context.game_logic.game_type,
                game_logic=context.game_logic.game_logic,
                description=context.game_logic.description,
                html_content=result.files.html,
                image_resources=result.image_resources,
                audio_resources=result.audio_resources,
                agent_chain=context.metadata.agent_chain,
                version=version,
                parent_version_id=ObjectId(parent_version_id) if parent_version_id else None
            )
            
            # 保存到数据库
            result_doc = await self.games_collection.insert_one(
                history.dict(by_alias=True, exclude={'id'})
            )
            
            record_id = str(result_doc.inserted_id)
            logger.info(f"✅ 游戏生成记录已保存: {record_id}")
            
            return record_id
            
        except Exception as e:
            logger.error(f"❌ 保存游戏记录失败: {str(e)}")
            raise
    
    async def _get_next_version(self, session_id: str) -> int:
        """获取会话的下一个版本号"""
        latest = await self.games_collection.find_one(
            {"session_id": session_id},
            sort=[("version", -1)]
        )
        return (latest["version"] + 1) if latest else 1
    
    async def get_session_history(
        self, 
        session_id: str, 
        limit: int = 10
    ) -> List[GameGenerationHistory]:
        """获取会话历史记录"""
        try:
            cursor = self.games_collection.find(
                {"session_id": session_id}
            ).sort("generation_time", -1).limit(limit)
            
            histories = []
            async for doc in cursor:
                doc['_id'] = str(doc['_id'])
                if doc.get('parent_version_id'):
                    doc['parent_version_id'] = str(doc['parent_version_id'])
                histories.append(GameGenerationHistory(**doc))
            
            return histories
            
        except Exception as e:
            logger.error(f"❌ 获取会话历史失败: {str(e)}")
            return []
    
    async def get_latest_version(self, session_id: str) -> Optional[GameGenerationHistory]:
        """获取会话的最新版本"""
        try:
            doc = await self.games_collection.find_one(
                {"session_id": session_id},
                sort=[("version", -1)]
            )
            
            if doc:
                doc['_id'] = str(doc['_id'])
                if doc.get('parent_version_id'):
                    doc['parent_version_id'] = str(doc['parent_version_id'])
                return GameGenerationHistory(**doc)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取最新版本失败: {str(e)}")
            return None
    
    async def save_conversation(
        self, 
        session_id: str, 
        messages: List[Dict[str, Any]]
    ) -> str:
        """保存对话记录"""
        try:
            # 检查是否已存在该会话的对话记录
            existing = await self.conversations_collection.find_one(
                {"session_id": session_id}
            )
            
            if existing:
                # 更新现有记录
                await self.conversations_collection.update_one(
                    {"session_id": session_id},
                    {
                        "$set": {
                            "messages": messages,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                return str(existing["_id"])
            else:
                # 创建新记录
                conversation = ConversationHistory(
                    session_id=session_id,
                    messages=messages
                )
                
                result = await self.conversations_collection.insert_one(
                    conversation.dict(by_alias=True, exclude={'id'})
                )
                
                return str(result.inserted_id)
                
        except Exception as e:
            logger.error(f"❌ 保存对话记录失败: {str(e)}")
            raise
    
    async def get_conversation_history(self, session_id: str) -> Optional[ConversationHistory]:
        """获取对话历史"""
        try:
            doc = await self.conversations_collection.find_one(
                {"session_id": session_id}
            )
            
            if doc:
                doc['_id'] = str(doc['_id'])
                return ConversationHistory(**doc)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取对话历史失败: {str(e)}")
            return None
    
    async def get_game_by_id(self, game_id: str) -> Optional[GameGenerationHistory]:
        """根据ID获取游戏记录"""
        try:
            doc = await self.games_collection.find_one(
                {"_id": ObjectId(game_id)}
            )
            
            if doc:
                doc['_id'] = str(doc['_id'])
                if doc.get('parent_version_id'):
                    doc['parent_version_id'] = str(doc['parent_version_id'])
                return GameGenerationHistory(**doc)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取游戏记录失败: {str(e)}")
            return None
    
    async def update_user_feedback(
        self, 
        game_id: str, 
        rating: Optional[int] = None,
        feedback: Optional[str] = None
    ) -> bool:
        """更新用户反馈"""
        try:
            update_data = {}
            if rating is not None:
                update_data["user_rating"] = rating
            if feedback is not None:
                update_data["user_feedback"] = feedback
            
            if not update_data:
                return False
            
            result = await self.games_collection.update_one(
                {"_id": ObjectId(game_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ 更新用户反馈失败: {str(e)}")
            return False
    
    async def close(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB连接已关闭")


# 全局历史服务实例
history_service = HistoryService()