// AI Client - 调用Python后端API
"use client";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function generateGame(prompt: string, context: any[] = []) {
  try {
    console.log('🚀 调用后端生成游戏...', { prompt, context });
    
    const response = await fetch(`${BACKEND_URL}/api/game/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        prompt,
        context
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    console.log('📦 后端响应:', data);
    
    if (!data.success) {
      throw new Error(data.error || '游戏生成失败');
    }
    
    return data.data;
  } catch (error) {
    console.error('❌ 游戏生成失败:', error);
    throw error;
  }
}

// 健康检查
export async function checkBackendHealth() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/game/health`);
    const data = await response.json();
    console.log('💚 后端健康状态:', data);
    return data;
  } catch (error) {
    console.error('❌ 后端健康检查失败:', error);
    throw error;
  }
}

// 兼容性函数 - 保持向后兼容
export async function getGameLogic(systemMessage: string, userMessage: string, previousChatId: string | null = null) {
  console.warn('⚠️ getGameLogic已废弃，请使用generateGame');
  return generateGame(userMessage, []);
}

export async function getGameFiles(systemMessage: string, userMessage: string, previousChatId: string | null = null) {
  console.warn('⚠️ getGameFiles已废弃，请使用generateGame');
  return generateGame(userMessage, []);
}

export async function getImageResources(systemMessage: string, userMessage: string, previousChatId: string | null = null) {
  console.warn('⚠️ getImageResources已废弃，请使用generateGame');
  return generateGame(userMessage, []);
}

export async function getAudioResources(systemMessage: string, userMessage: string, previousChatId: string | null = null) {
  console.warn('⚠️ getAudioResources已废弃，请使用generateGame');
  return generateGame(userMessage, []);
}


