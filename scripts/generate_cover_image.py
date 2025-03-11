#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import requests
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 加载环境变量
load_dotenv()

# 封面图片尺寸（微信公众号推荐尺寸）
COVER_WIDTH = 900
COVER_HEIGHT = 383

# 颜色方案
COLOR_SCHEMES = [
    {
        'background': (240, 248, 255),  # 淡蓝色背景
        'title': (30, 144, 255),        # 道奇蓝标题
        'subtitle': (70, 130, 180),     # 钢青色副标题
        'accent': (0, 191, 255),        # 深天蓝强调色
        'text': (47, 79, 79)            # 深石板灰文本
    },
    {
        'background': (255, 250, 240),  # 花白色背景
        'title': (255, 99, 71),         # 番茄红标题
        'subtitle': (255, 127, 80),     # 珊瑚色副标题
        'accent': (255, 160, 122),      # 浅鲑鱼色强调色
        'text': (139, 69, 19)           # 马鞍棕色文本
    },
    {
        'background': (240, 255, 240),  # 蜜瓜色背景
        'title': (60, 179, 113),        # 中海绿标题
        'subtitle': (46, 139, 87),      # 海绿色副标题
        'accent': (32, 178, 170),       # 浅海绿强调色
        'text': (47, 79, 79)            # 深石板灰文本
    },
    {
        'background': (245, 245, 245),  # 白烟色背景
        'title': (25, 25, 112),         # 午夜蓝标题
        'subtitle': (70, 130, 180),     # 钢青色副标题
        'accent': (100, 149, 237),      # 矢车菊蓝强调色
        'text': (47, 79, 79)            # 深石板灰文本
    },
    {
        'background': (255, 250, 250),  # 雪色背景
        'title': (199, 21, 133),        # 适中的紫罗兰红标题
        'subtitle': (219, 112, 147),    # 苍白的紫罗兰红副标题
        'accent': (255, 20, 147),       # 深粉色强调色
        'text': (139, 0, 139)           # 深洋红色文本
    }
]

class CoverImageGenerator:
    def __init__(self):
        pass
    
    def download_product_icon(self, icon_url):
        """下载产品图标"""
        try:
            response = requests.get(icon_url)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            logging.error(f"下载产品图标失败: {str(e)}")
            # 返回一个默认图标
            return self.create_default_icon()
    
    def create_default_icon(self):
        """创建默认图标"""
        icon = Image.new('RGBA', (100, 100), (200, 200, 200, 255))
        draw = ImageDraw.Draw(icon)
        draw.rectangle([10, 10, 90, 90], outline=(100, 100, 100, 255), width=2)
        draw.text((50, 50), "PH", fill=(100, 100, 100, 255), anchor="mm")
        return icon
    
    def resize_icon(self, icon, size=(150, 150)):
        """调整图标大小"""
        if icon.mode != 'RGBA':
            icon = icon.convert('RGBA')
        return icon.resize(size, Image.LANCZOS)
    
    def create_cover_image(self, product_name, product_label, date_str, icon=None):
        """创建封面图片"""
        # 随机选择一个颜色方案
        colors = random.choice(COLOR_SCHEMES)
        
        # 创建背景图片
        cover = Image.new('RGB', (COVER_WIDTH, COVER_HEIGHT), colors['background'])
        draw = ImageDraw.Draw(cover)
        
        # 尝试加载字体，如果失败则使用默认字体
        try:
            # 尝试加载系统字体
            system_fonts = [
                "/System/Library/Fonts/PingFang.ttc",  # macOS
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Linux
                "C:\\Windows\\Fonts\\msyh.ttc"  # Windows
            ]
            
            font_file = None
            for font_path in system_fonts:
                if os.path.exists(font_path):
                    font_file = font_path
                    break
            
            if font_file:
                title_font = ImageFont.truetype(font_file, 40)
                subtitle_font = ImageFont.truetype(font_file, 30)
                small_font = ImageFont.truetype(font_file, 20)
            else:
                # 如果找不到系统字体，使用默认字体
                title_font = ImageFont.load_default()
                subtitle_font = title_font
                small_font = title_font
        except Exception as e:
            logging.warning(f"加载字体失败: {str(e)}，使用默认字体")
            title_font = ImageFont.load_default()
            subtitle_font = title_font
            small_font = title_font
        
        # 绘制装饰性元素
        # 左上角装饰
        draw.rectangle([0, 0, 20, COVER_HEIGHT], fill=colors['accent'])
        # 右下角装饰
        draw.rectangle([COVER_WIDTH-20, 0, COVER_WIDTH, COVER_HEIGHT], fill=colors['accent'])
        # 顶部装饰线
        draw.rectangle([0, 0, COVER_WIDTH, 5], fill=colors['accent'])
        # 底部装饰线
        draw.rectangle([0, COVER_HEIGHT-5, COVER_WIDTH, COVER_HEIGHT], fill=colors['accent'])
        
        # 绘制标题
        title = "Product Hunt 每日精选"
        title_width = draw.textlength(title, font=title_font)
        draw.text((COVER_WIDTH//2, 80), title, fill=colors['title'], font=title_font, anchor="mm")
        
        # 绘制日期
        draw.text((COVER_WIDTH//2, 130), date_str, fill=colors['subtitle'], font=subtitle_font, anchor="mm")
        
        # 绘制产品名称
        if len(product_name) > 25:
            product_name = product_name[:22] + "..."
        draw.text((COVER_WIDTH//2, 190), product_name, fill=colors['text'], font=subtitle_font, anchor="mm")
        
        # 绘制产品标签
        if product_label and len(product_label) > 40:
            product_label = product_label[:37] + "..."
        if product_label:
            draw.text((COVER_WIDTH//2, 230), f'"{product_label}"', fill=colors['subtitle'], font=small_font, anchor="mm")
        
        # 绘制底部信息
        draw.text((COVER_WIDTH//2, COVER_HEIGHT-30), "由AI自动生成", fill=colors['text'], font=small_font, anchor="mm")
        
        # 如果有图标，将图标合成到图片上
        if icon:
            # 计算图标位置（右上角）
            icon_position = (COVER_WIDTH - icon.width - 40, 40)
            
            # 创建一个圆形蒙版
            mask = Image.new('L', icon.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, icon.width, icon.height), fill=255)
            
            # 将图标粘贴到背景上
            cover.paste(icon, icon_position, mask)
        
        # 应用轻微模糊效果
        cover = cover.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # 增强对比度
        enhancer = ImageEnhance.Contrast(cover)
        cover = enhancer.enhance(1.1)
        
        return cover
    
    def save_image(self, image, output_path):
        """保存图片到指定路径"""
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 保存图片
            image.save(output_path, "JPEG", quality=95)
            logging.info(f"成功保存封面图片: {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"保存图片时发生错误: {str(e)}")
            raise

def main():
    """主函数"""
    logging.info("开始执行封面图片生成程序...")
    
    try:
        # 获取当前日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 构建JSON文件路径
        json_file_path = f"data/product_{today}.json"
        
        # 检查文件是否存在
        if not os.path.exists(json_file_path):
            logging.error(f"JSON文件不存在: {json_file_path}")
            return
        
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        # 初始化封面图片生成器
        generator = CoverImageGenerator()
        
        # 获取票数最高的产品
        top_product = max(products, key=lambda x: x.get('votes', 0))
        
        # 下载产品图标
        icon_url = top_product.get('icon_url', '')
        if icon_url:
            icon = generator.download_product_icon(icon_url)
            icon = generator.resize_icon(icon)
        else:
            icon = generator.create_default_icon()
        
        # 获取产品信息
        product_name = top_product.get('name', 'Product Hunt')
        product_label = top_product.get('label', '')
        
        # 生成封面图片
        cover_image = generator.create_cover_image(product_name, product_label, today, icon)
        
        # 保存封面图片
        output_path = f"assets/cover_{today}.jpg"
        generator.save_image(cover_image, output_path)
        
        # 同时保存一份为cover.jpg，用于微信公众号发布
        generator.save_image(cover_image, "assets/cover.jpg")
        
        logging.info("封面图片生成程序执行完成")
    
    except Exception as e:
        logging.error(f"封面图片生成程序执行失败: {str(e)}")

if __name__ == "__main__":
    main()
