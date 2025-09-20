// 前端核心接口定义

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface GameFiles {
  html: string  // 包含所有代码的完整HTML文件
}

export interface GameVersion {
  id: number
  files: GameFiles
  description: string
  userPrompt: string  // 用户输入的原始提示词
  timestamp: Date
  messageId: string
}

// 后端API响应接口
export interface GameGenerationResult {
  files: GameFiles
  description: string
  gameLogic: string
  imageResources: string[]
  audioResources: string[]
}

// 后端健康检查响应
export interface BackendHealthResponse {
  status: string
  timestamp: string
  service: string
}
