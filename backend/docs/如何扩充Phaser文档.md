# 📚 如何扩充Phaser文档到RAG知识库

## 当前状态

您的RAG知识库目前包含 **6个文档**：
- **3个Phaser文档**: Game, Scene, Physics
- **3个Canvas文档**: 基础绘图, 路径绘制, 动画

## 🎯 扩充Phaser文档的三种方法

---

## 方法1: 通过API接口添加（推荐，最简单）

### 1.1 添加单个文档

```bash
curl -X POST http://localhost:8000/api/rag/documents/add \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      "Phaser.Input.Keyboard - 键盘输入\n\n监听键盘事件:\nthis.input.keyboard.on('\''keydown'\'', function(event) {\n    console.log(event.key);\n});\n\n创建按键对象:\nconst spaceKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);\n\n检查按键状态:\nif (spaceKey.isDown) {\n    // 空格键被按下\n}"
    ],
    "metadatas": [
      {
        "source": "phaser",
        "api": "Input.Keyboard",
        "category": "input",
        "version": "3.x"
      }
    ],
    "ids": ["phaser_keyboard_input"]
  }'
```

### 1.2 批量添加多个文档

```bash
curl -X POST http://localhost:8000/api/rag/documents/add \
  -H "Content-Type: application/json" \
  -d @phaser_docs.json
```

**phaser_docs.json 示例**:
```json
{
  "documents": [
    "Phaser.Tweens - 补间动画\n\n创建补间:\nthis.tweens.add({\n    targets: sprite,\n    x: 400,\n    y: 300,\n    duration: 2000,\n    ease: 'Power2'\n});",

    "Phaser.Sound - 音频管理\n\n播放音频:\nconst music = this.sound.add('bgm');\nmusic.play();\n\n控制音量:\nmusic.setVolume(0.5);"
  ],
  "metadatas": [
    {"source": "phaser", "api": "Tweens", "category": "animation"},
    {"source": "phaser", "api": "Sound", "category": "audio"}
  ],
  "ids": ["phaser_tweens", "phaser_sound"]
}
```

### 1.3 查看添加结果

```bash
# 查看知识库统计
curl http://localhost:8000/api/rag/stats

# 测试检索
curl -X POST http://localhost:8000/api/rag/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "如何使用Phaser播放音频",
    "n_results": 3
  }'
```

---

## 方法2: 修改代码添加预置文档（适合批量添加）

编辑文件: `app/services/document_loader.py`

找到 `APIDocumentLoader.load_phaser_docs()` 方法（第324行），在 `phaser_docs` 列表中添加新文档：

```python
@staticmethod
def load_phaser_docs() -> List[Document]:
    """加载Phaser游戏引擎文档"""
    phaser_docs = [
        # 现有的3个文档...

        # ✅ 添加新文档 - Sprite（精灵）
        {
            "content": """
Phaser.GameObjects.Sprite - 精灵对象
精灵是带有纹理的显示对象，是游戏中最常用的对象。

创建精灵:
this.add.sprite(x, y, 'texture_key');

精灵属性:
sprite.x = 100;  // X坐标
sprite.y = 100;  // Y坐标
sprite.scale = 2;  // 缩放（1=原始大小）
sprite.setScale(2, 2);  // 分别设置X和Y缩放
sprite.angle = 45;  // 旋转角度
sprite.alpha = 0.5;  // 透明度（0-1）
sprite.setOrigin(0.5, 0.5);  // 设置锚点（默认中心）

精灵方法:
sprite.setPosition(x, y);  // 设置位置
sprite.setRotation(radians);  // 设置旋转（弧度）
sprite.setVisible(false);  // 隐藏/显示
sprite.destroy();  // 销毁精灵

交互:
sprite.setInteractive();  // 启用交互
sprite.on('pointerdown', () => {
    console.log('Sprite clicked!');
});
            """,
            "metadata": {"source": "phaser", "api": "Sprite", "category": "gameobjects"}
        },

        # ✅ 添加新文档 - Group（组）
        {
            "content": """
Phaser.GameObjects.Group - 游戏对象组
组用于管理多个相同类型的游戏对象。

创建组:
const group = this.add.group();

添加对象到组:
group.add(sprite);
group.addMultiple([sprite1, sprite2, sprite3]);

批量创建:
const enemies = this.add.group({
    key: 'enemy',
    repeat: 10,
    setXY: { x: 100, y: 100, stepX: 70 }
});

遍历组:
group.children.iterate((child) => {
    child.x += 1;
});

碰撞检测:
this.physics.add.collider(player, group);

清空组:
group.clear(true, true);  // (removeFromScene, destroyChild)
            """,
            "metadata": {"source": "phaser", "api": "Group", "category": "gameobjects"}
        },

        # ✅ 添加新文档 - Tilemap（瓦片地图）
        {
            "content": """
Phaser.Tilemaps - 瓦片地图系统
用于创建基于瓦片的游戏世界。

加载瓦片地图:
this.load.image('tiles', 'assets/tileset.png');
this.load.tilemapTiledJSON('map', 'assets/map.json');

创建地图:
const map = this.make.tilemap({ key: 'map' });
const tileset = map.addTilesetImage('tileset_name', 'tiles');
const layer = map.createLayer('layer_name', tileset, 0, 0);

碰撞:
layer.setCollisionByProperty({ collides: true });
this.physics.add.collider(player, layer);

动态修改瓦片:
map.putTileAt(tile_index, x, y, true, layer);
map.removeTileAt(x, y, true, true, layer);

查找瓦片:
const tile = map.getTileAt(x, y, true, layer);
            """,
            "metadata": {"source": "phaser", "api": "Tilemap", "category": "tilemap"}
        },

        # ✅ 添加新文档 - Cameras（摄像机）
        {
            "content": """
Phaser.Cameras - 摄像机系统
控制游戏视角和特效。

主摄像机:
const camera = this.cameras.main;

摄像机跟随:
camera.startFollow(player);
camera.startFollow(player, true, 0.1, 0.1);  // 平滑跟随

摄像机边界:
camera.setBounds(0, 0, mapWidth, mapHeight);

摄像机特效:
camera.shake(500, 0.01);  // 震动（持续时间, 强度）
camera.flash(250);  // 闪烁
camera.fade(1000, 0, 0, 0);  // 淡出到黑色

缩放和旋转:
camera.setZoom(2);  // 放大2倍
camera.rotation = Math.PI / 4;  // 旋转45度

多摄像机:
const minimap = this.cameras.add(600, 0, 200, 200);
minimap.setZoom(0.2);
            """,
            "metadata": {"source": "phaser", "api": "Camera", "category": "camera"}
        },

        # ✅ 添加新文档 - Particles（粒子系统）
        {
            "content": """
Phaser.GameObjects.Particles - 粒子系统
创建视觉特效如爆炸、烟雾、火焰等。

创建粒子发射器:
const particles = this.add.particles('particle_texture');

const emitter = particles.createEmitter({
    speed: { min: -100, max: 100 },
    angle: { min: 0, max: 360 },
    scale: { start: 1, end: 0 },
    alpha: { start: 1, end: 0 },
    lifespan: 1000,
    blendMode: 'ADD'
});

控制发射器:
emitter.start();
emitter.stop();
emitter.explode(16, x, y);  // 爆炸效果（粒子数, x, y）

跟随对象:
emitter.startFollow(player);

粒子区域:
emitter.setEmitZone({
    type: 'random',
    source: new Phaser.Geom.Circle(0, 0, 100)
});
            """,
            "metadata": {"source": "phaser", "api": "Particles", "category": "effects"}
        },

        # ✅ 添加新文档 - Text（文本）
        {
            "content": """
Phaser.GameObjects.Text - 文本对象
显示游戏中的文字信息。

创建文本:
const text = this.add.text(x, y, 'Hello World', {
    fontSize: '32px',
    fontFamily: 'Arial',
    color: '#ffffff',
    backgroundColor: '#000000',
    padding: { x: 10, y: 5 },
    align: 'center'
});

更新文本:
text.setText('New Text');
text.text = 'Another way';

样式设置:
text.setStyle({
    fontSize: '48px',
    fontStyle: 'bold',
    color: '#ff0000'
});

文本效果:
text.setShadow(2, 2, '#000000', 2, false, true);
text.setStroke('#000000', 4);

动态文本:
let score = 0;
const scoreText = this.add.text(16, 16, 'Score: 0', { fontSize: '24px' });

function updateScore() {
    score += 10;
    scoreText.setText('Score: ' + score);
}
            """,
            "metadata": {"source": "phaser", "api": "Text", "category": "gameobjects"}
        }
    ]

    # 转换为Document对象
    documents = []
    for i, doc_data in enumerate(phaser_docs):
        documents.append(Document(
            content=doc_data["content"].strip(),
            metadata=doc_data["metadata"],
            id=f"phaser_doc_{i}"
        ))

    logger.info(f"✅ 加载了 {len(documents)} 个Phaser文档")
    return documents
```

### 重新初始化知识库

修改代码后，需要重置并重新加载知识库：

```bash
# 1. 重置知识库
curl -X POST http://localhost:8000/api/rag/reset

# 2. 重新初始化
curl -X POST http://localhost:8000/api/rag/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "load_phaser_docs": true,
    "load_canvas_docs": true
  }'

# 3. 验证文档数量
curl http://localhost:8000/api/rag/stats
```

---

## 方法3: 从外部文件批量导入

### 3.1 准备文档目录

创建一个文档目录，例如 `/Users/yuzhong/Projects/Agents/websimm/backend/docs/phaser_api/`

```
phaser_api/
├── sprite.md
├── physics.md
├── input.md
├── animation.md
└── tilemap.md
```

### 3.2 文档格式示例

**sprite.md**:
```markdown
# Phaser.GameObjects.Sprite - 精灵对象

精灵是带有纹理的显示对象，是游戏中最常用的对象。

## 创建精灵

```javascript
this.add.sprite(x, y, 'texture_key');
```

## 精灵属性

- `sprite.x` - X坐标
- `sprite.y` - Y坐标
- `sprite.scale` - 缩放
- `sprite.angle` - 旋转角度
- `sprite.alpha` - 透明度（0-1）

## 精灵方法

```javascript
sprite.setPosition(x, y);
sprite.setRotation(radians);
sprite.setVisible(false);
sprite.destroy();
```

## 交互

```javascript
sprite.setInteractive();
sprite.on('pointerdown', () => {
    console.log('Sprite clicked!');
});
```
```

### 3.3 通过API导入

```bash
curl -X POST http://localhost:8000/api/rag/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "load_phaser_docs": true,
    "load_canvas_docs": true,
    "custom_docs_path": "/Users/yuzhong/Projects/Agents/websimm/backend/docs/phaser_api"
  }'
```

---

## 📝 文档格式规范

### 好的文档示例

```markdown
API名称 - 简短描述

详细说明...

使用方法:
代码示例1

属性/参数:
- 属性1: 说明
- 属性2: 说明

示例:
完整代码示例

注意事项:
- 注意事项1
- 注意事项2
```

### 元数据字段说明

```json
{
  "source": "phaser",           // 来源：phaser/canvas/three等
  "api": "Sprite",              // API名称
  "category": "gameobjects",    // 分类：core/physics/input/audio等
  "version": "3.x",             // 可选：版本号
  "difficulty": "beginner"      // 可选：难度级别
}
```

---

## 🎯 推荐添加的Phaser API文档

根据游戏开发需求，建议优先添加以下API文档：

### 核心类
- ✅ Game (已有)
- ✅ Scene (已有)
- ⬜ Config (游戏配置)
- ⬜ Events (事件系统)

### 游戏对象
- ⬜ Sprite (精灵) - **高优先级**
- ⬜ Image (图像)
- ⬜ Graphics (矢量图形)
- ⬜ Text (文本) - **高优先级**
- ⬜ Container (容器)
- ⬜ Group (组) - **高优先级**

### 物理引擎
- ✅ Arcade Physics (已有)
- ⬜ Matter Physics
- ⬜ Body (物理体)

### 输入
- ⬜ Keyboard (键盘) - **高优先级**
- ⬜ Mouse (鼠标)
- ⬜ Touch (触摸)
- ⬜ Pointer (指针)

### 动画
- ⬜ Animations (帧动画) - **高优先级**
- ⬜ Tweens (补间动画) - **高优先级**

### 音频
- ⬜ Sound (音频管理) - **高优先级**
- ⬜ AudioSprite (音频精灵)

### 瓦片地图
- ⬜ Tilemap (瓦片地图) - **中优先级**
- ⬜ TilemapLayer (地图层)

### 摄像机
- ⬜ Camera (摄像机) - **中优先级**
- ⬜ CameraEffects (摄像机特效)

### 特效
- ⬜ Particles (粒子系统)
- ⬜ Lights (光照)

### 资源加载
- ⬜ LoaderPlugin (资源加载) - **高优先级**
- ⬜ TextureManager (纹理管理)

---

## 🧪 测试和验证

### 1. 添加文档后测试检索

```bash
# 测试Phaser相关查询
curl -X POST http://localhost:8000/api/rag/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "如何在Phaser中创建精灵并添加点击事件",
    "n_results": 3
  }'

# 测试物理引擎查询
curl -X POST http://localhost:8000/api/rag/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Phaser物理引擎碰撞检测",
    "n_results": 3
  }'
```

### 2. 完整系统测试

```bash
curl http://localhost:8000/api/rag/test
```

### 3. 实际游戏生成测试

```bash
curl -X POST http://localhost:8000/api/game/new \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "使用Phaser创建一个简单的平台跳跃游戏，包含角色移动、跳跃和简单的平台"
  }'
```

检查生成的代码是否使用了您添加的API文档中的知识。

---

## 💡 最佳实践

### 1. 文档内容建议

- **包含代码示例**: 每个API都应该有实际可运行的代码示例
- **说明参数**: 清楚标注每个参数的类型和作用
- **提供完整示例**: 不要只给API签名，要给完整的使用场景
- **注意版本**: 如果API在不同版本有差异，要标注版本号

### 2. 文档组织建议

- **按类别分组**: 将相关的API放在一起（如所有Input相关的）
- **从简单到复杂**: 先添加基础常用的API
- **包含常见模式**: 添加常见的游戏开发模式（如对象池、状态机等）

### 3. 元数据建议

- **统一命名**: source字段统一使用小写（phaser, canvas, three等）
- **清晰分类**: category字段使用明确的分类（core, physics, input, audio等）
- **添加标签**: 可以在metadata中添加tags字段帮助检索

### 4. 增量添加

不要一次添加太多文档，建议：
1. 先添加5-10个最常用的API
2. 测试游戏生成效果
3. 根据实际需求逐步补充

---

## 🔍 查看当前文档

```bash
# 查看统计信息
curl http://localhost:8000/api/rag/stats

# 查看健康状态
curl http://localhost:8000/api/rag/health

# 检索测试（查看有哪些文档）
curl -X POST http://localhost:8000/api/rag/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Phaser",
    "n_results": 10
  }'
```

---

## ❓ 常见问题

### Q1: 添加文档后检索不到？
A: 检查文档ID是否重复，重复ID会覆盖旧文档。建议使用唯一的ID如 `phaser_sprite_v1`。

### Q2: 如何删除错误的文档？
A: 目前需要重置整个知识库，然后重新添加正确的文档：
```bash
curl -X POST http://localhost:8000/api/rag/reset
curl -X POST http://localhost:8000/api/rag/initialize ...
```

### Q3: 文档太长会影响检索吗？
A: 文档会自动分块（chunk_size=1000字符），长文档会被分成多个小块存储。

### Q4: 如何确认文档被使用了？
A: 查看游戏生成时的后端日志，会显示RAG检索结果和使用的文档。

---

## 📚 参考资源

- [Phaser 3 官方文档](https://photonstorm.github.io/phaser3-docs/)
- [Phaser 3 示例](https://phaser.io/examples)
- [Canvas MDN文档](https://developer.mozilla.org/zh-CN/docs/Web/API/Canvas_API)
- 项目代码位置：
  - RAG服务: `app/services/rag_service.py`
  - 文档加载器: `app/services/document_loader.py`
  - RAG路由: `app/routers/rag_routes.py`

---

**最后更新**: 2025-12-18
**文档版本**: 1.0
