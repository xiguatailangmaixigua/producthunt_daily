import os
import json
from datetime import datetime

def generate_markdown(product_data, output_file):
    """
    根据产品数据生成Markdown文件
    """
    markdown_content = []
    
    # 添加标题
    date_str = os.path.basename(output_file).replace('producthunt-daily-', '').replace('.md', '')
    markdown_content.append(f'# Product Hunt 每日产品 Top 5 - {date_str}\n')
    
    # 添加产品列表
    for i, (product_id, product) in enumerate(product_data.items(), 1):
        # 产品标题
        markdown_content.append(f"## {i}. {product['name']}")
        
        # 产品链接和图片
        if product.get('image'):
            markdown_content.append(f"\n[![]({product['image']})]({product['url']})")
        
        # 产品描述
        if product.get('description'):
            markdown_content.append(f"\n> {product['description']}")
            
        # 中文描述
        if product.get('description_zh'):
            markdown_content.append(f"\n> {product['description_zh']}")
        
        # 主题标签
        if product.get('topics'):
            topics_str = ' '.join([f'`{topic}`' for topic in product['topics']])
            markdown_content.append(f"\n主题：{topics_str}")
            
        # 投票数
        if product.get('votes') is not None:
            markdown_content.append(f"\n投票数：{product['votes']}")
            
        markdown_content.append('\n')  # 添加空行分隔
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_content))
