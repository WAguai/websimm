"""
RAG Agent - 检索增强生成代理
为其他Agent提供上下文检索和增强功能
"""
import logging
from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
from ..services.rag_service import get_rag_service

logger = logging.getLogger(__name__)


class RAGAgent(BaseAgent):
    """RAG Agent - 提供检索增强生成能力"""

    def __init__(self, ai_client, collection_name: str = "game_api_docs"):
        """
        初始化RAG Agent

        Args:
            ai_client: AI客户端
            collection_name: 使用的向量数据库集合名称
        """
        super().__init__(ai_client)
        self.collection_name = collection_name
        self.rag_service = get_rag_service(collection_name=collection_name)

    @property
    def system_message(self) -> str:
        """系统提示词"""
        return """你是一个RAG检索助手，负责从知识库中检索相关信息。

你的职责：
1. 理解用户的查询意图
2. 从向量数据库中检索最相关的文档
3. 将检索结果整理成清晰、有用的上下文信息

检索原则：
- 准确理解查询关键词
- 返回最相关的文档片段
- 保持信息的完整性和准确性
"""

    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理检索请求

        Args:
            context: 包含查询信息的上下文

        Returns:
            检索结果
        """
        query = context.get("query", "")
        n_results = context.get("n_results", 3)

        logger.info(f"🔍 RAG Agent 检索: {query[:100]}...")

        try:
            # 执行检索
            results = self.rag_service.retrieve(
                query=query,
                n_results=n_results
            )

            # 格式化上下文
            context_text = self._format_context(results)

            return {
                "success": True,
                "query": query,
                "retrieved_documents": results["documents"],
                "context_text": context_text,
                "document_count": len(results["documents"])
            }

        except Exception as e:
            logger.error(f"❌ RAG检索失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "context_text": ""
            }

    def _format_context(self, results: Dict[str, Any]) -> str:
        """
        格式化检索结果为上下文文本

        Args:
            results: 检索结果

        Returns:
            格式化的上下文文本
        """
        if not results["documents"]:
            return ""

        context_parts = ["=== 相关API文档和参考资料 ===\n"]

        for i, (doc, metadata) in enumerate(zip(results["documents"], results["metadatas"])):
            source = metadata.get("source", "unknown")
            api_name = metadata.get("api", "")
            category = metadata.get("category", "")

            header = f"\n[参考 {i+1}]"
            if api_name:
                header += f" {api_name}"
            if category:
                header += f" ({category})"
            header += f" - 来源: {source}"

            context_parts.append(header)
            context_parts.append("-" * 60)
            context_parts.append(doc)
            context_parts.append("")

        return "\n".join(context_parts)

    async def retrieve_for_prompt(
        self,
        query: str,
        n_results: int = 3
    ) -> str:
        """
        为提示词检索相关上下文

        Args:
            query: 查询文本
            n_results: 返回结果数量

        Returns:
            格式化的上下文文本
        """
        context = {"query": query, "n_results": n_results}
        result = await self.process(context)

        if result.get("success"):
            return result["context_text"]
        else:
            return ""

    def add_documents_to_kb(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        添加文档到知识库

        Args:
            documents: 文档文本列表
            metadatas: 元数据列表
            ids: 文档ID列表

        Returns:
            是否成功
        """
        try:
            self.rag_service.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ 成功添加 {len(documents)} 个文档到知识库")
            return True
        except Exception as e:
            logger.error(f"❌ 添加文档失败: {str(e)}")
            return False

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        return self.rag_service.get_collection_stats()


class RAGEnhancedMixin:
    """RAG增强混入类 - 为现有Agent添加RAG能力"""

    def __init__(self, *args, enable_rag: bool = True, **kwargs):
        """
        初始化RAG增强混入

        Args:
            enable_rag: 是否启用RAG
        """
        super().__init__(*args, **kwargs)
        self.enable_rag = enable_rag
        self._rag_service = None

        if enable_rag:
            try:
                self._rag_service = get_rag_service()
                logger.info(f"✅ {self.__class__.__name__} 启用RAG增强")
            except Exception as e:
                logger.warning(f"⚠️  RAG服务初始化失败，将不使用RAG: {str(e)}")
                self.enable_rag = False

    async def enhance_prompt_with_rag(
        self,
        base_prompt: str,
        query: Optional[str] = None,
        n_results: int = 3
    ) -> str:
        """
        使用RAG增强提示词

        Args:
            base_prompt: 基础提示词
            query: 检索查询（如果为None，使用base_prompt）
            n_results: 检索结果数量

        Returns:
            增强后的提示词
        """
        if not self.enable_rag or not self._rag_service:
            return base_prompt

        try:
            # 使用base_prompt作为查询
            search_query = query or base_prompt

            # 检索相关上下文
            context = self._rag_service.retrieve_for_context(
                query=search_query,
                n_results=n_results
            )

            if context:
                # 将上下文添加到提示词中
                enhanced_prompt = f"""{base_prompt}

{context}

请参考以上API文档和资料来完成任务。确保使用正确的API和最佳实践。
"""
                logger.info(f"✅ 提示词已通过RAG增强（检索到 {n_results} 个相关文档）")
                return enhanced_prompt
            else:
                logger.debug("未检索到相关文档，使用原始提示词")
                return base_prompt

        except Exception as e:
            logger.warning(f"⚠️  RAG增强失败，使用原始提示词: {str(e)}")
            return base_prompt


def create_rag_enhanced_agent(agent_class):
    """
    工厂函数：创建支持RAG的Agent类

    Args:
        agent_class: 原始Agent类

    Returns:
        支持RAG的新Agent类

    示例:
        RAGGameLogicAgent = create_rag_enhanced_agent(GameLogicAgent)
        agent = RAGGameLogicAgent(ai_client, enable_rag=True)
    """
    class RAGEnhancedAgent(RAGEnhancedMixin, agent_class):
        """RAG增强的Agent"""
        pass

    RAGEnhancedAgent.__name__ = f"RAG{agent_class.__name__}"
    RAGEnhancedAgent.__doc__ = f"RAG增强版本的{agent_class.__name__}"

    return RAGEnhancedAgent
