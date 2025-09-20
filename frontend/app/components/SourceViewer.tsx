'use client'

import { useState } from 'react'
import { X, Copy, Download, ExternalLink } from 'lucide-react'
import { GameVersion } from '../types'

interface SourceViewerProps {
  gameVersion: GameVersion
  isOpen: boolean
  onClose: () => void
}

export default function SourceViewer({ gameVersion, isOpen, onClose }: SourceViewerProps) {
  const [copied, setCopied] = useState(false)

  if (!isOpen) return null

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(gameVersion.files.html)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('复制失败:', err)
    }
  }

  const handleDownload = () => {
    const blob = new Blob([gameVersion.files.html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `game-v${gameVersion.id + 1}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleOpenInNewTab = () => {
    const blob = new Blob([gameVersion.files.html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-full max-h-[90vh] flex flex-col">
        {/* 头部 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              游戏源码 - 版本 {gameVersion.id + 1}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {gameVersion.description}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopy}
              className="px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100 flex items-center space-x-1"
            >
              <Copy size={14} />
              <span>{copied ? '已复制' : '复制'}</span>
            </button>
            <button
              onClick={handleDownload}
              className="px-3 py-1.5 text-sm bg-green-50 text-green-600 rounded hover:bg-green-100 flex items-center space-x-1"
            >
              <Download size={14} />
              <span>下载</span>
            </button>
            <button
              onClick={handleOpenInNewTab}
              className="px-3 py-1.5 text-sm bg-purple-50 text-purple-600 rounded hover:bg-purple-100 flex items-center space-x-1"
            >
              <ExternalLink size={14} />
              <span>新窗口打开</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-gray-600 rounded"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* 代码内容 */}
        <div className="flex-1 overflow-hidden">
          <pre className="h-full overflow-auto p-4 bg-gray-50 text-sm font-mono">
            <code className="text-gray-800">
              {gameVersion.files.html}
            </code>
          </pre>
        </div>

        {/* 底部信息 */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div>
              文件大小: {(gameVersion.files.html.length / 1024).toFixed(1)} KB
            </div>
            <div>
              生成时间: {gameVersion.timestamp.toLocaleString()}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}