from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from ..models.history_models import (
    ConversationHistory,
    ConversationMessage,
    GameData
)
import uuid
from ..config import settings

import logging

logger = logging.getLogger(__name__)


class HistoryService:
    """历史数据管理服务"""

    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db: AsyncIOMotorDatabase = None
        self.conversations_collection = None

    async def connect(self):
        """连接MongoDB"""
        try:
            # MongoDB连接字符串应该在config中配置
            mongo_url = getattr(settings, 'mongo_url', 'mongodb://localhost:27017')
            db_name = getattr(settings, 'mongo_db_name', 'game_generation')

            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[db_name]
            self.conversations_collection = self.db.conversation_history

            # 测试连接
            await self.client.admin.command('ping')
            logger.info("✅ MongoDB连接成功")

            # 清理旧数据并创建索引
            await self._migrate_database()

        except Exception as e:
            logger.error(f"❌ MongoDB连接失败: {str(e)}")
            raise

    async def _migrate_database(self):
        """数据库迁移：清理旧数据和索引"""
        try:
            # 清空旧数据（包含session_id字段的文档）
            old_docs_count = await self.conversations_collection.count_documents({"session_id": {"$exists": True}})
            if old_docs_count > 0:
                await self.conversations_collection.delete_many({"session_id": {"$exists": True}})
                logger.info(f"✅ 已清理 {old_docs_count} 条旧数据")

            # 创建新索引
            await self._create_indexes()

        except Exception as e:
            logger.error(f"❌ 数据库迁移失败: {str(e)}")
            # 如果迁移失败，仍然尝试创建索引
            await self._create_indexes()

    async def _create_indexes(self):
        """创建数据库索引"""
        try:
            # 删除旧的session_id索引（如果存在）
            try:
                await self.conversations_collection.drop_index("session_id_1")
                logger.info("✅ 旧的session_id索引已删除")
            except Exception as e:
                logger.info("旧索引不存在或已删除")

            # 创建新的conversation_id唯一索引
            try:
                await self.conversations_collection.create_index([("conversation_id", 1)], unique=True)
                logger.info("✅ conversation_id唯一索引已创建")
            except Exception as e:
                if "IndexKeySpecsConflict" in str(e):
                    await self.conversations_collection.drop_index("conversation_id_1")
                    await self.conversations_collection.create_index([("conversation_id", 1)], unique=True)
                    logger.info("✅ conversation_id索引重建完成")

            # 创建更新时间索引
            await self.conversations_collection.create_index([("updated_at", -1)])

            logger.info("✅ 数据库索引创建完成")
        except Exception as e:
            logger.error(f"❌ 创建索引失败: {str(e)}")

    async def create_new_conversation(self, session_id: str, title: str = "新对话") -> ConversationHistory:
        """创建新对话"""
        try:
            conversation_data = {
                "session_id": session_id,
                "title": title,
                "messages": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await self.conversations_collection.insert_one(conversation_data)
            conversation_data["_id"] = str(result.inserted_id)

            logger.info(f"✅ 新对话已创建: {session_id}")
            return ConversationHistory(**conversation_data)

        except Exception as e:
            logger.error(f"❌ 创建新对话失败: {str(e)}")
            raise

    async def create_new_game_message(
        self,
        conversation_id: str,
        user_prompt: str,
        game_data: GameData,
        parent_message_id: Optional[str] = None,
        history_enhanced_prompt: Optional[str] = None,
        usage: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """创建新的游戏消息并返回conversation_id和message_id"""
        try:
            message_id = str(uuid.uuid4())

            # 创建消息
            message = ConversationMessage(
                message_id=message_id,
                user_prompt=user_prompt,
                history_enhanced_prompt=history_enhanced_prompt,
                parent_message_id=parent_message_id,
                timestamp=datetime.utcnow(),
                game_data=game_data,
                usage=usage
            )

            # 检查对话是否存在
            conversation = await self.conversations_collection.find_one(
                {"conversation_id": conversation_id}
            )

            if not conversation:
                # 创建新对话
                title = game_data.title if game_data else user_prompt[:50] + ("..." if len(user_prompt) > 50 else "")
                conversation_data = {
                    "conversation_id": conversation_id,
                    "title": title,
                    "messages": [message.dict()],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                await self.conversations_collection.insert_one(conversation_data)
            else:
                # 添加消息到现有对话
                await self.conversations_collection.update_one(
                    {"conversation_id": conversation_id},
                    {
                        "$push": {"messages": message.dict()},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )

            logger.info(f"✅ 游戏消息已创建: conversation_id={conversation_id}, message_id={message_id}")
            return conversation_id, message_id

        except Exception as e:
            logger.error(f"❌ 创建游戏消息失败: {str(e)}")
            raise

    async def generate_history_enhanced_prompt(
        self,
        conversation_id: str,
        parent_message_id: str,
        user_prompt: str
    ) -> str:
        """生成历史增强的prompt"""
        try:
            # 获取父消息的游戏数据
            conversation = await self.conversations_collection.find_one(
                {"conversation_id": conversation_id}
            )

            if not conversation:
                logger.warning(f"对话不存在: {conversation_id}")
                return user_prompt

            # 查找父消息
            parent_message = None
            for msg in conversation.get("messages", []):
                if msg.get("message_id") == parent_message_id:
                    parent_message = msg
                    break

            if not parent_message or not parent_message.get("game_data"):
                logger.warning(f"父消息或游戏数据不存在: {parent_message_id}")
                return user_prompt

            # 提取父消息的游戏数据
            parent_game = parent_message["game_data"]

            # 构建历史增强prompt
            enhanced_prompt = f"""=== 历史游戏信息 ===
                基于以下现有游戏进行改进或扩展：
                
                游戏标题: {parent_game.get('title', '')}
                游戏类型: {parent_game.get('game_type', '')}
                游戏逻辑: {parent_game.get('game_logic', '')}
                游戏描述: {parent_game.get('description', '')}
                
                === 用户新需求 ===
                {user_prompt}
                
                === 指导原则 ===
                请基于上述现有游戏，结合用户的新需求，进行游戏的改进、优化或扩展。
                保持游戏的核心特色，同时满足用户的新要求。
                如果用户要求完全不同的游戏，请说明新游戏与原游戏的关系。
                """

            logger.info(f"✅ 历史增强prompt已生成，长度: {len(enhanced_prompt)}")
            return enhanced_prompt

        except Exception as e:
            logger.error(f"❌ 生成历史增强prompt失败: {str(e)}")
            return user_prompt



    async def get_conversation_by_id(self, conversation_id: str) -> Optional[ConversationHistory]:
        """根据conversation_id获取对话历史"""
        try:
            doc = await self.conversations_collection.find_one(
                {"conversation_id": conversation_id}
            )

            if doc:
                doc['_id'] = str(doc['_id'])
                return ConversationHistory(**doc)

            return None

        except Exception as e:
            logger.error(f"❌ 获取对话历史失败: {str(e)}")
            return None

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

    async def get_conversations_with_games_summary(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取带游戏信息的对话摘要列表（轻量级）"""
        try:
            pipeline = [
                {
                    "$project": {
                        "session_id": 1,
                        "title": 1,
                        "created_at": 1,
                        "updated_at": 1,
                        "games": {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$messages",
                                        "cond": {
                                            "$and": [
                                                {"$eq": ["$$this.role", "assistant"]},
                                                {"$ne": ["$$this.game_data", None]}
                                            ]
                                        }
                                    }
                                },
                                "as": "msg",
                                "in": {
                                    "user_prompt": {
                                        "$let": {
                                            "vars": {
                                                "user_msg": {
                                                    "$arrayElemAt": [
                                                        {
                                                            "$filter": {
                                                                "input": "$messages",
                                                                "cond": {
                                                                    "$and": [
                                                                        {"$eq": ["$$this.role", "user"]},
                                                                        {"$lt": ["$$this.timestamp", "$$msg.timestamp"]}
                                                                    ]
                                                                }
                                                            }
                                                        },
                                                        -1
                                                    ]
                                                }
                                            },
                                            "in": "$$user_msg.content"
                                        }
                                    },
                                    "game_title": "$$msg.game_data.title",
                                    "game_description": "$$msg.game_data.description",
                                    "generation_time": "$$msg.game_data.generation_time"
                                }
                            }
                        }
                    }
                },
                {"$sort": {"updated_at": -1}},
                {"$limit": limit}
            ]

            cursor = self.conversations_collection.aggregate(pipeline)
            conversations = []

            async for doc in cursor:
                # 过滤掉空的游戏数据
                games = [game for game in doc.get("games", []) if game.get("game_title")]

                conversations.append({
                    "session_id": doc["session_id"],
                    "title": doc.get("title", "新对话"),
                    "created_at": doc.get("created_at"),
                    "updated_at": doc.get("updated_at"),
                    "games": games
                })

            return conversations

        except Exception as e:
            logger.error(f"❌ 获取对话摘要失败: {str(e)}")
            return []

    async def get_all_conversations_new_format(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有对话的新格式摘要"""
        try:
            cursor = self.conversations_collection.find(
                {},
                {"conversation_id": 1, "messages": 1, "created_at": 1}
            ).sort("created_at", -1).limit(limit)

            conversations = []
            async for doc in cursor:
                messages = doc.get("messages", [])
                if not messages:
                    continue

                # 获取第一条消息的游戏标题作为intro
                first_message = messages[0]
                game_data = first_message.get("game_data")
                intro = game_data.get("title", "未命名游戏") if game_data else "新对话"

                conversations.append({
                    "intro": intro,
                    "conversation_id": doc["conversation_id"],
                    "timestamp": doc.get("created_at"),
                    "messages": messages
                })

            return conversations

        except Exception as e:
            logger.error(f"❌ 获取对话摘要失败: {str(e)}")
            return []


    async def create_conversation(self, session_id: str, messages: List[Dict[str, Any]] = None) -> ConversationHistory:
        """创建新对话"""
        try:
            # 生成标题
            title = "新对话"
            if messages:
                for msg in messages:
                    if msg.get("role") == "user":
                        content = msg.get("content", "")
                        title = content[:50] + ("..." if len(content) > 50 else "")
                        break

            conversation_data = {
                "session_id": session_id,
                "title": title,
                "messages": messages or [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await self.conversations_collection.insert_one(conversation_data)
            conversation_data["_id"] = str(result.inserted_id)

            return ConversationHistory(**conversation_data)

        except Exception as e:
            logger.error(f"❌ 创建对话失败: {str(e)}")
            raise

    async def update_conversation(self, session_id: str, messages: List[Dict[str, Any]]) -> ConversationHistory:
        """更新对话消息"""
        try:
            result = await self.conversations_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "messages": messages,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            if result.matched_count == 0:
                raise ValueError(f"对话不存在: {session_id}")

            # 返回更新后的对话
            return await self.get_conversation_history(session_id)

        except Exception as e:
            logger.error(f"❌ 更新对话失败: {str(e)}")
            raise

    async def delete_conversation(self, session_id: str) -> bool:
        """删除对话"""
        try:
            result = await self.conversations_collection.delete_one(
                {"session_id": session_id}
            )

            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"❌ 删除对话失败: {str(e)}")
            return False

    async def get_game_history_from_conversation(self, session_id: str) -> List[GameData]:
        """从对话历史中提取所有游戏数据"""
        try:
            conversation = await self.get_conversation_history(session_id)
            if not conversation:
                return []

            game_data_list = []
            for message in conversation.messages:
                if message.game_data:
                    game_data_list.append(message.game_data)

            return game_data_list

        except Exception as e:
            logger.error(f"❌ 获取游戏历史失败: {str(e)}")
            return []

    async def close(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB连接已关闭")


# 全局历史服务实例
history_service = HistoryService()