"""
RAG API路由 - 管理RAG知识库
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from ..services.rag_service import get_rag_service
from ..services.document_loader import (
    APIDocumentLoader,
    DirectoryLoader,
    MarkdownLoader,
    HTMLLoader,
    JSONLoader,
    TextLoader
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/rag",
    tags=["RAG Knowledge Base"]
)


# ===== 请求/响应模型 =====

class AddDocumentRequest(BaseModel):
    """添加文档请求"""
    documents: List[str] = Field(..., description="文档文本列表")
    metadatas: Optional[List[Dict[str, Any]]] = Field(None, description="文档元数据列表")
    ids: Optional[List[str]] = Field(None, description="文档ID列表")


class RetrieveRequest(BaseModel):
    """检索请求"""
    query: str = Field(..., description="查询文本")
    n_results: int = Field(3, ge=1, le=10, description="返回结果数量")


class RetrieveResponse(BaseModel):
    """检索响应"""
    success: bool
    query: str
    documents: List[str]
    metadatas: List[Dict[str, Any]]
    distances: List[float]
    document_count: int


class InitializeKBRequest(BaseModel):
    """初始化知识库请求"""
    load_phaser_docs: bool = Field(True, description="是否加载Phaser文档")
    load_canvas_docs: bool = Field(True, description="是否加载Canvas文档")
    custom_docs_path: Optional[str] = Field(None, description="自定义文档路径")


class StatsResponse(BaseModel):
    """统计信息响应"""
    collection_name: str
    document_count: int
    persist_directory: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    message: str
    rag_enabled: bool
    collection_stats: Optional[Dict[str, Any]] = None


# ===== API端点 =====

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """RAG系统健康检查"""
    try:
        rag_service = get_rag_service()
        stats = rag_service.get_collection_stats()

        return HealthResponse(
            status="healthy",
            message="RAG系统运行正常",
            rag_enabled=True,
            collection_stats=stats
        )
    except Exception as e:
        logger.error(f"RAG健康检查失败: {str(e)}")
        return HealthResponse(
            status="error",
            message=f"RAG系统异常: {str(e)}",
            rag_enabled=False
        )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """获取知识库统计信息"""
    try:
        rag_service = get_rag_service()
        stats = rag_service.get_collection_stats()

        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.post("/documents/add")
async def add_documents(request: AddDocumentRequest):
    """添加文档到知识库"""
    try:
        rag_service = get_rag_service()

        rag_service.add_documents(
            documents=request.documents,
            metadatas=request.metadatas,
            ids=request.ids
        )

        return {
            "success": True,
            "message": f"成功添加 {len(request.documents)} 个文档",
            "document_count": len(request.documents)
        }

    except Exception as e:
        logger.error(f"添加文档失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加文档失败: {str(e)}"
        )


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_documents(request: RetrieveRequest):
    """检索相关文档"""
    try:
        rag_service = get_rag_service()

        results = rag_service.retrieve(
            query=request.query,
            n_results=request.n_results
        )

        return RetrieveResponse(
            success=True,
            query=request.query,
            documents=results["documents"],
            metadatas=results["metadatas"],
            distances=results["distances"],
            document_count=len(results["documents"])
        )

    except Exception as e:
        logger.error(f"检索文档失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检索文档失败: {str(e)}"
        )


@router.post("/initialize")
async def initialize_knowledge_base(request: InitializeKBRequest):
    """初始化知识库 - 加载预置文档"""
    try:
        rag_service = get_rag_service()
        total_docs = 0
        loaded_sources = []

        # 加载Phaser文档
        if request.load_phaser_docs:
            logger.info("📚 加载Phaser API文档...")
            phaser_docs = APIDocumentLoader.load_phaser_docs()

            documents = [doc.content for doc in phaser_docs]
            metadatas = [doc.metadata for doc in phaser_docs]
            ids = [doc.id for doc in phaser_docs]

            rag_service.add_documents(documents, metadatas, ids)
            total_docs += len(phaser_docs)
            loaded_sources.append("Phaser API")
            logger.info(f"✅ Phaser文档加载完成: {len(phaser_docs)} 个文档")

        # 加载Canvas文档
        if request.load_canvas_docs:
            logger.info("📚 加载Canvas API文档...")
            canvas_docs = APIDocumentLoader.load_canvas_docs()

            documents = [doc.content for doc in canvas_docs]
            metadatas = [doc.metadata for doc in canvas_docs]
            ids = [doc.id for doc in canvas_docs]

            rag_service.add_documents(documents, metadatas, ids)
            total_docs += len(canvas_docs)
            loaded_sources.append("Canvas API")
            logger.info(f"✅ Canvas文档加载完成: {len(canvas_docs)} 个文档")

        # 加载自定义文档目录
        if request.custom_docs_path:
            logger.info(f"📚 加载自定义文档: {request.custom_docs_path}")
            try:
                dir_loader = DirectoryLoader()
                custom_docs = dir_loader.load(request.custom_docs_path)

                if custom_docs:
                    documents = [doc.content for doc in custom_docs]
                    metadatas = [doc.metadata for doc in custom_docs]
                    ids = [f"custom_{i}" for i in range(len(custom_docs))]

                    rag_service.add_documents(documents, metadatas, ids)
                    total_docs += len(custom_docs)
                    loaded_sources.append(f"Custom ({request.custom_docs_path})")
                    logger.info(f"✅ 自定义文档加载完成: {len(custom_docs)} 个文档")
            except Exception as e:
                logger.warning(f"⚠️  加载自定义文档失败: {str(e)}")

        return {
            "success": True,
            "message": "知识库初始化完成",
            "total_documents": total_docs,
            "loaded_sources": loaded_sources,
            "stats": rag_service.get_collection_stats()
        }

    except Exception as e:
        logger.error(f"初始化知识库失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化知识库失败: {str(e)}"
        )


@router.post("/reset")
async def reset_knowledge_base():
    """重置知识库（删除所有文档）"""
    try:
        rag_service = get_rag_service()
        rag_service.reset_collection()

        return {
            "success": True,
            "message": "知识库已重置",
            "stats": rag_service.get_collection_stats()
        }

    except Exception as e:
        logger.error(f"重置知识库失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置知识库失败: {str(e)}"
        )


@router.get("/test")
async def test_rag_system():
    """测试RAG系统 - 执行一次完整的测试流程"""
    try:
        rag_service = get_rag_service()

        # 测试查询
        test_queries = [
            "如何创建Phaser游戏",
            "Canvas绘制矩形",
            "物理引擎碰撞检测"
        ]

        test_results = []
        for query in test_queries:
            results = rag_service.retrieve(query, n_results=2)
            test_results.append({
                "query": query,
                "found_documents": len(results["documents"]),
                "top_result": results["documents"][0] if results["documents"] else None
            })

        return {
            "success": True,
            "message": "RAG系统测试完成",
            "stats": rag_service.get_collection_stats(),
            "test_results": test_results
        }

    except Exception as e:
        logger.error(f"RAG系统测试失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG系统测试失败: {str(e)}"
        )
