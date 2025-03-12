#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import requests
import random
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
from datetime import datetime
import numpy as np
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
COVER_HEIGHT = 383  # 微信公众号推荐尺寸

# 颜色方案
COLOR_SCHEMES = [
    {
        'gradient_top': (255, 223, 128),    # 浅黄色顶部
        'gradient_bottom': (255, 153, 153), # 浅红色底部
        'title': (255, 255, 255),           # 白色标题
        'subtitle': (255, 255, 255, 200),   # 半透明白色副标题
        'shadow': (0, 0, 0, 100)            # 黑色阴影
    },
    {
        'gradient_top': (179, 229, 252),    # 浅蓝色顶部
        'gradient_bottom': (240, 203, 240), # 浅紫色底部
        'title': (255, 255, 255),           # 白色标题
        'subtitle': (255, 255, 255, 200),   # 半透明白色副标题
        'shadow': (0, 0, 0, 100)            # 黑色阴影
    },
    {
        'gradient_top': (200, 250, 200),    # 浅绿色顶部
        'gradient_bottom': (255, 216, 155), # 浅橙色底部
        'title': (255, 255, 255),           # 白色标题
        'subtitle': (255, 255, 255, 200),   # 半透明白色副标题
        'shadow': (0, 0, 0, 100)            # 黑色阴影
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
                title_font = ImageFont.truetype(font_file, 48)
                subtitle_font = ImageFont.truetype(font_file, 24)
                date_font = ImageFont.truetype(font_file, 18)
            else:
                # 使用默认字体
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                date_font = ImageFont.load_default()
        except Exception as e:
            logging.error(f"加载字体失败: {str(e)}")
            # 使用默认字体
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            date_font = ImageFont.load_default()
        
        # 绘制标题
        title_text = "Product Hunt Daily"
        title_width = draw.textlength(title_text, font=title_font)
        draw.text(((COVER_WIDTH - title_width) / 2, 50), title_text, font=title_font, fill=colors['title'])
        
        # 绘制产品名称
        draw.text(((COVER_WIDTH - draw.textlength(product_name, font=subtitle_font)) / 2, 120), 
                 product_name, font=subtitle_font, fill=colors['subtitle'])
        
        # 绘制产品标语
        if product_label:
            # 限制标语长度
            if len(product_label) > 100:
                product_label = product_label[:97] + "..."
            
            # 计算文本换行
            max_width = COVER_WIDTH - 40
            words = product_label.split()
            lines = []
            current_line = words[0]
            
            for word in words[1:]:
                if draw.textlength(current_line + " " + word, font=subtitle_font) <= max_width:
                    current_line += " " + word
                else:
                    lines.append(current_line)
                    current_line = word
            
            lines.append(current_line)
            
            # 绘制多行文本
            y_position = 170
            for line in lines:
                draw.text(((COVER_WIDTH - draw.textlength(line, font=subtitle_font)) / 2, y_position), 
                         line, font=subtitle_font, fill=colors['subtitle'])
                y_position += 30
        
        # 添加图标
        if icon:
            # 创建圆形遮罩
            mask = Image.new('L', icon.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, icon.size[0], icon.size[1]), fill=255)
            
            # 应用圆形遮罩
            icon_with_mask = Image.new('RGBA', icon.size)
            icon_with_mask.paste(icon, (0, 0), mask)
            
            # 添加阴影效果
            shadow = Image.new('RGBA', icon.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.ellipse((0, 0, icon.size[0], icon.size[1]), fill=colors['shadow'])
            shadow = shadow.filter(ImageFilter.GaussianBlur(5))
            
            # 将阴影和图标合并到封面上
            cover.paste(shadow, (int((COVER_WIDTH - icon.size[0]) / 2) + 5, 250 + 5), shadow)
            cover.paste(icon_with_mask, (int((COVER_WIDTH - icon.size[0]) / 2), 250), icon_with_mask)
        
        # 添加日期
        date_text = f"Date: {date_str}"
        draw.text(((COVER_WIDTH - draw.textlength(date_text, font=date_font)) / 2, COVER_HEIGHT - 50), 
                 date_text, font=date_font, fill=colors['subtitle'])
        
        return cover
    
    def create_stacked_icons_cover(self, icons, date_str):
        """创建多图标堆叠的封面图片"""
        # 随机选择一个颜色方案
        colors = random.choice(COLOR_SCHEMES)
        
        # 创建渐变背景
        cover = Image.new('RGB', (COVER_WIDTH, COVER_HEIGHT), (255, 255, 255))
        
        # 创建渐变背景
        gradient = np.zeros((COVER_HEIGHT, COVER_WIDTH, 3), dtype=np.uint8)
        for y in range(COVER_HEIGHT):
            r = int(colors['gradient_top'][0] * (1 - y/COVER_HEIGHT) + colors['gradient_bottom'][0] * (y/COVER_HEIGHT))
            g = int(colors['gradient_top'][1] * (1 - y/COVER_HEIGHT) + colors['gradient_bottom'][1] * (y/COVER_HEIGHT))
            b = int(colors['gradient_top'][2] * (1 - y/COVER_HEIGHT) + colors['gradient_bottom'][2] * (y/COVER_HEIGHT))
            gradient[y, :] = [r, g, b]
        
        # 将numpy数组转换为PIL图像
        gradient_img = Image.fromarray(gradient)
        cover.paste(gradient_img, (0, 0))
        
        # 尝试加载字体，如果失败则使用默认字体
        try:
            # 尝试加载系统字体
            system_fonts = [
                "/System/Library/Fonts/PingFang.ttc",  # macOS
                "/System/Library/Fonts/STHeiti Medium.ttc",  # macOS 黑体
                "/System/Library/Fonts/STHeiti Light.ttc",  # macOS 黑体
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",  # Linux
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Linux
                "C:\\Windows\\Fonts\\msyhbd.ttc",  # Windows 黑体
                "C:\\Windows\\Fonts\\msyh.ttc"  # Windows
            ]
            
            font_file = None
            for font_path in system_fonts:
                if os.path.exists(font_path):
                    font_file = font_path
                    break
            
            if font_file:
                title_font = ImageFont.truetype(font_file, 60)  # 增大字体尺寸
                subtitle_font = ImageFont.truetype(font_file, 32)
                date_font = ImageFont.truetype(font_file, 20)
            else:
                # 使用默认字体
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                date_font = ImageFont.load_default()
        except Exception as e:
            logging.error(f"加载字体失败: {str(e)}")
            # 使用默认字体
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            date_font = ImageFont.load_default()
        
        # 处理图标
        processed_icons = []
        for i, icon in enumerate(icons[:5]):  # 最多使用5个图标
            # 调整大小
            size = 120  # 减小图标尺寸以适应较小的封面高度
            icon = self.resize_icon(icon, (size, size))
            
            # 添加圆角或圆形效果
            mask = Image.new('L', icon.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((0, 0, icon.size[0], icon.size[1]), radius=30, fill=255)
            
            # 应用遮罩
            icon_with_mask = Image.new('RGBA', icon.size)
            icon_with_mask.paste(icon, (0, 0), mask)
            
            # 添加阴影效果
            shadow = Image.new('RGBA', icon.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rounded_rectangle((0, 0, icon.size[0], icon.size[1]), radius=30, fill=(0, 0, 0, 100))
            shadow = shadow.filter(ImageFilter.GaussianBlur(5))
            
            processed_icons.append((icon_with_mask, shadow))
        
        # 堆叠图标
        center_x = COVER_WIDTH // 2 - 100  # 将图标组向左移动，为文字留出空间
        center_y = COVER_HEIGHT // 2
        
        # 创建一个新的透明图层用于绘制图标
        icons_layer = Image.new('RGBA', (COVER_WIDTH, COVER_HEIGHT), (0, 0, 0, 0))
        
        # 计算图标位置和旋转角度
        for i, (icon, shadow) in enumerate(reversed(processed_icons)):
            # 计算位置偏移
            angle = -15 + i * 8  # 角度从-15度开始，每个图标增加8度
            offset_x = i * 20 - len(processed_icons) * 10  # 水平偏移
            offset_y = i * 15  # 垂直偏移
            
            # 旋转图标
            rotated_icon = icon.rotate(angle, expand=True, resample=Image.BICUBIC)
            rotated_shadow = shadow.rotate(angle, expand=True, resample=Image.BICUBIC)
            
            # 计算粘贴位置
            paste_x = center_x - rotated_icon.width // 2 + offset_x
            paste_y = center_y - rotated_icon.height // 2 + offset_y
            
            # 粘贴阴影和图标
            icons_layer.paste(rotated_shadow, (paste_x + 5, paste_y + 5), rotated_shadow)
            icons_layer.paste(rotated_icon, (paste_x, paste_y), rotated_icon)
        
        # 将图标层合并到封面
        cover.paste(icons_layer, (0, 0), icons_layer)
        
        # 创建一个带有阴影的文本层
        text_layer = Image.new('RGBA', (COVER_WIDTH, COVER_HEIGHT), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_layer)
        
        # 绘制标题
        title_text = "Product Hunt热门应用"
        title_width = text_draw.textlength(title_text, font=title_font)
        
        # 文字位置调整为右侧且更加居中
        text_x = center_x + 160
        text_y = center_y - 50  # 上移一点
        
        # 绘制标题阴影 - 加深阴影
        shadow_offset = 3
        text_draw.text((text_x + shadow_offset, text_y + shadow_offset), 
                      title_text, font=title_font, fill=(0, 0, 0, 150))
        
        # 绘制标题 - 使用纯黑色
        text_draw.text((text_x, text_y), 
                      title_text, font=title_font, fill=(0, 0, 0))
        
        # 绘制日期
        date_text = date_str
        
        # 绘制日期阴影
        text_draw.text((text_x + shadow_offset, text_y + 60 + shadow_offset), 
                      date_text, font=date_font, fill=(0, 0, 0, 100))
        
        # 绘制日期
        text_draw.text((text_x, text_y + 60), 
                      date_text, font=date_font, fill=(0, 0, 0))
        
        # 将文本层合并到封面
        cover.paste(text_layer, (0, 0), text_layer)
        
        return cover
    
    def save_image(self, image, output_path):
        """保存图片到指定路径"""
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 保存图片
        image.save(output_path, quality=95)
        logging.info(f"图片已保存到: {output_path}")

def main():
    """主函数"""
    logging.info("开始执行封面图片生成程序...")
    
    try:
        # 解析命令行参数
        import argparse
        parser = argparse.ArgumentParser(description='生成封面图片')
        parser.add_argument('--date', type=str, help='指定日期，格式为YYYY-MM-DD')
        parser.add_argument('--style', type=str, default='stacked', help='封面样式: stacked或single')
        args = parser.parse_args()
        
        # 获取日期
        if args.date:
            date_str = args.date
        else:
            # 获取当前日期
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        logging.info(f"使用日期: {date_str}")
        
        # 构建JSON文件路径
        json_file_path = f"data/product_{date_str}.json"
        
        # 检查文件是否存在
        if not os.path.exists(json_file_path):
            logging.error(f"JSON文件不存在: {json_file_path}")
            return
        
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        # 初始化封面图片生成器
        generator = CoverImageGenerator()
        
        if args.style == 'single':
            # 获取票数最高的产品
            top_product = max(products, key=lambda x: x.get('votes', 0))
            
            # 下载产品图标
            icon_url = top_product.get('icon', '')
            if icon_url:
                icon = generator.download_product_icon(icon_url)
                icon = generator.resize_icon(icon)
            else:
                icon = generator.create_default_icon()
            
            # 获取产品信息
            product_name = top_product.get('name', 'Product Hunt')
            product_label = top_product.get('label', '')
            
            # 生成封面图片
            cover_image = generator.create_cover_image(product_name, product_label, date_str, icon)
        else:
            # 下载多个产品图标
            icons = []
            for product in sorted(products, key=lambda x: x.get('votes', 0), reverse=True)[:5]:
                # 优先使用产品图片而不是图标
                image_url = product.get('image', '')
                if image_url:
                    logging.info(f"下载产品图片: {image_url}")
                    icon = generator.download_product_icon(image_url)
                    icons.append(icon)
                else:
                    # 如果没有图片，尝试使用图标
                    icon_url = product.get('icon', '')
                    if icon_url:
                        logging.info(f"下载图标: {icon_url}")
                        icon = generator.download_product_icon(icon_url)
                        icons.append(icon)
                    else:
                        logging.warning(f"产品 {product.get('name', 'Unknown')} 没有图片或图标URL")
                        icons.append(generator.create_default_icon())
            
            # 如果没有足够的图标，添加默认图标
            while len(icons) < 3:
                icons.append(generator.create_default_icon())
            
            # 生成堆叠图标的封面图片
            cover_image = generator.create_stacked_icons_cover(icons, date_str)
        
        # 保存封面图片
        output_path = f"assets/cover_{date_str}.jpg"
        generator.save_image(cover_image, output_path)
        
        # 同时保存一份为cover.jpg，用于微信公众号发布
        generator.save_image(cover_image, "assets/cover.jpg")
        
        logging.info("封面图片生成程序执行完成")
    
    except Exception as e:
        logging.error(f"封面图片生成程序执行失败: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
