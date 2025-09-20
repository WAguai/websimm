'use client'

import { useState, useRef } from 'react'
import GamePreview from './components/GamePreview'
import ChatHistory from './components/ChatHistory'
import ChatInput from './components/ChatInput'
import BackendHealthCheck from './components/BackendHealthCheck'
import ResizablePanels from './components/ResizablePanels'
import { GameAgents } from './lib/gameAgents'
import { Message, GameVersion } from './types'
export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [gameVersions, setGameVersions] = useState<GameVersion[]>([])
  const [currentGameIndex, setCurrentGameIndex] = useState<number>(-1)
  const [isGenerating, setIsGenerating] = useState(false)
  const gameAgents = useRef(new GameAgents())

  // // 初始化一些示例对话和游戏版本
  // useEffect(() => {
  //   const initializeExamples = async () => {
  //     const exampleConversations = [
  //       {
  //         userPrompt: '生成一个跳跃平台游戏',
  //         aiResponse: '已为你生成了一个跳跃平台游戏！使用方向键控制角色移动和跳跃。'
  //       },
  //       {
  //         userPrompt: '创建一个贪吃蛇游戏',
  //         aiResponse: '贪吃蛇游戏已生成！使用方向键控制蛇的移动方向，吃到食物会增长。'
  //       },
  //       {
  //         userPrompt: '制作一个收集游戏',
  //         aiResponse: '收集游戏已完成！控制绿色方块移动，收集红色目标来获得分数。'
  //       }
  //     ]

  //     const initialMessages: Message[] = []
  //     const initialGameVersions: GameVersion[] = []

  //     for (let i = 0; i < exampleConversations.length; i++) {
  //       const conversation = exampleConversations[i]
  //       const baseTime = new Date(Date.now() - (exampleConversations.length - i) * 300000) // 5分钟间隔

  //       const userMessage: Message = {
  //         id: `user-${i}`,
  //         role: 'user',
  //         content: conversation.userPrompt,
  //         timestamp: new Date(baseTime.getTime() - 60000) // 用户消息在AI回复前1分钟
  //       }

  //       const aiMessage: Message = {
  //         id: `ai-${i}`,
  //         role: 'assistant',
  //         content: conversation.aiResponse,
  //         timestamp: baseTime
  //       }

  //       // 生成对应的游戏版本
  //       const gameResult = await gameAgents.current.generateGame(conversation.userPrompt, [])

  //       const gameVersion: GameVersion = {
  //         id: i,
  //         files: gameResult.files,
  //         description: gameResult.description,
  //         timestamp: baseTime,
  //         messageId: aiMessage.id
  //       }

  //       initialMessages.push(userMessage, aiMessage)
  //       initialGameVersions.push(gameVersion)
  //     }

  //     setMessages(initialMessages)
  //     setGameVersions(initialGameVersions)
  //     setCurrentGameIndex(0) // 默认显示第一个游戏
  //   }

  //   initializeExamples()
  // }, [])

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsGenerating(true)

    try {
      // 使用多代理系统生成游戏
      const gameResult = await gameAgents.current.generateGame(content, messages)

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: gameResult.description,
        timestamp: new Date()
      }

      const newGameVersion: GameVersion = {
        id: gameVersions.length,
        files: gameResult.files,
        description: gameResult.description,
        userPrompt: content,  // 保存用户输入的原始提示词
        timestamp: new Date(),
        messageId: aiMessage.id
      }

      setMessages(prev => [...prev, aiMessage])
      setGameVersions(prev => [...prev, newGameVersion])
      setCurrentGameIndex(gameVersions.length)
    } catch (error) {
      console.error('生成游戏失败:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '抱歉，生成游戏时出现错误，请重试。',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsGenerating(false)
    }
  }

  const handleSelectGameVersion = (index: number) => {
    setCurrentGameIndex(index)
  }

  const handleGameVersionUpdate = (updatedVersion: GameVersion) => {
    setGameVersions(prev =>
      prev.map(version =>
        version.id === updatedVersion.id ? updatedVersion : version
      )
    )
  }

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* 顶部后端状态检查 */}
      {/* <div className="p-4 bg-white border-b border-gray-200">
        <BackendHealthCheck />
      </div> */}

      <div className="flex-1 overflow-hidden">
        <ResizablePanels
          leftPanel={
            <GamePreview
              gameVersion={currentGameIndex >= 0 ? gameVersions[currentGameIndex] : null}
              isGenerating={isGenerating}
              onGameVersionUpdate={handleGameVersionUpdate}
            />
          }
          rightPanel={
            <div className="h-full flex flex-col">
              <ChatHistory
                messages={messages}
                gameVersions={gameVersions}
                onSelectGameVersion={handleSelectGameVersion}
                currentGameIndex={currentGameIndex}
              />
              <ChatInput
                onSendMessage={handleSendMessage}
                isGenerating={isGenerating}
              />
            </div>
          }
          defaultLeftWidth={70}
          minLeftWidth={40}
          maxLeftWidth={80}
        />
      </div>
    </div>
  )
}