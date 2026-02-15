#!/bin/bash

# 添加Phaser文档到RAG知识库的快捷脚本

echo "🚀 开始添加Phaser文档到RAG知识库..."

# 检查后端是否运行
if ! curl -s http://localhost:8000/api/rag/health > /dev/null; then
    echo "❌ 后端服务未运行，请先启动后端"
    exit 1
fi

# 显示当前统计
echo ""
echo "📊 当前知识库状态:"
curl -s http://localhost:8000/api/rag/stats | python3 -m json.tool

# 询问是否添加文档
echo ""
read -p "是否添加新的Phaser文档? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 添加文档
echo ""
echo "📚 正在添加文档..."
DOCS_FILE="../docs/phaser_docs_template.json"

if [ ! -f "$DOCS_FILE" ]; then
    echo "❌ 找不到文档文件: $DOCS_FILE"
    exit 1
fi

RESPONSE=$(curl -s -X POST http://localhost:8000/api/rag/documents/add \
  -H "Content-Type: application/json" \
  -d @"$DOCS_FILE")

echo "$RESPONSE" | python3 -m json.tool

# 显示更新后的统计
echo ""
echo "📊 更新后的知识库状态:"
curl -s http://localhost:8000/api/rag/stats | python3 -m json.tool

# 测试检索
echo ""
echo "🔍 测试检索..."
curl -s -X POST http://localhost:8000/api/rag/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "如何在Phaser中播放音频",
    "n_results": 2
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('检索结果:')
for i, doc in enumerate(data['documents']):
    print(f'\n[文档 {i+1}]')
    print(doc[:200] + '...' if len(doc) > 200 else doc)
"

echo ""
echo "✅ 完成！"
