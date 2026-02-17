// 对话历史API服务

import {
  ConversationSummary,
  ConversationFull,
  NewGameRequest,
  NewGameResponse,
  HistoryBasedGameRequest,
  HistoryBasedGameResponse,
  ModelInfo
} from '../types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class ConversationApi {
  // 0. 获取可用模型列表
  static async getModels(): Promise<{ models: ModelInfo[]; default: string }> {
    const response = await fetch(`${API_BASE_URL}/api/game/models`)
    if (!response.ok) throw new Error('Failed to fetch models')
    return response.json()
  }

  // 1. 创建新游戏对话
  static async createNewGame(request: NewGameRequest): Promise<NewGameResponse> {
    const response = await fetch(`${API_BASE_URL}/api/game/new`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`Failed to create new game: ${response.statusText}`)
    }

    return await response.json()
  }

  // 2. 基于历史对话生成游戏
  static async createHistoryBasedGame(request: HistoryBasedGameRequest): Promise<HistoryBasedGameResponse> {
    const response = await fetch(`${API_BASE_URL}/api/game/history-based`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`Failed to create history-based game: ${response.statusText}`)
    }

    return await response.json()
  }

  // 3. 获取历史对话列表
  static async getConversationsList(limit: number = 100): Promise<ConversationSummary[]> {
    const response = await fetch(`${API_BASE_URL}/api/conversations/list?limit=${limit}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch conversations list: ${response.statusText}`)
    }

    return await response.json()
  }

  // 4. 获取对话详细数据
  static async getConversationFull(conversationId: string): Promise<ConversationFull> {
    const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}/full`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch conversation detail: ${response.statusText}`)
    }

    return await response.json()
  }
}