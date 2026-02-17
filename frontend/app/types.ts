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

// 匹配实际后端API结构
export interface GameData {
  title: string
  game_type: string
  game_logic: string
  description: string
  html_content: string
  image_resources: string[]
  audio_resources: string[]
  agent_chain: string[]
}

export interface BackendMessage {
  message_id: string
  user_prompt: string
  history_enhanced_prompt?: string
  parent_message_id?: string
  timestamp: string
  game_data: GameData
  usage?: {
    total_tokens?: number
    prompt_tokens?: number
    completion_tokens?: number
  }
}

export interface ConversationSummary {
  intro: string
  conversation_id: string
  timestamp: string
  messages: BackendMessage[]
}

export interface ConversationFull {
  id: string
  conversation_id: string
  title: string
  messages: BackendMessage[]
  created_at: string
  updated_at: string
}

// 可用模型
export interface ModelInfo {
  id: string
  name: string
  provider: string
}

// 创建新游戏请求
export interface NewGameRequest {
  user_prompt: string
  model?: string
}

// 创建新游戏响应
export interface NewGameResponse {
  conversation_id: string
  message_id: string
  game_data: GameData
  usage?: any
}

// 基于历史的游戏生成请求
export interface HistoryBasedGameRequest {
  conversation_id: string
  parent_message_id: string
  user_prompt: string
  model?: string
}

// 基于历史的游戏生成响应
export interface HistoryBasedGameResponse {
  conversation_id: string
  message_id: string
  game_data: GameData
  usage?: any
}
