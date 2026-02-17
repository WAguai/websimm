"""
RAG (Retrieval-Augmented Generation) Service
用于检索API文档和资源库，增强Agent的生成能力
"""
import os
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class RAGService:
    """RAG服务：管理文档向量化、存储和检索"""

    def __init__(
        self,
        api_key: str,
        collection_name: str = "game_api_docs",
        persist_directory: str = "./chroma_db"
    ):
        """
        初始化RAG服务

        Args:
            api_key: Anthropic API密钥
            collection_name: Chroma集合名称
            persist_directory: Chroma数据持久化目录
        """
        self.api_key = api_key
        self.anthropic = Anthropic(api_key=api_key)
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # 初始化Chroma客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 获取或创建集合
        self.collection = self._get_or_create_collection()

        logger.info(f"✅ RAG服务初始化成功 - 集合: {collection_name}")

    def _get_or_create_collection(self) -> chromadb.Collection:
        """获取或创建Chroma集合"""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"📚 加载现有集合: {self.collection_name}")
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Game API documentation and resources"}
            )
            logger.info(f"🆕 创建新集合: {self.collection_name}")

        return collection

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        添加文档到向量数据库

        Args:
            documents: 文档文本列表
            metadatas: 文档元数据列表
            ids: 文档ID列表
        """
        try:
            # 生成embeddings并添加到集合
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]

            if metadatas is None:
                metadatas = [{"source": "unknown"} for _ in documents]

            # 使用Anthropic生成embeddings
            embeddings = self._generate_embeddings(documents)

            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"✅ 成功添加 {len(documents)} 个文档到向量数据库")

        except Exception as e:
            logger.error(f"❌ 添加文档失败: {str(e)}")
            raise

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        使用Claude生成文本embeddings
        注意：Claude本身不提供embedding API，这里使用简单的文本特征表示
        实际应用中可以使用OpenAI的embedding API或其他embedding模型
        """
        # 由于Claude不提供embedding，这里使用简化的方法
        # 在生产环境中，建议使用专门的embedding模型
        embeddings = []
        for text in texts:
            # 简单的字符级别向量化（仅用于演示）
            # 实际应用中应该使用真正的embedding模型
            embedding = self._simple_embedding(text)
            embeddings.append(embedding)

        return embeddings

    def _simple_embedding(self, text: str, dim: int = 384) -> List[float]:
        """
        简单的文本向量化方法（用于演示）
        实际应用中应替换为真正的embedding模型
        """
        import hashlib
        import struct

        # 使用哈希创建固定维度的向量
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        embedding = []
        for i in range(dim):
            byte_idx = i % len(hash_bytes)
            value = struct.unpack('B', bytes([hash_bytes[byte_idx]]))[0] / 255.0
            embedding.append(value)

        return embedding

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        检索相关文档

        Args:
            query: 查询文本
            n_results: 返回结果数量
            where: 过滤条件

        Returns:
            检索结果字典，包含documents, metadatas, distances
        """
        try:
            # 生成查询向量
            query_embedding = self._simple_embedding(query)

            # 执行检索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )

            logger.info(f"🔍 检索到 {len(results['documents'][0])} 个相关文档")

            return {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else []
            }

        except Exception as e:
            logger.error(f"❌ 检索失败: {str(e)}")
            return {
                "documents": [],
                "metadatas": [],
                "distances": []
            }

    def retrieve_for_context(
        self,
        query: str,
        n_results: int = 3
    ) -> str:
        """
        检索相关文档并格式化为上下文文本

        Args:
            query: 查询文本
            n_results: 返回结果数量

        Returns:
            格式化的上下文文本
        """
        results = self.retrieve(query, n_results=n_results)

        if not results["documents"]:
            return ""

        context_parts = []
        for i, (doc, metadata) in enumerate(zip(results["documents"], results["metadatas"])):
            source = metadata.get("source", "unknown")
            context_parts.append(f"[参考文档 {i+1} - {source}]\n{doc}\n")

        context = "\n".join(context_parts)
        return context

    def delete_collection(self) -> None:
        """删除当前集合"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"🗑️  删除集合: {self.collection_name}")
        except Exception as e:
            logger.error(f"❌ 删除集合失败: {str(e)}")

    def reset_collection(self) -> None:
        """重置集合（删除后重新创建）"""
        self.delete_collection()
        self.collection = self._get_or_create_collection()
        logger.info(f"🔄 重置集合: {self.collection_name}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {str(e)}")
            return {}


# 全局RAG服务实例
_rag_service: Optional[RAGService] = None


def get_rag_service(
    api_key: Optional[str] = None,
    collection_name: str = "game_api_docs"
) -> RAGService:
    """
    获取全局RAG服务实例（单例模式）

    Args:
        api_key: Anthropic API密钥
        collection_name: 集合名称

    Returns:
        RAG服务实例
    """
    global _rag_service

    if _rag_service is None:
        if api_key is None:
            from ..config import settings
            api_key = settings.anthropic_api_key or "dummy"  # RAG 使用 simple_embedding，不实际调用 Anthropic

        _rag_service = RAGService(
            api_key=api_key,
            collection_name=collection_name
        )

    return _rag_service
