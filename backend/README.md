# Game Generation Backend

AI驱动的多代理游戏生成后端服务，使用Python FastAPI构建。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env` 文件并配置你的API密钥：

```bash
cp .env .env.local
```

编辑 `.env` 文件：
```env
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 3. 启动服务

```bash
# 方式1: 使用启动脚本
python run.py

# 方式2: 直接使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问服务

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/game/health
- **游戏生成**: POST http://localhost:8000/api/game/generate

## 📁 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── models/              # Pydantic数据模型
│   ├── agents/              # AI Agent实现
│   ├── services/            # 业务逻辑服务
│   └── routers/             # API路由
├── requirements.txt         # Python依赖
├── .env                     # 环境变量配置
└── run.py                  # 启动脚本
```

## 🤖 Agent架构

系统采用多代理协作架构：

1. **GameLogicAgent** - 游戏逻辑设计和特征推断
2. **FileGenerateAgent** - 生成完整的HTML游戏文件
3. **ImageResourceAgent** - 图像资源引用生成
4. **AudioResourceAgent** - 音频资源引用生成

## 🔌 API接口

### 生成游戏

```http
POST /api/game/generate
Content-Type: application/json

{
  "prompt": "创建一个简单的贪吃蛇游戏",
  "context": []
}
```

响应：
```json
{
  "success": true,
  "data": {
    "files": {
      "html": "完整的HTML文件内容，包含内嵌的CSS和JavaScript"
    },
    "description": "游戏描述",
    "game_logic": "游戏逻辑",
    "image_resources": ["..."],
    "audio_resources": ["..."]
  },
  "timestamp": "2025-01-19T..."
}
```

**注意**: 现在只生成一个完整的HTML文件，包含所有CSS样式和JavaScript代码，可以直接在浏览器中打开运行。

## 🔧 开发说明

### 添加新的Agent

1. 继承 `BaseAgent` 类
2. 实现 `process()` 和 `system_message` 方法
3. 在 `GameService` 中注册新Agent

### 自定义配置

修改 `app/config.py` 中的 `Settings` 类来添加新的配置项。

## 📝 日志

服务会输出详细的执行日志，包括：
- Agent执行流程
- AI接口调用
- 错误信息
- 性能统计

## 🚨 注意事项

1. 确保 `.env` 文件中的API密钥正确配置
2. 首次运行可能需要下载模型，请耐心等待
3. 建议在生产环境中使用更安全的密钥管理方案