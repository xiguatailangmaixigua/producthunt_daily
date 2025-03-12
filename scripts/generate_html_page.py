#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
import argparse
import markdown
import re
import urllib.parse
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class HTMLPageGenerator:
    """生成HTML页面并保存到pages目录"""
    
    def __init__(self):
        """初始化HTML页面生成器"""
        self.pages_dir = "pages"
        # 确保pages目录存在
        os.makedirs(self.pages_dir, exist_ok=True)
    
    def generate_html_from_json(self, json_file_path, output_file_path=None):
        """从JSON文件生成HTML页面
        
        Args:
            json_file_path: JSON文件路径
            output_file_path: 输出HTML文件路径，如果为None则自动生成
        
        Returns:
            生成的HTML内容和保存路径
        """
        try:
            # 从文件名中提取日期
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', json_file_path)
            date_str = date_match.group(1) if date_match else datetime.now().strftime('%Y-%m-%d')
            
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            # 格式化每个产品为HTML卡片
            formatted_products = []
            
            for product in products:
                # 提取产品信息
                product_name = product.get('name', '')
                product_url = product.get('product_hunt_url', '')
                
                # 设置默认图片URL
                default_icon = "https://ph-static.imgix.net/ph-logo-1.png"
                default_image = "https://ph-static.imgix.net/ph-logo-1.png"
                
                # 从产品名称生成占位图片
                icon_url = product.get('icon', '')
                image_url = product.get('image', '')
                
                # 如果图片URL为空，使用基于产品名称的占位图片
                if not icon_url:
                    # 使用产品名称生成一个随机颜色的占位图片
                    encoded_name = urllib.parse.quote(product_name)
                    icon_url = f"https://ui-avatars.com/api/?name={encoded_name}&background=random&color=fff&size=128"
                
                if not image_url:
                    # 使用产品名称生成一个随机颜色的占位图片，更大尺寸
                    encoded_name = urllib.parse.quote(product_name)
                    image_url = f"https://ui-avatars.com/api/?name={encoded_name}&background=random&color=fff&size=512"
                
                label = product.get('label_zh', product.get('label', ''))
                description = product.get('description_zh', product.get('description', ''))
                content = product.get('content_zh', product.get('maker_introduction', ''))
                
                # 截断过长的内容
                if content and len(content) > 300:
                    content = content[:300] + "..."
                
                topics = product.get('topics_zh', product.get('topics', []))
                topics_str = ', '.join(topics) if isinstance(topics, list) else topics
                votes = product.get('votes', 0)
                
                # 创建卡片式布局
                card_html = f"""
                <div class="product-card">
                    <div class="product-header">
                        <div class="product-icon">
                            <img src="{icon_url}" alt="图标" onerror="this.src='{default_icon}';" />
                        </div>
                        <h2 class="product-title">{product_name}</h2>
                    </div>
                    
                    <div class="product-image">
                        <img src="{image_url}" alt="{product_name}" onerror="this.src='{default_image}';" />
                    </div>
                    
                    <div class="product-info">
                        <div class="product-label">{label}</div>
                        <div class="product-description">{description}</div>
                        <div class="product-content">{content}</div>
                        <div class="product-meta">
                            <div class="product-votes"><span class="vote-count">▲ {votes}</span> 票</div>
                            <div class="product-topics">{topics_str}</div>
                        </div>
                        <div class="product-links">
                            <a href="{product_url}" class="product-link" target="_blank">在 Product Hunt 上查看</a>
                        </div>
                    </div>
                </div>
                """
                formatted_products.append(card_html)
            
            # 组合所有产品卡片
            formatted_html = f"""
            <div class="header">
                <h1>PH今日热榜 | {date_str}</h1>
            </div>
            <div class="products-container">
                {"".join(formatted_products)}
            </div>
            """
            
            # 添加完整HTML结构和样式
            styled_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Product Hunt 每日精选 | {date_str}</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                        line-height: 1.6;
                        color: #333;
                        background-color: #f8f8f8;
                        margin: 0;
                        padding: 0;
                    }}
                    
                    .header {{
                        text-align: center;
                        padding: 20px 15px;
                        background-color: #fff;
                        margin-bottom: 20px;
                        border-bottom: 1px solid #eaeaea;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                    }}
                    
                    .header h1 {{
                        margin: 0;
                        font-size: 22px;
                        font-weight: 600;
                        color: #333;
                    }}
                    
                    .products-container {{
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 0 15px;
                    }}
                    
                    .product-card {{
                        background-color: #fff;
                        border-radius: 12px;
                        overflow: hidden;
                        margin-bottom: 25px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                        transition: transform 0.2s ease, box-shadow 0.2s ease;
                    }}
                    
                    .product-card:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
                    }}
                    
                    .product-header {{
                        padding: 16px;
                        border-bottom: 1px solid #f0f0f0;
                        display: flex;
                        align-items: center;
                    }}
                    
                    .product-icon {{
                        width: 36px;
                        height: 36px;
                        margin-right: 12px;
                        border-radius: 8px;
                        overflow: hidden;
                        flex-shrink: 0;
                    }}
                    
                    .product-icon img {{
                        width: 100%;
                        height: 100%;
                        object-fit: cover;
                    }}
                    
                    .product-title {{
                        margin: 0;
                        font-size: 18px;
                        font-weight: 600;
                        color: #333;
                        flex-grow: 1;
                    }}
                    
                    .product-image {{
                        width: 100%;
                        height: auto;
                        background-color: #f5f5f5;
                        text-align: center;
                        max-height: 400px;
                        overflow: hidden;
                    }}
                    
                    .product-image img {{
                        width: 100%;
                        height: auto;
                        display: block;
                        object-fit: cover;
                    }}
                    
                    .product-info {{
                        padding: 20px;
                    }}
                    
                    .product-label {{
                        margin-bottom: 12px;
                        font-size: 16px;
                        color: #444;
                        font-weight: 500;
                    }}
                    
                    .product-description {{
                        margin-bottom: 16px;
                        font-size: 15px;
                        color: #666;
                        line-height: 1.5;
                    }}
                    
                    .product-content {{
                        margin-bottom: 16px;
                        font-size: 14px;
                        color: #666;
                        line-height: 1.5;
                        border-left: 3px solid #f0f0f0;
                        padding-left: 12px;
                        background-color: #f9f9f9;
                        padding: 10px 12px;
                    }}
                    
                    .product-meta {{
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 16px;
                        padding: 10px 0;
                        border-top: 1px solid #f0f0f0;
                        border-bottom: 1px solid #f0f0f0;
                    }}
                    
                    .product-votes {{
                        font-size: 14px;
                        color: #666;
                    }}
                    
                    .vote-count {{
                        color: #ff6154;
                        font-weight: 600;
                    }}
                    
                    .product-topics {{
                        font-size: 13px;
                        color: #888;
                        max-width: 60%;
                    }}
                    
                    .product-links {{
                        margin-top: 16px;
                        display: flex;
                        justify-content: flex-end;
                    }}
                    
                    .product-link {{
                        display: inline-block;
                        padding: 8px 16px;
                        background-color: #ff6154;
                        color: white;
                        text-decoration: none;
                        border-radius: 6px;
                        font-size: 14px;
                        font-weight: 500;
                        transition: background-color 0.2s;
                    }}
                    
                    .product-link:hover {{
                        background-color: #e55a4f;
                    }}
                    
                    .footer {{
                        margin: 40px 15px 30px;
                        padding-top: 20px;
                        border-top: 1px solid #eee;
                        font-size: 13px;
                        color: #888;
                        text-align: center;
                    }}
                    
                    /* 响应式设计 */
                    @media (max-width: 600px) {{
                        .product-meta {{
                            flex-direction: column;
                            align-items: flex-start;
                            gap: 8px;
                        }}
                        
                        .product-topics {{
                            max-width: 100%;
                        }}
                        
                        .product-header {{
                            padding: 12px;
                        }}
                        
                        .product-info {{
                            padding: 15px;
                        }}
                    }}
                </style>
            </head>
            <body>
                {formatted_html}
                <div class="footer">
                    <p>本文由 Product Hunt Daily 自动生成，每日更新最新科技产品信息。</p>
                    <p>Powered by ReadPo</p>
                </div>
            </body>
            </html>
            """
            
            # 确定输出文件路径
            if output_file_path is None:
                output_file_path = os.path.join(self.pages_dir, f"ph_daily_{date_str}.html")
            
            # 保存HTML文件
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(styled_html)
            
            logging.info(f"已生成HTML页面并保存到: {output_file_path}")
            return styled_html, output_file_path
            
        except Exception as e:
            logging.error(f"生成HTML页面时发生错误: {str(e)}")
            return None, None
    
    def generate_index_page(self):
        """生成索引页面，列出所有可用的日报页面
        
        Returns:
            生成的索引页面HTML内容
        """
        try:
            # 获取pages目录下的所有HTML文件
            html_files = [f for f in os.listdir(self.pages_dir) if f.endswith('.html') and f.startswith('ph_daily_')]
            
            # 按日期排序（最新的在前面）
            html_files.sort(reverse=True)
            
            # 生成文件列表
            file_list_html = ""
            for html_file in html_files:
                # 从文件名中提取日期
                date_match = re.search(r'ph_daily_(\d{4}-\d{2}-\d{2})\.html', html_file)
                if date_match:
                    date_str = date_match.group(1)
                    file_list_html += f'<li><a href="{html_file}">Product Hunt 每日精选 | {date_str}</a></li>\n'
            
            # 生成索引页面
            index_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Product Hunt 每日精选 - 索引</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                        line-height: 1.6;
                        color: #333;
                        background-color: #f8f8f8;
                        margin: 0;
                        padding: 0;
                    }}
                    
                    .container {{
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    
                    h1 {{
                        text-align: center;
                        margin-bottom: 30px;
                        color: #333;
                    }}
                    
                    ul {{
                        list-style-type: none;
                        padding: 0;
                    }}
                    
                    li {{
                        background-color: #fff;
                        margin-bottom: 10px;
                        padding: 15px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                        transition: transform 0.2s ease;
                    }}
                    
                    li:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    }}
                    
                    a {{
                        color: #ff6154;
                        text-decoration: none;
                        font-weight: 500;
                        display: block;
                    }}
                    
                    a:hover {{
                        text-decoration: underline;
                    }}
                    
                    .footer {{
                        margin-top: 40px;
                        text-align: center;
                        font-size: 13px;
                        color: #888;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Product Hunt 每日精选</h1>
                    <ul>
                        {file_list_html}
                    </ul>
                    <div class="footer">
                        <p>Product Hunt Daily - 每日更新最新科技产品信息</p>
                        <p>Powered by ReadPo</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 保存索引页面
            index_file_path = os.path.join(self.pages_dir, "index.html")
            with open(index_file_path, 'w', encoding='utf-8') as f:
                f.write(index_html)
            
            logging.info(f"已生成索引页面并保存到: {index_file_path}")
            return index_html
            
        except Exception as e:
            logging.error(f"生成索引页面时发生错误: {str(e)}")
            return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成HTML页面并保存到pages目录')
    parser.add_argument('--date', help='指定日期，格式为YYYY-MM-DD')
    parser.add_argument('--json', help='指定JSON文件路径')
    parser.add_argument('--output', help='指定输出HTML文件路径')
    parser.add_argument('--index', action='store_true', help='生成索引页面')
    args = parser.parse_args()
    
    generator = HTMLPageGenerator()
    
    if args.index:
        # 生成索引页面
        generator.generate_index_page()
    else:
        # 确定JSON文件路径
        json_file_path = args.json
        if json_file_path is None:
            if args.date:
                date_str = args.date
            else:
                # 默认使用昨天的日期
                yesterday = datetime.now() - timedelta(days=1)
                date_str = yesterday.strftime('%Y-%m-%d')
            
            json_file_path = f"data/product_{date_str}_zh.json"
        
        # 确定输出文件路径
        output_file_path = args.output
        
        # 生成HTML页面
        generator.generate_html_from_json(json_file_path, output_file_path)
        
        # 更新索引页面
        generator.generate_index_page()

if __name__ == "__main__":
    main()
