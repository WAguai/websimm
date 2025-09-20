# 前端集成示例

## 修改前端调用方式

将原来直接调用AI接口的方式改为调用Python后端API。

### 1. 更新 aiClient.ts

```typescript
// frontend/app/lib/aiClient.ts
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function generateGame(prompt: string, context: any[] = []) {
  try {
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
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || '游戏生成失败');
    }
    
    return data.data;
  } catch (error) {
    console.error('游戏生成失败:', error);
    throw error;
  }
}

// 健康检查
export async function checkBackendHealth() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/game/health`);
    return await response.json();
  } catch (error) {
    console.error('后端健康检查失败:', error);
    throw error;
  }
}
```

### 2. 更新 GameAgents 类

```typescript
// frontend/app/lib/gameAgents.ts
import { generateGame } from './aiClient';
import { GameGenerationResult } from '../types';

export class GameAgents {
  // 简化为单一接口调用
  public async generateGame(prompt: string, context: any[] = []): Promise<GameGenerationResult> {
    try {
      console.log('🚀 开始调用后端生成游戏...');
      
      const result = await generateGame(prompt, context);
      
      console.log('✅ 游戏生成完成:', result);
      return result;
      
    } catch (error) {
      console.error('❌ 游戏生成失败:', error);
      throw new Error('游戏生成过程中出现错误');
    }
  }
}
```

### 3. 环境变量配置

在 `frontend/.env.local` 中添加：

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 4. 使用示例

```typescript
// 在React组件中使用
import { GameAgents } from '../lib/gameAgents';

const gameAgents = new GameAgents();

const handleGenerateGame = async () => {
  try {
    setLoading(true);
    
    const result = await gameAgents.generateGame(userPrompt);
    
    // 处理生成结果
    setGameFiles(result.files);
    setDescription(result.description);
    
  } catch (error) {
    setError(error.message);
  } finally {
    setLoading(false);
  }
};
```

## 优势

✅ **前后端分离** - 清晰的架构边界
✅ **统一错误处理** - 后端统一处理AI接口异常
✅ **更好的日志** - 后端提供详细的执行日志
✅ **易于扩展** - 可以轻松添加新的Agent
✅ **性能优化** - 后端可以进行缓存和优化
✅ **安全性** - API密钥不暴露给前端

## 迁移步骤

1. 启动Python后端服务
2. 更新前端的API调用代码
3. 删除前端中的AI接口调用逻辑
4. 测试完整的前后端交互
5. 部署到生产环境