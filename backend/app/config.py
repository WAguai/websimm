from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Anthropic API配置（可选，用于 Claude 模型）
    anthropic_api_key: Optional[str] = None
    anthropic_base_url: str = "https://api.anthropic.com"
    
    # Kimi (Moonshot) API配置 - OpenAI 兼容接口
    kimi_api_key: Optional[str] = None
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    
    # 服务配置
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True  
    
    # CORS配置
    frontend_url: str = "http://localhost:3000"
    
    # 模型配置：provider 为 kimi 或 anthropic
    default_model_provider: str = "kimi"
    default_model: str = "kimi-k2-turbo-preview"
    
    # MongoDB配置
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db_name: str = "game_generation"
    
    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    def get_available_models(self) -> List[dict]:
        """返回可用的模型列表"""
        models = []
        if self.kimi_api_key:
            models.extend([
                {"id": "kimi-k2-turbo-preview", "name": "Kimi K2 Turbo", "provider": "kimi"},
                {"id": "moonshot-v1-8k", "name": "Moonshot 8K", "provider": "kimi"},
                {"id": "moonshot-v1-32k", "name": "Moonshot 32K", "provider": "kimi"},
            ])
        if self.anthropic_api_key:
            models.extend([
                {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "provider": "anthropic"},
            ])
        if not models:
            models.append({"id": self.default_model, "name": self.default_model, "provider": self.default_model_provider})
        return models


# 全局配置实例
try:
    settings = Settings()
    print(f"✅ 配置加载成功")
    print(f"📁 .env 文件路径: {BASE_DIR / '.env'}")
    api_status = []
    if settings.kimi_api_key:
        api_status.append("Kimi")
    if settings.anthropic_api_key:
        api_status.append("Anthropic")
    print(f"🔑 已配置 API: {', '.join(api_status) or '无'}")
    print(f"🤖 默认模型: {settings.default_model} ({settings.default_model_provider})")
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    print(f"📁 请检查 .env 文件是否存在: {BASE_DIR / '.env'}")
    raise