from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import game_routes, history_routes, rag_routes
from .services.history_service import history_service
from .config import settings
import logging
import asyncio

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Game Generation Backend",
    description="AI驱动的多代理游戏生成后端服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(game_routes.router)
app.include_router(history_routes.router)
app.include_router(rag_routes.router)

# 根路径
@app.get("/")
async def root():
    return {
        "message": "Game Generation Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/game/health"
    }

# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Game Generation Backend 启动中...")

    # 连接MongoDB
    try:
        await history_service.connect()
    except Exception as e:
        logger.warning(f"⚠️  MongoDB连接失败，历史功能将不可用: {str(e)}")

    # 初始化RAG知识库
    try:
        from .services.rag_service import get_rag_service
        from .services.document_loader import APIDocumentLoader

        logger.info("📚 初始化RAG知识库...")
        rag_service = get_rag_service()

        # 检查知识库是否已有文档
        stats = rag_service.get_collection_stats()
        if stats.get("document_count", 0) == 0:
            logger.info("📖 知识库为空，加载预置API文档...")

            # 加载Phaser文档
            phaser_docs = APIDocumentLoader.load_phaser_docs()
            rag_service.add_documents(
                documents=[doc.content for doc in phaser_docs],
                metadatas=[doc.metadata for doc in phaser_docs],
                ids=[doc.id for doc in phaser_docs]
            )

            # 加载Canvas文档
            canvas_docs = APIDocumentLoader.load_canvas_docs()
            rag_service.add_documents(
                documents=[doc.content for doc in canvas_docs],
                metadatas=[doc.metadata for doc in canvas_docs],
                ids=[doc.id for doc in canvas_docs]
            )

            logger.info(f"✅ RAG知识库初始化完成，共 {len(phaser_docs) + len(canvas_docs)} 个文档")
        else:
            logger.info(f"✅ RAG知识库已存在，包含 {stats.get('document_count', 0)} 个文档")

    except Exception as e:
        logger.warning(f"⚠️  RAG知识库初始化失败，RAG功能将不可用: {str(e)}")

    # 启动 RabbitMQ 任务消费者（用于异步游戏生成）
    # 先尝试连接，连接失败则不启动消费者，避免后台任务报错
    try:
        from .services.task_queue import get_task_queue
        from .services.game_service import game_service

        task_queue = get_task_queue()
        await task_queue.connect()
    except Exception as e:
        logger.warning(
            f"⚠️  RabbitMQ 不可用，异步任务功能将关闭。"
            f" 请启动 RabbitMQ（如: brew services start rabbitmq）或忽略此警告使用同步接口。错误: {e}"
        )
    else:
        async def handle_game_task(payload):
            from .services.history_service import history_service as hs  # 避免循环引用

            task_id = payload.get("task_id")
            user_prompt = payload.get("user_prompt", "")
            model = payload.get("model")
            session_id = payload.get("conversation_id")

            await hs.update_task_status(task_id, "running")
            try:
                result = await game_service.generate_game(
                    prompt=user_prompt,
                    session_id=session_id,
                    save_to_history=True,
                    model=model,
                )
                await hs.update_task_status(
                    task_id,
                    "success",
                    conversation_id=result.session_id,
                    message_id=getattr(result, "record_id", None),
                )
            except Exception as e:
                logger.error(f"❌ 异步游戏生成任务失败: {e}")
                await hs.update_task_status(task_id, "failed", error=str(e))

        asyncio.create_task(task_queue.consume_game_tasks(handle_game_task))
        logger.info("✅ RabbitMQ 任务消费者已启动")

    logger.info("🚀 Game Generation Backend 启动成功!")
    logger.info(f"📍 服务地址: http://{settings.host}:{settings.port}")
    logger.info(f"📚 API文档: http://{settings.host}:{settings.port}/docs")
    logger.info(f"🌐 前端地址: {settings.frontend_url}")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Game Generation Backend 正在关闭...")
    
    # 关闭MongoDB连接
    await history_service.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )