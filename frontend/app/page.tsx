'use client'

import { useState, useRef, useEffect } from 'react'
import GamePreview from './components/GamePreview'
import ChatHistory from './components/ChatHistory'
import ChatInput from './components/ChatInput'
import BackendHealthCheck from './components/BackendHealthCheck'
import ResizablePanels from './components/ResizablePanels'
import ConversationModal from './components/ConversationModal'
import { ConversationApi } from './lib/conversationApi'
import { Message, GameVersion, ConversationSummary, BackendMessage, NewGameResponse, HistoryBasedGameResponse, ModelInfo } from './types'
export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [models, setModels] = useState<ModelInfo[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [gameVersions, setGameVersions] = useState<GameVersion[]>([])
  const [currentGameIndex, setCurrentGameIndex] = useState<number>(-1)
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentConversationId, setCurrentConversationId] = useState<string>('')
  const [currentParentMessageId, setCurrentParentMessageId] = useState<string>('')
  const [showConversationModal, setShowConversationModal] = useState(false)
  const requestInProgress = useRef(false)  // 防止重复请求

  // 加载可用模型列表
  useEffect(() => {
    ConversationApi.getModels()
      .then(({ models: m, default: d }) => {
        setModels(m)
        setSelectedModel(d || (m[0]?.id ?? ''))
      })
      .catch(console.error)
  }, [])

  const handleSendMessage = async (content: string) => {
    // 防止重复请求
    if (requestInProgress.current) {
      console.log('Request already in progress, ignoring duplicate call')
      return
    }

    requestInProgress.current = true

    // 创建用户消息显示
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }

    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setIsGenerating(true)

    try {
      let gameResponse: NewGameResponse | HistoryBasedGameResponse

      if (!currentConversationId || !currentParentMessageId) {
        // 新游戏对话
        gameResponse = await ConversationApi.createNewGame({ user_prompt: content, model: selectedModel || undefined })

        // 更新对话状态
        setCurrentConversationId(gameResponse.conversation_id)
        setCurrentParentMessageId(gameResponse.message_id)
      } else {
        // 基于历史的游戏生成
        gameResponse = await ConversationApi.createHistoryBasedGame({
          conversation_id: currentConversationId,
          parent_message_id: currentParentMessageId,
          user_prompt: content,
          model: selectedModel || undefined
        })

        // 更新父消息ID
        setCurrentParentMessageId(gameResponse.message_id)
      }

      // 创建AI回复消息
      const aiMessage: Message = {
        id: gameResponse.message_id,
        role: 'assistant',
        content: `已生成游戏：${gameResponse.game_data.title}`,
        timestamp: new Date()
      }

      // 创建游戏版本
      const newGameVersion: GameVersion = {
        id: gameVersions.length,
        files: { html: gameResponse.game_data.html_content },
        description: gameResponse.game_data.description,
        userPrompt: content,
        timestamp: new Date(),
        messageId: gameResponse.message_id
      }

      const finalMessages = [...newMessages, aiMessage]
      setMessages(finalMessages)
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
      requestInProgress.current = false  // 重置请求状态
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

  // 处理选择对话
  const handleSelectConversation = async (conversationId: string) => {
    try {
      // 获取对话详细数据
      const conversationFull = await ConversationApi.getConversationFull(conversationId)

      setCurrentConversationId(conversationFull.conversation_id)

      // 转换消息格式，每个后端消息对应一对用户-助手消息
      const loadedMessages: Message[] = []
      const loadedGameVersions: GameVersion[] = []

      conversationFull.messages.forEach((backendMsg, index) => {
        // 用户消息
        const userMessage: Message = {
          id: `${backendMsg.message_id}_user`,
          role: 'user',
          content: backendMsg.user_prompt,
          timestamp: new Date(backendMsg.timestamp)
        }
        loadedMessages.push(userMessage)

        // 助手消息
        const assistantMessage: Message = {
          id: backendMsg.message_id,
          role: 'assistant',
          content: `已生成游戏：${backendMsg.game_data.title}`,
          timestamp: new Date(backendMsg.timestamp)
        }
        loadedMessages.push(assistantMessage)

        // 创建游戏版本
        const gameVersion: GameVersion = {
          id: index,
          files: { html: backendMsg.game_data.html_content },
          description: backendMsg.game_data.description,
          userPrompt: backendMsg.user_prompt,
          timestamp: new Date(backendMsg.timestamp),
          messageId: backendMsg.message_id
        }
        loadedGameVersions.push(gameVersion)
      })

      setMessages(loadedMessages)
      setGameVersions(loadedGameVersions)
      setCurrentGameIndex(loadedGameVersions.length > 0 ? loadedGameVersions.length - 1 : -1)

      // 设置最后一个消息为父消息ID（用于继续对话）
      if (conversationFull.messages.length > 0) {
        const lastMessage = conversationFull.messages[conversationFull.messages.length - 1]
        setCurrentParentMessageId(lastMessage.message_id)
      }

    } catch (error) {
      console.error('加载对话失败:', error)
    }
  }

  // 处理新对话
  const handleNewConversation = () => {
    setCurrentConversationId('')
    setCurrentParentMessageId('')
    setMessages([])
    setGameVersions([])
    setCurrentGameIndex(-1)
    // 对话会在第一次发送消息时自动创建
  }

  // 打开对话选择模态框
  const handleOpenConversations = () => {
    setShowConversationModal(true)
  }

  // 关闭对话选择模态框
  const handleCloseConversations = () => {
    setShowConversationModal(false)
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
                onOpenConversations={handleOpenConversations}
                models={models}
                selectedModel={selectedModel}
                onModelChange={setSelectedModel}
              />
            </div>
          }
          defaultLeftWidth={70}
          minLeftWidth={40}
          maxLeftWidth={80}
        />
      </div>

      {/* 对话选择模态框 */}
      <ConversationModal
        isOpen={showConversationModal}
        onClose={handleCloseConversations}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />
    </div>
  )
}