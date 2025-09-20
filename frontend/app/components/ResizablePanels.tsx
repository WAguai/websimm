'use client'

import { useState, useRef, useEffect, ReactNode } from 'react'

interface ResizablePanelsProps {
  leftPanel: ReactNode
  rightPanel: ReactNode
  defaultLeftWidth?: number // 百分比，默认70%
  minLeftWidth?: number     // 最小百分比，默认30%
  maxLeftWidth?: number     // 最大百分比，默认85%
}

export default function ResizablePanels({
  leftPanel,
  rightPanel,
  defaultLeftWidth = 70,
  minLeftWidth = 30,
  maxLeftWidth = 85
}: ResizablePanelsProps) {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth)
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return

      const containerRect = containerRef.current.getBoundingClientRect()
      const newLeftWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100

      // 限制在最小和最大宽度之间
      const clampedWidth = Math.max(minLeftWidth, Math.min(maxLeftWidth, newLeftWidth))
      setLeftWidth(clampedWidth)
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isDragging, minLeftWidth, maxLeftWidth])

  const handleMouseDown = () => {
    setIsDragging(true)
  }

  return (
    <div ref={containerRef} className="flex h-full">
      {/* 左侧面板 */}
      <div 
        className="flex-shrink-0 bg-white border-r border-gray-300"
        style={{ width: `${leftWidth}%` }}
      >
        {leftPanel}
      </div>

      {/* 分割器 */}
      <div
        className={`w-1 bg-gray-300 hover:bg-blue-400 cursor-col-resize flex-shrink-0 transition-colors duration-150 relative group ${
          isDragging ? 'bg-blue-500' : ''
        }`}
        onMouseDown={handleMouseDown}
      >
        {/* 分割器中间的拖拽指示器 */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-0.5 h-8 bg-white opacity-50 rounded-full group-hover:opacity-80 transition-opacity"></div>
        </div>
        
        {/* 拖拽提示 */}
        <div className="absolute -left-2 -right-2 top-0 bottom-0 hover:bg-blue-100 hover:bg-opacity-20 transition-colors"></div>
      </div>

      {/* 右侧面板 */}
      <div 
        className="flex-1 bg-gray-900"
        style={{ width: `${100 - leftWidth}%` }}
      >
        {rightPanel}
      </div>
    </div>
  )
}