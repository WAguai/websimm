#!/usr/bin/env python3
"""
测试单HTML文件生成功能
"""

import asyncio
import sys
from pathlib import Path

# 添加app目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "app"))

async def test_single_file_generation():
    """测试单HTML文件生成"""
    try:
        from app.services.game_service import game_service
        
        print("🧪 开始测试单HTML文件生成...")
        
        # 测试游戏生成
        prompt = "创建一个简单的贪吃蛇游戏"
        print(f"📝 测试提示: {prompt}")
        
        result = await game_service.generate_game(prompt, [])
        
        print(f"\n✅ 生成成功!")
        print(f"📊 结果统计:")
        print(f"  - HTML文件大小: {len(result.files.html)} 字符")
        print(f"  - 游戏标题: {result.game_logic}")
        print(f"  - 游戏描述: {result.description}")
        print(f"  - 图像资源数量: {len(result.image_resources)}")
        print(f"  - 音频资源数量: {len(result.audio_resources)}")
        print(f"  - 文件类型: 单个HTML文件（自包含）")
        
        # 保存HTML文件用于测试
        output_file = Path(__file__).parent / "test_game.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.files.html)
        
        print(f"\n💾 HTML文件已保存到: {output_file}")
        print(f"🌐 可以在浏览器中打开测试: file://{output_file.absolute()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_single_file_generation())
    if success:
        print("\n🎉 单HTML文件生成测试通过!")
    else:
        print("\n💥 测试失败，请检查配置和代码。")
        sys.exit(1)