#!/usr/bin/env python3
"""
测试配置加载脚本
"""

import os
import sys
from pathlib import Path

# 添加app目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_env_file():
    """测试.env文件是否存在和可读"""
    env_file = Path(__file__).parent / ".env"
    print(f"🔍 检查 .env 文件: {env_file}")
    
    if not env_file.exists():
        print(f"❌ .env 文件不存在")
        return False
    
    print(f"✅ .env 文件存在")
    
    # 读取并显示内容（隐藏敏感信息）
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📄 .env 文件内容:")
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            key, _, value = line.partition('=')
            if 'KEY' in key.upper():
                print(f"  {key}=***隐藏***")
            else:
                print(f"  {key}={value}")
    
    return True

def test_pydantic_settings():
    """测试Pydantic Settings加载"""
    try:
        from app.config import settings
        print(f"\n✅ Pydantic Settings 加载成功")
        print(f"🔑 API Key 长度: {len(settings.openai_api_key) if settings.openai_api_key else 0}")
        print(f"🌐 Base URL: {settings.openai_base_url}")
        print(f"🖥️  Host: {settings.host}")
        print(f"🔌 Port: {settings.port}")
        return True
    except Exception as e:
        print(f"❌ Pydantic Settings 加载失败: {e}")
        return False

def test_direct_env():
    """直接测试环境变量"""
    print(f"\n🔍 直接检查环境变量:")
    
    # 手动加载.env文件
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    os.environ[key] = value
    
    # 检查关键环境变量
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL')
    
    print(f"  OPENAI_API_KEY: {'已设置' if api_key else '未设置'} (长度: {len(api_key) if api_key else 0})")
    print(f"  OPENAI_BASE_URL: {base_url}")
    
    return bool(api_key)

if __name__ == "__main__":
    print("🧪 开始配置测试...\n")
    
    # 测试步骤
    step1 = test_env_file()
    step2 = test_direct_env()
    step3 = test_pydantic_settings()
    
    print(f"\n📊 测试结果:")
    print(f"  .env 文件: {'✅' if step1 else '❌'}")
    print(f"  环境变量: {'✅' if step2 else '❌'}")
    print(f"  Pydantic: {'✅' if step3 else '❌'}")
    
    if all([step1, step2, step3]):
        print(f"\n🎉 所有测试通过！配置正确。")
    else:
        print(f"\n⚠️  存在配置问题，请检查上述错误。")