"""
文档加载器 - 用于加载和处理各种格式的文档
支持：Markdown, HTML, 纯文本, JSON等
"""
import os
import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import re

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """文档数据类"""
    content: str
    metadata: Dict[str, Any]
    id: Optional[str] = None


class DocumentLoader:
    """文档加载器基类"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化文档加载器

        Args:
            chunk_size: 文档分块大小
            chunk_overlap: 块之间的重叠字符数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load(self, source: str) -> List[Document]:
        """
        加载文档（需要子类实现）

        Args:
            source: 文档源（文件路径、URL等）

        Returns:
            文档列表
        """
        raise NotImplementedError

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Document]:
        """
        将长文本分块

        Args:
            text: 原始文本
            metadata: 元数据

        Returns:
            分块后的文档列表
        """
        if len(text) <= self.chunk_size:
            return [Document(content=text, metadata=metadata)]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # 尝试在句子边界处分割
            if end < len(text):
                # 查找最近的句号、问号或换行符
                for delimiter in ['\n\n', '\n', '. ', '。', '! ', '！', '? ', '？']:
                    last_delimiter = text.rfind(delimiter, start, end)
                    if last_delimiter != -1:
                        end = last_delimiter + len(delimiter)
                        break

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = len(chunks)
                chunks.append(Document(
                    content=chunk_text,
                    metadata=chunk_metadata
                ))

            start = end - self.chunk_overlap if end < len(text) else end

        return chunks


class MarkdownLoader(DocumentLoader):
    """Markdown文档加载器"""

    def load(self, file_path: str) -> List[Document]:
        """加载Markdown文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = {
                'source': file_path,
                'type': 'markdown',
                'filename': Path(file_path).name
            }

            return self.chunk_text(content, metadata)

        except Exception as e:
            logger.error(f"❌ 加载Markdown文件失败 {file_path}: {str(e)}")
            return []


class HTMLLoader(DocumentLoader):
    """HTML文档加载器"""

    def load(self, file_path: str) -> List[Document]:
        """加载HTML文件"""
        try:
            if BeautifulSoup is None:
                raise ImportError("需要安装beautifulsoup4: pip install beautifulsoup4")

            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # 移除script和style标签
            for script in soup(['script', 'style']):
                script.decompose()

            # 提取文本
            text = soup.get_text()

            # 清理多余的空白
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = text.strip()

            metadata = {
                'source': file_path,
                'type': 'html',
                'filename': Path(file_path).name
            }

            return self.chunk_text(text, metadata)

        except Exception as e:
            logger.error(f"❌ 加载HTML文件失败 {file_path}: {str(e)}")
            return []


class JSONLoader(DocumentLoader):
    """JSON文档加载器"""

    def __init__(self, content_key: str = 'content', **kwargs):
        """
        初始化JSON加载器

        Args:
            content_key: JSON中包含内容的键名
        """
        super().__init__(**kwargs)
        self.content_key = content_key

    def load(self, file_path: str) -> List[Document]:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            documents = []

            # 如果是列表
            if isinstance(data, list):
                for i, item in enumerate(data):
                    content = self._extract_content(item)
                    if content:
                        metadata = {
                            'source': file_path,
                            'type': 'json',
                            'filename': Path(file_path).name,
                            'index': i
                        }
                        documents.extend(self.chunk_text(content, metadata))

            # 如果是单个对象
            elif isinstance(data, dict):
                content = self._extract_content(data)
                if content:
                    metadata = {
                        'source': file_path,
                        'type': 'json',
                        'filename': Path(file_path).name
                    }
                    documents.extend(self.chunk_text(content, metadata))

            return documents

        except Exception as e:
            logger.error(f"❌ 加载JSON文件失败 {file_path}: {str(e)}")
            return []

    def _extract_content(self, item: Any) -> str:
        """从JSON对象中提取内容"""
        if isinstance(item, str):
            return item
        elif isinstance(item, dict):
            if self.content_key in item:
                return str(item[self.content_key])
            # 如果没有指定键，将整个对象转为字符串
            return json.dumps(item, ensure_ascii=False)
        else:
            return str(item)


class TextLoader(DocumentLoader):
    """纯文本文档加载器"""

    def load(self, file_path: str) -> List[Document]:
        """加载文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = {
                'source': file_path,
                'type': 'text',
                'filename': Path(file_path).name
            }

            return self.chunk_text(content, metadata)

        except Exception as e:
            logger.error(f"❌ 加载文本文件失败 {file_path}: {str(e)}")
            return []


class DirectoryLoader:
    """目录加载器 - 批量加载目录中的文档"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """初始化目录加载器"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 文件扩展名到加载器的映射
        self.loaders = {
            '.md': MarkdownLoader(chunk_size, chunk_overlap),
            '.markdown': MarkdownLoader(chunk_size, chunk_overlap),
            '.html': HTMLLoader(chunk_size, chunk_overlap),
            '.htm': HTMLLoader(chunk_size, chunk_overlap),
            '.json': JSONLoader(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
            '.txt': TextLoader(chunk_size, chunk_overlap),
        }

    def load(
        self,
        directory: str,
        glob_pattern: str = "**/*",
        exclude_patterns: Optional[List[str]] = None
    ) -> List[Document]:
        """
        加载目录中的所有文档

        Args:
            directory: 目录路径
            glob_pattern: 文件匹配模式
            exclude_patterns: 排除的文件模式列表

        Returns:
            文档列表
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            logger.error(f"❌ 目录不存在: {directory}")
            return []

        all_documents = []
        exclude_patterns = exclude_patterns or []

        # 遍历匹配的文件
        for file_path in directory_path.glob(glob_pattern):
            if not file_path.is_file():
                continue

            # 检查是否应该排除
            should_exclude = any(
                re.search(pattern, str(file_path))
                for pattern in exclude_patterns
            )
            if should_exclude:
                continue

            # 根据文件扩展名选择加载器
            suffix = file_path.suffix.lower()
            loader = self.loaders.get(suffix)

            if loader:
                logger.info(f"📄 加载文件: {file_path}")
                documents = loader.load(str(file_path))
                all_documents.extend(documents)
            else:
                logger.debug(f"⏭️  跳过不支持的文件类型: {file_path}")

        logger.info(f"✅ 从目录 {directory} 加载了 {len(all_documents)} 个文档块")
        return all_documents


class APIDocumentLoader:
    """API文档预置加载器 - 加载常见游戏开发API文档"""

    @staticmethod
    def load_phaser_docs() -> List[Document]:
        """加载Phaser游戏引擎文档（示例）"""
        # 这里提供一些预置的Phaser API文档
        phaser_docs = [
            {
                "content": """
Phaser.Game - 游戏主类
创建一个新的Phaser游戏实例。

构造函数:
new Phaser.Game(config)

配置参数:
- type: Phaser.AUTO, Phaser.CANVAS, 或 Phaser.WEBGL
- width: 游戏宽度（像素）
- height: 游戏高度（像素）
- scene: 场景类或场景配置对象
- physics: 物理引擎配置
- backgroundColor: 背景颜色

示例:
const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    scene: {
        preload: preload,
        create: create,
        update: update
    }
};
const game = new Phaser.Game(config);
                """,
                "metadata": {"source": "phaser", "api": "Game", "category": "core"}
            },
            {
                "content": """
Phaser.Scene - 场景类
场景是游戏的一个独立部分，包含自己的资源、游戏对象和逻辑。

生命周期方法:
- init(data): 初始化场景，接收启动数据
- preload(): 预加载资源
- create(data): 创建游戏对象
- update(time, delta): 每帧更新

加载资源:
this.load.image('key', 'path/to/image.png');
this.load.audio('key', 'path/to/audio.mp3');
this.load.spritesheet('key', 'path/to/spritesheet.png', { frameWidth: 32, frameHeight: 32 });

添加游戏对象:
this.add.sprite(x, y, 'key');
this.add.text(x, y, 'Hello World', { fontSize: '32px', fill: '#fff' });
                """,
                "metadata": {"source": "phaser", "api": "Scene", "category": "core"}
            },
            {
                "content": """
Phaser.Physics.Arcade - Arcade物理引擎
简单、快速的物理引擎，适合大多数2D游戏。

启用物理:
在游戏配置中添加：
physics: {
    default: 'arcade',
    arcade: {
        gravity: { y: 300 },
        debug: false
    }
}

给游戏对象添加物理:
this.physics.add.sprite(x, y, 'key');
this.physics.add.existing(gameObject);

设置物理属性:
sprite.setVelocity(100, 200);
sprite.setBounce(0.2);
sprite.setCollideWorldBounds(true);

碰撞检测:
this.physics.add.collider(object1, object2, collisionCallback);
this.physics.add.overlap(object1, object2, overlapCallback);
                """,
                "metadata": {"source": "phaser", "api": "Physics", "category": "physics"}
            }
        ]

        documents = []
        for i, doc_data in enumerate(phaser_docs):
            documents.append(Document(
                content=doc_data["content"].strip(),
                metadata=doc_data["metadata"],
                id=f"phaser_doc_{i}"
            ))

        logger.info(f"✅ 加载了 {len(documents)} 个Phaser文档")
        return documents

    @staticmethod
    def load_canvas_docs() -> List[Document]:
        """加载Canvas API文档（示例）"""
        canvas_docs = [
            {
                "content": """
Canvas API - 基础绘图
HTML5 Canvas提供了2D绘图API。

获取上下文:
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

绘制矩形:
ctx.fillRect(x, y, width, height);  // 填充矩形
ctx.strokeRect(x, y, width, height);  // 描边矩形
ctx.clearRect(x, y, width, height);  // 清除矩形区域

设置样式:
ctx.fillStyle = 'red';  // 填充颜色
ctx.strokeStyle = '#00ff00';  // 描边颜色
ctx.lineWidth = 5;  // 线宽
                """,
                "metadata": {"source": "canvas", "api": "drawing", "category": "basic"}
            },
            {
                "content": """
Canvas API - 路径绘制
使用路径可以绘制复杂的形状。

开始路径:
ctx.beginPath();

移动和绘制:
ctx.moveTo(x, y);  // 移动到点
ctx.lineTo(x, y);  // 画线到点
ctx.arc(x, y, radius, startAngle, endAngle);  // 画圆弧

完成路径:
ctx.closePath();  // 闭合路径
ctx.stroke();  // 描边
ctx.fill();  // 填充

示例 - 绘制三角形:
ctx.beginPath();
ctx.moveTo(100, 100);
ctx.lineTo(200, 200);
ctx.lineTo(100, 200);
ctx.closePath();
ctx.fill();
                """,
                "metadata": {"source": "canvas", "api": "path", "category": "basic"}
            },
            {
                "content": """
Canvas API - 动画
创建流畅的Canvas动画。

requestAnimationFrame:
使用requestAnimationFrame创建动画循环。

function animate() {
    requestAnimationFrame(animate);

    // 清除画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 绘制内容
    drawGameObjects();

    // 更新状态
    updateGameLogic();
}

animate();

性能优化:
- 只重绘改变的区域
- 使用离屏canvas
- 避免频繁的状态改变
- 批量绘制相同的对象
                """,
                "metadata": {"source": "canvas", "api": "animation", "category": "advanced"}
            }
        ]

        documents = []
        for i, doc_data in enumerate(canvas_docs):
            documents.append(Document(
                content=doc_data["content"].strip(),
                metadata=doc_data["metadata"],
                id=f"canvas_doc_{i}"
            ))

        logger.info(f"✅ 加载了 {len(documents)} 个Canvas文档")
        return documents
