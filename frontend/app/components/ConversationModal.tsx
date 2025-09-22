'use client'

import { useState, useEffect } from 'react'
import { ConversationSummary } from '../types'
import { ConversationApi } from '../lib/conversationApi'


interface ConversationModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectConversation: (conversationId: string) => void
  onNewConversation: () => void
}

export default function ConversationModal({
  isOpen,
  onClose,
  onSelectConversation,
  onNewConversation
}: ConversationModalProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadConversations()
    }
  }, [isOpen])

  const loadConversations = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await ConversationApi.getConversationsList(50)  // 限制50条
      setConversations(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectConversation = async (conversationId: string) => {
    try {
      onSelectConversation(conversationId)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversation')
    }
  }

  const handleNewConversation = () => {
    onNewConversation()
    onClose()
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)

    if (diffInHours < 1) {
      return '刚刚'
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)} 小时前`
    } else if (diffInHours < 24 * 7) {
      return `${Math.floor(diffInHours / 24)} 天前`
    } else {
      return date.toLocaleDateString('zh-CN')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-800">选择对话</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* New Conversation Button */}
          <div className="p-6 border-r border-gray-200">
            <button
              onClick={handleNewConversation}
              className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
              </svg>
              开始新对话
            </button>
          </div>

          {/* Conversation List */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600">加载中...</span>
              </div>
            ) : error ? (
              <div className="p-6">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-600">加载失败: {error}</p>
                  <button
                    onClick={loadConversations}
                    className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                  >
                    重试
                  </button>
                </div>
              </div>
            ) : conversations.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <p>暂无历史对话</p>
                <p className="text-sm mt-1">点击"开始新对话"创建第一个对话</p>
              </div>
            ) : (
              <div className="p-4">
                <div className="space-y-3">
                  {conversations.map((conv) => (
                    <div
                      key={conv.conversation_id}
                      onClick={() => handleSelectConversation(conv.conversation_id)}
                      className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-medium text-gray-900 truncate flex-1 mr-2">
                          {conv.intro}
                        </h3>
                        <span className="text-sm text-gray-500 whitespace-nowrap">
                          {formatDate(conv.timestamp)}
                        </span>
                      </div>

                      {/* 显示游戏数量和最新游戏信息 */}
                      {conv.messages.length > 0 && (
                        <div className="mb-2">
                          <div className="text-sm text-gray-600">
                            最新：{conv.messages[conv.messages.length - 1].game_data.title}
                          </div>
                          <div className="text-xs text-gray-500">
                            "{conv.messages[conv.messages.length - 1].user_prompt}"
                          </div>
                        </div>
                      )}

                      <div className="flex justify-between items-center text-xs text-gray-500">
                        <span>{conv.messages.length} 个游戏</span>
                        <span>ID: {conv.conversation_id.slice(-8)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}