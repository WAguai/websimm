# AI 游戏生成器

一个基于 AI 的网页游戏生成平台，用户可以通过自然语言与 AI 对话，实时生成可运行的 HTML5 游戏。本项目仿制了 [WebSim.com](https://websim.com/) 的核心功能，专注于实现 AI 游戏生成模块。

![AI Game Generator](https://via.placeholder.com/800x400/4CAF50/FFFFFF?text=AI+Game+Generator)

## ✨ 核心功能

### 🎮 游戏生成
- **自然语言交互**：通过简单的文字描述生成游戏
- **多种游戏类型**：支持跳跃平台、贪吃蛇、收集等多种游戏类型
- **实时预览**：生成后立即可在左侧区域预览和游玩

### 🔧 多代理系统
项目采用多代理（Multi-Agent）协作机制，包含以下专业化 Agent：

- **🎮 游戏逻辑 Agent**：负责设计核心游戏机制和代码结构
- **🎨 图像资源 Agent**：根据语义生成或引用合适的图像资源
- **🔊 音效资源 Agent**：为游戏生成基础音效或添加音频占位链接
- **🧠 脚本整合 Agent**：整合其他 Agent 的输出，生成最终可运行的游戏文件

### 📁 源码管理
- **三文件结构**：每个游戏生成 HTML、CSS、JS 三个独立文件
- **源码查看器**：点击 "View Source" 查看和编辑源代码
- **实时编辑**：支持在线编辑代码并实时预览
- **文件下载**：支持单个文件或批量下载所有文件

### 💬 版本历史
- **对话历史**：右侧展示完整的用户与 AI 对话记录
- **版本切换**：点击历史版本可在左侧切换预览对应的游戏
- **版本管理**：每次对话都会生成新的游戏版本

## 🚀 快速开始

### 环境要求
- Node.js 18+ 
- npm 或 yarn

### 安装依赖
```bash
npm install
```

### 启动开发服务器
```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000) 开始使用。

### 构建生产版本
```bash
npm run build
npm start
```

## 🎯 使用示例

在右侧输入框中输入以下示例来生成不同类型的游戏：

- `"生成一个跳跃类平台游戏"` - 创建一个简单的平台跳跃游戏
- `"创建一个贪吃蛇游戏"` - 生成经典的贪吃蛇游戏
- `"制作一个收集游戏"` - 开发一个收集红色方块的游戏

## 🏗️ 项目结构

```
ai-game-generator/
├── app/
│   ├── components/           # React 组件
│   │   ├── GamePreview.tsx   # 游戏预览组件
│   │   ├── ChatHistory.tsx   # 聊天历史组件
│   │   ├── ChatInput.tsx     # 输入框组件
│   │   └── SourceViewer.tsx  # 源码查看器组件
│   ├── lib/                  # 核心逻辑
│   │   ├── agents/           # 多代理系统
│   │   │   ├── gameLogicAgent.ts      # 游戏逻辑代理
│   │   │   ├── imageResourceAgent.ts  # 图像资源代理
│   │   │   ├── audioResourceAgent.ts  # 音效资源代理
│   │   │   └── scriptIntegrationAgent.ts # 脚本整合代理
│   │   ├── gameAgents.ts     # 主代理协调器
│   │   ├── gameTemplates.ts  # 游戏模板
│   │   └── htmlGenerator.ts  # HTML 生成器
│   ├── types.ts              # TypeScript 类型定义
│   ├── page.tsx              # 主页面
│   ├── layout.tsx            # 布局组件
│   └── globals.css           # 全局样式
├── public/                   # 静态资源
├── package.json
└── README.md
```

## 🔧 技术栈

### 前端框架
- **Next.js 14** - React 全栈框架
- **React 18** - 用户界面库
- **TypeScript** - 类型安全的 JavaScript

### 样式和 UI
- **Tailwind CSS** - 实用优先的 CSS 框架
- **Lucide React** - 现代图标库

### 开发工具
- **ESLint** - 代码质量检查
- **PostCSS** - CSS 后处理器

## 🎨 界面设计

### 布局结构
- **左侧区域**：游戏预览和运行区域，支持 iframe 沙箱环境
- **右侧区域**：深色主题的聊天界面，展示对话历史和版本列表
- **底部输入**：自然语言输入框，支持快捷操作按钮

### 设计特色
- **深色主题**：右侧聊天区域采用现代深色设计
- **版本缩略图**：每个游戏版本都有对应的可视化缩略图
- **响应式设计**：适配不同屏幕尺寸

## 🔮 多代理工作流程

1. **用户输入**：用户通过自然语言描述想要的游戏
2. **游戏逻辑生成**：游戏逻辑 Agent 分析需求并生成核心代码
3. **资源处理**：图像和音效 Agent 并行处理相关资源
4. **脚本整合**：整合 Agent 将所有组件组合成完整的游戏文件
5. **文件输出**：生成 HTML、CSS、JS 三个独立文件
6. **预览展示**：在左侧区域实时预览生成的游戏

## 📝 支持的游戏类型

### 🏃 跳跃平台游戏
- 重力系统和跳跃机制
- 平台碰撞检测
- 敌人和障碍物
- 得分系统

### 🐍 贪吃蛇游戏
- 经典蛇身移动逻辑
- 食物生成和碰撞检测
- 边界和自身碰撞检测
- 分数统计

### 🎯 收集游戏
- 玩家角色控制
- 随机目标生成
- 碰撞检测和得分
- 边界限制

## 🛠️ 自定义和扩展

### 添加新游戏类型
1. 在 `app/lib/gameTemplates.ts` 中添加新的游戏逻辑
2. 更新 `app/lib/agents/gameLogicAgent.ts` 中的游戏类型识别
3. 在各个 Agent 中添加对应的资源处理逻辑

### 自定义 Agent
每个 Agent 都是独立的模块，可以轻松扩展或替换：
- 实现相同的接口
- 添加新的处理逻辑
- 在主协调器中注册新 Agent

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 灵感来源于 [WebSim.com](https://websim.com/)
- 使用了 [Next.js](https://nextjs.org/) 框架
- UI 组件基于 [Tailwind CSS](https://tailwindcss.com/)
- 图标来自 [Lucide](https://lucide.dev/)

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue：[GitHub Issues](https://github.com/your-username/ai-game-generator/issues)
- 邮箱：your-email@example.com

---

⭐ 如果这个项目对你有帮助，请给它一个星标！