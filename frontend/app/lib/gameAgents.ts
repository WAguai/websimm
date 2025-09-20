import { Message, GameGenerationResult } from '../types'
import { generateGame, checkBackendHealth } from './aiClient'

export class GameAgents {
  constructor() {
    // 不再需要初始化各个Agent，直接调用后端API
  }

  // 多代理协作生成游戏 - 现在通过后端API实现
  public async generateGame(prompt: string, context: Message[] = []): Promise<GameGenerationResult> {
    try {
      console.log('🚀 开始调用后端生成游戏...');
      console.log('📝 用户需求:', prompt);
      
      // 转换context格式
      const contextMessages = context.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp
      }));
      
      // 调用后端API
      const result = await generateGame(prompt, contextMessages);
      
      console.log('✅ 游戏生成完成:', result);
      return result;
      
    } catch (error) {
      console.error('❌ 游戏生成失败:', error);
      throw new Error(`游戏生成过程中出现错误: ${error.message}`);
    }
  }

  // 检查后端服务状态
  public async checkHealth(): Promise<any> {
    try {
      return await checkBackendHealth();
    } catch (error) {
      console.error('❌ 后端服务检查失败:', error);
      throw new Error('后端服务不可用，请检查服务是否启动');
    }
  }
}