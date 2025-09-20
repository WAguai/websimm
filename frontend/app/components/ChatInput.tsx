'use client'

import { useState, KeyboardEvent } from 'react'
import { Send, Loader2 } from 'lucide-react'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  isGenerating: boolean
}

export default function ChatInput({ onSendMessage, isGenerating }: ChatInputProps) {
  const [input, setInput] = useState('')

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
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="What would you like to change?"
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
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-blue-500 rounded flex items-center justify-center">
            <span className="text-xs text-white">A</span>
          </div>
          <span className="text-gray-300">Gemini 2.5 Pro</span>
          <button className="text-gray-500 hover:text-gray-300">
            <span className="text-xs">^</span>
          </button>
        </div>
        <div className="flex items-center space-x-2 text-gray-500">
          <span className="text-xs">🌐</span>
          <span className="text-xs">Public</span>
        </div>
      </div>
    </div>
  )
}