from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # AI API配置
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True  
    
    # CORS配置
    frontend_url: str = "http://localhost:3000"
    
    # 模型配置
    default_model: str = "claude-sonnet-4-20250514"
    
    # MongoDB配置
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db_name: str = "game_generation"
    
    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


# 全局配置实例
try:
    settings = Settings()
    print(f"✅ 配置加载成功")
    print(f"📁 .env 文件路径: {BASE_DIR / '.env'}")
    print(f"🔑 API Key 已配置: {'是' if settings.openai_api_key else '否'}")
    print(f"🌐 Base URL: {settings.openai_base_url}")
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    print(f"📁 请检查 .env 文件是否存在: {BASE_DIR / '.env'}")
    raise