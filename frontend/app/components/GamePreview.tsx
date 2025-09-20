'use client'

import { useEffect, useRef } from 'react'
import { GameVersion } from '../types'

interface GamePreviewProps {
  gameVersion: GameVersion | null
  isGenerating: boolean
  onGameVersionUpdate?: (gameVersion: GameVersion) => void
}

export default function GamePreview({ gameVersion, isGenerating, onGameVersionUpdate }: GamePreviewProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null)

  useEffect(() => {
    if (gameVersion && iframeRef.current) {
      const iframe = iframeRef.current
      const doc = iframe.contentDocument || iframe.contentWindow?.document
      
      if (doc) {
        doc.open()
        // 直接使用生成的完整HTML文件
        const completeHTML = gameVersion.files.html
        doc.write(completeHTML)
        doc.close()
      }
    }
  }, [gameVersion])

  const handleFilesChange = (newFiles: any) => {
    if (gameVersion && onGameVersionUpdate) {
      const updatedVersion = {
        ...gameVersion,
        files: newFiles
      }
      onGameVersionUpdate(updatedVersion)
    }
  }

  if (isGenerating) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">AI 正在生成游戏...</p>
          <div className="mt-4 space-y-2 text-sm text-gray-500">
            <div className="flex items-center justify-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span>🎮 游戏逻辑 Agent 设计中...</span>
            </div>
            <div className="flex items-center justify-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>📄 文件生成 Agent 编码中...</span>
            </div>
            <div className="flex items-center justify-center space-x-2">
              <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
              <span>🎨 图像资源 Agent 处理中...</span>
            </div>
            <div className="flex items-center justify-center space-x-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
              <span>🔊 音效资源 Agent 生成中...</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!gameVersion) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <div className="text-6xl mb-4">🎮</div>
          <h2 className="text-xl font-semibold mb-2">欢迎使用 AI 游戏生成器</h2>
          <p className="text-gray-400">在右侧输入框中描述你想要的游戏，AI 将为你生成可交互的网页游戏</p>
          <div className="mt-6 text-sm text-gray-400">
            <p>示例：</p>
            <ul className="mt-2 space-y-1">
              <li>"生成一个跳跃类平台游戏"</li>
              <li>"创建一个简单的贪吃蛇游戏"</li>
              <li>"制作一个太空射击游戏"</li>
            </ul>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="bg-gray-100 px-4 py-2 border-b border-gray-200 flex-shrink-0">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-gray-700">游戏预览</h3>
          <span className="text-xs text-gray-500">
            版本 {gameVersion.id + 1} - {gameVersion.timestamp.toLocaleTimeString()}
          </span>
        </div>
      </div>
      <div className="flex-1 p-2 min-h-0">
        <iframe
          ref={iframeRef}
          className="w-full h-full rounded-lg shadow-sm border border-gray-200 bg-white"
          sandbox="allow-scripts allow-same-origin"
          title={`Game Version ${gameVersion.id + 1}`}
        />
      </div>
    </div>
  )
}