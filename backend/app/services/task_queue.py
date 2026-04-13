import asyncio
import json
import logging
import uuid
from typing import Any, Dict, Callable, Awaitable, Optional

import aio_pika

from ..config import settings

logger = logging.getLogger(__name__)


class TaskQueue:
    """RabbitMQ 任务队列封装，用于游戏生成异步化"""

    def __init__(self) -> None:
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._queue: Optional[aio_pika.Queue] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """建立与 RabbitMQ 的连接（惰性初始化）"""
        if self._connection and not self._connection.is_closed:
            return

        async with self._lock:
            if self._connection and not self._connection.is_closed:
                return

            logger.info(f"🔌 连接 RabbitMQ: {settings.rabbitmq_url}")
            self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            self._channel = await self._connection.channel()
            self._queue = await self._channel.declare_queue(
                settings.rabbitmq_queue_name,
                durable=True,
            )
            logger.info(f"✅ RabbitMQ 队列已就绪: {settings.rabbitmq_queue_name}")

    async def publish_game_task(self, payload: Dict[str, Any]) -> str:
        """发布游戏生成任务到队列，返回 task_id"""
        await self.connect()
        assert self._channel is not None

        task_id = str(uuid.uuid4())
        message_body = {
            "task_id": task_id,
            "type": "generate_game",
            **payload,
        }

        message = aio_pika.Message(
            body=json.dumps(message_body, ensure_ascii=False).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await self._channel.default_exchange.publish(
            message, routing_key=settings.rabbitmq_queue_name
        )
        logger.info(f"📨 已发布游戏生成任务到队列: task_id={task_id}")
        return task_id

    async def consume_game_tasks(
        self,
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """启动消费者，处理游戏生成任务

        注意：应在 FastAPI 启动时以后台任务方式运行
        """
        await self.connect()
        assert self._queue is not None

        async with self._queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        if message.content_type != "application/json":
                            logger.warning("收到非 JSON 消息，已忽略")
                            continue

                        payload = json.loads(message.body.decode("utf-8"))
                        logger.info(f"👷 处理队列任务: {payload.get('task_id')}")
                        await handler(payload)
                    except Exception as e:
                        logger.error(f"❌ 处理队列任务失败: {e}")


_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """获取全局 TaskQueue 单例"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue

