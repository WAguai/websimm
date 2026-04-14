from typing import Dict, List, Any


CAPABILITY_SPECS: List[Dict[str, Any]] = [
    {
        "name": "retrieve_reference_context",
        "description": "检索与用户需求相关的API与实现文档",
        "inputs": ["user_prompt"],
        "outputs": ["reference_context"],
        "when_to_use": ["需要RAG增强", "用户要求特定框架或API"],
        "acceptance": ["reference_context_ready"],
        "default_agent": "RAGAgent",
    },
    {
        "name": "game_logic_generation",
        "description": "生成结构化玩法规则和核心逻辑",
        "inputs": ["user_prompt", "reference_context"],
        "outputs": ["logic_spec"],
        "when_to_use": ["需要生成游戏玩法"],
        "acceptance": ["logic_complete"],
        "default_agent": "GameLogicAgent",
    },
    {
        "name": "game_code_generation",
        "description": "根据logic_spec生成可运行HTML/JS代码",
        "inputs": ["logic_spec", "reference_context", "skills_guidance"],
        "outputs": ["html_code"],
        "when_to_use": ["需要生成游戏代码"],
        "acceptance": ["code_generated", "html_structure_valid"],
        "default_agent": "GameCodeAgent",
    },
    {
        "name": "asset_generation",
        "description": "生成图像资源清单",
        "inputs": ["logic_spec"],
        "outputs": ["image_manifest"],
        "when_to_use": ["需要图像资源"],
        "acceptance": ["assets_ready"],
        "default_agent": "AssetAgent",
    },
    {
        "name": "audio_generation",
        "description": "生成音频资源清单",
        "inputs": ["logic_spec"],
        "outputs": ["audio_manifest"],
        "when_to_use": ["需要音频资源"],
        "acceptance": ["audio_ready"],
        "default_agent": "AudioAgent",
    },
    {
        "name": "review_and_validate",
        "description": "校验可运行性、引用完整性、需求匹配度",
        "inputs": ["logic_spec", "html_code", "image_manifest", "audio_manifest"],
        "outputs": ["review_report"],
        "when_to_use": ["最终交付前"],
        "acceptance": ["review_passed"],
        "default_agent": "ReviewAgent",
    },
]

