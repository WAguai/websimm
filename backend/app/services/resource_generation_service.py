import base64
import io
from typing import List, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ResourceGenerationService:
    """资源生成服务 - 生成高质量的游戏资源"""
    
    def __init__(self):
        self.color_palettes = {
            "像素风格": ["#FF6B35", "#F7931E", "#FFD23F", "#06FFA5", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
            "卡通风格": ["#FF7675", "#74B9FF", "#00B894", "#FDCB6E", "#6C5CE7", "#FD79A8", "#55A3FF", "#A29BFE"],
            "现代风格": ["#2D3436", "#636E72", "#B2BEC3", "#DDD", "#74B9FF", "#00B894", "#FDCB6E", "#E17055"],
            "简约风格": ["#2C3E50", "#3498DB", "#E74C3C", "#F39C12", "#27AE60", "#9B59B6", "#1ABC9C", "#E67E22"]
        }
    
    def generate_game_images(
        self, 
        game_type: str, 
        visual_style: str, 
        game_elements: List[str]
    ) -> List[str]:
        """生成游戏图像资源"""
        try:
            images = []
            colors = self.color_palettes.get(visual_style, self.color_palettes["现代风格"])
            
            # 根据游戏元素生成不同的图像
            if "玩家角色" in game_elements:
                player_image = self._create_player_sprite(colors, visual_style)
                images.append(player_image)
            
            if "敌人" in game_elements:
                enemy_image = self._create_enemy_sprite(colors, visual_style)
                images.append(enemy_image)
            
            if "道具系统" in game_elements:
                item_image = self._create_item_sprite(colors, visual_style)
                images.append(item_image)
            
            # 根据游戏类型生成特定资源
            if "platform" in game_type.lower() or "平台" in game_type:
                platform_image = self._create_platform_sprite(colors, visual_style)
                images.append(platform_image)
            
            # 生成UI元素
            ui_images = self._create_ui_elements(colors, visual_style)
            images.extend(ui_images)
            
            logger.info(f"✅ 生成了 {len(images)} 个图像资源")
            return images
            
        except Exception as e:
            logger.error(f"❌ 图像资源生成失败: {str(e)}")
            return self._get_fallback_images()
    
    def _create_player_sprite(self, colors: List[str], style: str) -> str:
        """创建玩家精灵图"""
        if style == "像素风格":
            return self._create_pixel_sprite(32, 32, colors[0], "P")
        else:
            return self._create_smooth_sprite(32, 32, colors[0], "👤")
    
    def _create_enemy_sprite(self, colors: List[str], style: str) -> str:
        """创建敌人精灵图"""
        if style == "像素风格":
            return self._create_pixel_sprite(32, 32, colors[2], "E")
        else:
            return self._create_smooth_sprite(32, 32, colors[2], "👾")
    
    def _create_item_sprite(self, colors: List[str], style: str) -> str:
        """创建道具精灵图"""
        if style == "像素风格":
            return self._create_pixel_sprite(16, 16, colors[3], "★")
        else:
            return self._create_smooth_sprite(16, 16, colors[3], "💎")
    
    def _create_platform_sprite(self, colors: List[str], style: str) -> str:
        """创建平台精灵图"""
        width, height = 64, 16
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 根据风格绘制平台
        if style == "像素风格":
            # 像素风格的方块平台
            draw.rectangle([0, 0, width-1, height-1], fill=colors[1], outline=colors[4])
            # 添加像素细节
            for x in range(0, width, 4):
                draw.line([x, 0, x, height-1], fill=colors[4], width=1)
        else:
            # 现代风格的圆角平台
            draw.rounded_rectangle([0, 0, width-1, height-1], radius=4, fill=colors[1])
            # 添加渐变效果
            for y in range(height//2):
                alpha = int(255 * (1 - y / (height//2)) * 0.3)
                overlay = Image.new('RGBA', (width, 1), (*self._hex_to_rgb(colors[5]), alpha))
                img.paste(overlay, (0, y), overlay)
        
        return self._image_to_base64(img)
    
    def _create_ui_elements(self, colors: List[str], style: str) -> List[str]:
        """创建UI元素"""
        ui_elements = []
        
        # 创建按钮
        button_img = self._create_button(colors[0], style)
        ui_elements.append(button_img)
        
        # 创建分数板背景
        scoreboard_img = self._create_scoreboard_bg(colors[6], style)
        ui_elements.append(scoreboard_img)
        
        return ui_elements
    
    def _create_button(self, color: str, style: str) -> str:
        """创建按钮UI"""
        width, height = 80, 30
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if style == "像素风格":
            draw.rectangle([0, 0, width-1, height-1], fill=color, outline="#FFF")
        else:
            draw.rounded_rectangle([0, 0, width-1, height-1], radius=6, fill=color)
            # 添加高光效果
            highlight = Image.new('RGBA', (width, height//3), (*self._hex_to_rgb("#FFFFFF"), 50))
            img.paste(highlight, (0, 0), highlight)
        
        return self._image_to_base64(img)
    
    def _create_scoreboard_bg(self, color: str, style: str) -> str:
        """创建分数板背景"""
        width, height = 120, 40
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if style == "像素风格":
            draw.rectangle([0, 0, width-1, height-1], fill=color, outline="#000")
        else:
            draw.rounded_rectangle([0, 0, width-1, height-1], radius=8, fill=color)
            # 添加边框
            draw.rounded_rectangle([1, 1, width-2, height-2], radius=7, outline="#FFF", width=1)
        
        return self._image_to_base64(img)
    
    def _create_pixel_sprite(self, width: int, height: int, color: str, text: str = "") -> str:
        """创建像素风格精灵"""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 创建像素化的方形
        pixel_size = max(1, min(width, height) // 8)
        for x in range(0, width, pixel_size):
            for y in range(0, height, pixel_size):
                if (x + y) % (pixel_size * 2) == 0:
                    draw.rectangle([x, y, x+pixel_size-1, y+pixel_size-1], fill=color)
        
        # 添加边框
        draw.rectangle([0, 0, width-1, height-1], outline="#000", width=1)
        
        # 添加文本
        if text:
            try:
                font_size = max(8, min(width, height) // 3)
                draw.text((width//2, height//2), text, fill="#FFF", anchor="mm")
            except:
                pass
        
        return self._image_to_base64(img)
    
    def _create_smooth_sprite(self, width: int, height: int, color: str, emoji: str = "") -> str:
        """创建平滑风格精灵"""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 创建圆形或椭圆形
        padding = 2
        draw.ellipse([padding, padding, width-padding-1, height-padding-1], fill=color)
        
        # 添加高光
        highlight_size = max(width, height) // 4
        draw.ellipse([
            padding + highlight_size//2, 
            padding + highlight_size//4,
            padding + highlight_size*2, 
            padding + highlight_size
        ], fill="#FFFFFF80")
        
        # 添加emoji或文本
        if emoji:
            try:
                font_size = max(12, min(width, height) // 2)
                draw.text((width//2, height//2), emoji, fill="#FFF", anchor="mm")
            except:
                pass
        
        return self._image_to_base64(img)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """十六进制颜色转RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _image_to_base64(self, img: Image.Image) -> str:
        """图像转base64"""
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{img_str}"
    
    def _get_fallback_images(self) -> List[str]:
        """获取后备图像"""
        return [
            'https://via.placeholder.com/32x32/4CAF50/FFFFFF?text=P',
            'https://via.placeholder.com/32x32/F44336/FFFFFF?text=E',
            'https://via.placeholder.com/16x16/FFC107/FFFFFF?text=*'
        ]
    
    def generate_audio_resources(self, game_type: str, game_elements: List[str]) -> List[str]:
        """生成音频资源"""
        try:
            # 生成基础的音效数据
            audio_resources = []
            
            # 根据游戏类型和元素生成不同的音效
            base_frequencies = {
                "jump": 440,     # 跳跃音效 - A4
                "collect": 523,  # 收集音效 - C5 
                "hit": 220,      # 碰撞音效 - A3
                "move": 330,     # 移动音效 - E4
                "success": 659,  # 成功音效 - E5
                "fail": 165      # 失败音效 - E3
            }
            
            # 生成基础音效
            if "道具系统" in game_elements:
                collect_audio = self._generate_tone(base_frequencies["collect"], 0.2)
                audio_resources.append(collect_audio)
            
            if "玩家角色" in game_elements:
                move_audio = self._generate_tone(base_frequencies["move"], 0.1)
                audio_resources.append(move_audio)
            
            # 根据游戏类型生成特定音效
            if "platform" in game_type.lower() or "平台" in game_type:
                jump_audio = self._generate_tone(base_frequencies["jump"], 0.15)
                audio_resources.append(jump_audio)
                
                hit_audio = self._generate_tone(base_frequencies["hit"], 0.3)
                audio_resources.append(hit_audio)
            
            # 生成成功和失败音效
            success_audio = self._generate_chord([659, 784, 988], 0.5)  # E5, G5, B5
            audio_resources.append(success_audio)
            
            fail_audio = self._generate_tone(base_frequencies["fail"], 0.8)
            audio_resources.append(fail_audio)
            
            logger.info(f"✅ 生成了 {len(audio_resources)} 个音频资源")
            return audio_resources
            
        except Exception as e:
            logger.error(f"❌ 音频资源生成失败: {str(e)}")
            return self._get_fallback_audio()
    
    def _generate_tone(self, frequency: float, duration: float, sample_rate: int = 22050) -> str:
        """生成单音调"""
        t = np.linspace(0, duration, int(sample_rate * duration))
        wave = np.sin(2 * np.pi * frequency * t)
        
        # 添加包络（渐入渐出）
        envelope = np.ones_like(wave)
        fade_samples = int(0.01 * sample_rate)  # 10ms fade
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        wave *= envelope * 0.3  # 降低音量
        
        # 转换为16位整数
        wave_int = (wave * 32767).astype(np.int16)
        
        return self._audio_array_to_base64(wave_int, sample_rate)
    
    def _generate_chord(self, frequencies: List[float], duration: float, sample_rate: int = 22050) -> str:
        """生成和弦"""
        t = np.linspace(0, duration, int(sample_rate * duration))
        wave = np.zeros_like(t)
        
        for freq in frequencies:
            wave += np.sin(2 * np.pi * freq * t) / len(frequencies)
        
        # 添加包络
        envelope = np.ones_like(wave)
        fade_samples = int(0.02 * sample_rate)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        wave *= envelope * 0.3
        wave_int = (wave * 32767).astype(np.int16)
        
        return self._audio_array_to_base64(wave_int, sample_rate)
    
    def _audio_array_to_base64(self, audio_array: np.ndarray, sample_rate: int) -> str:
        """音频数组转base64"""
        # 创建WAV文件头
        import struct
        
        # WAV文件参数
        channels = 1
        sample_width = 2  # 16位
        n_frames = len(audio_array)
        
        # WAV文件头
        wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + n_frames * sample_width,
            b'WAVE', b'fmt ', 16,
            1, channels, sample_rate, sample_rate * channels * sample_width,
            channels * sample_width, sample_width * 8,
            b'data', n_frames * sample_width
        )
        
        # 组合头部和数据
        wav_data = wav_header + audio_array.tobytes()
        
        # 转为base64
        audio_b64 = base64.b64encode(wav_data).decode()
        return f"data:audio/wav;base64,{audio_b64}"
    
    def _get_fallback_audio(self) -> List[str]:
        """获取后备音频"""
        base_audio = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT'
        return [f"{base_audio}_{i}" for i in range(3)]


# 全局资源生成服务实例
resource_generation_service = ResourceGenerationService()