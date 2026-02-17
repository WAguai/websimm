'use client'

import { useState, KeyboardEvent } from 'react'
import { Send, Loader2, MessageSquare, ChevronDown } from 'lucide-react'
import { ModelInfo } from '../types'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  isGenerating: boolean
  onOpenConversations: () => void
  models?: ModelInfo[]
  selectedModel?: string
  onModelChange?: (modelId: string) => void
}

export default function ChatInput({ onSendMessage, isGenerating, onOpenConversations, models = [], selectedModel = '', onModelChange }: ChatInputProps) {
  const [input, setInput] = useState('')
  const [showModelDropdown, setShowModelDropdown] = useState(false)

  const handleSend = () => {
    if (input.trim() && !isGenerating) {
      onSendMessage(input.trim())
      setInput('')
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // const quickActions = [
  //   { icon: '🔊', label: '音频' },
  //   { icon: '🔍', label: '搜索' },
  //   { icon: '🍎', label: '苹果' },
  //   { icon: '🔊', label: '音频2' },
  //   { icon: '📄', label: '文档' }
  // ]

  return (
    <div className="border-t border-gray-700 bg-gray-900 text-white">
      {/* 快捷操作按钮 */}
      {/* <div className="p-3 border-b border-gray-700">
        <div className="flex items-center space-x-2">
          <button className="w-8 h-8 bg-gray-700 hover:bg-gray-600 rounded flex items-center justify-center transition-colors">
            <span className="text-lg">+</span>
          </button>
          {quickActions.map((action, index) => (
            <button
              key={index}
              className="w-8 h-8 bg-gray-700 hover:bg-gray-600 rounded flex items-center justify-center transition-colors text-sm"
              title={action.label}
            >
              {action.icon}
            </button>
          ))}
          <div className="flex-1"></div>
          <button className="w-8 h-8 bg-gray-700 hover:bg-gray-600 rounded flex items-center justify-center transition-colors">
            <span className="text-sm">^</span>
          </button>
        </div>
      </div> */}

      {/* 输入区域 */}
      <div className="p-4">
        <div className="flex space-x-3">
          <button
            onClick={onOpenConversations}
            className="self-end px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors flex items-center justify-center"
            title="对话历史"
          >
            <MessageSquare size={16} />
          </button>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="描述你想要的游戏..."
            className="flex-1 resize-none bg-transparent border-none text-gray-300 placeholder-gray-500 focus:outline-none text-sm"
            rows={2}
            disabled={isGenerating}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isGenerating}
            className="self-end px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded transition-colors flex items-center space-x-2"
          >
            {isGenerating ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Send size={16} />
            )}
          </button>
        </div>
      </div>

      {/* 底部模型选择 */}
      <div className="px-4 pb-4 flex items-center justify-between text-sm">
        <div className="flex items-center space-x-2 relative">
          <div className="w-4 h-4 bg-blue-500 rounded flex items-center justify-center">
            <span className="text-xs text-white">AI</span>
          </div>
          {models.length > 0 ? (
            <div className="relative">
              <button
                onClick={() => setShowModelDropdown(!showModelDropdown)}
                className="flex items-center space-x-1 text-gray-300 hover:text-white px-2 py-1 rounded hover:bg-gray-700 transition-colors"
              >
                <span>{models.find(m => m.id === selectedModel)?.name || selectedModel || '选择模型'}</span>
                <ChevronDown size={12} className={showModelDropdown ? 'rotate-180' : ''} />
              </button>
              {showModelDropdown && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowModelDropdown(false)} />
                  <div className="absolute bottom-full left-0 mb-1 py-1 bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-20 min-w-[180px]">
                    {models.map((m) => (
                      <button
                        key={m.id}
                        onClick={() => { onModelChange?.(m.id); setShowModelDropdown(false) }}
                        className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-700 ${m.id === selectedModel ? 'text-blue-400 bg-gray-700/50' : 'text-gray-300'}`}
                      >
                        {m.name}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          ) : (
            <span className="text-gray-500">加载模型...</span>
          )}
        </div>
      </div>
    </div>
  )
}