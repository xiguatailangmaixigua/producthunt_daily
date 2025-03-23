import os
import json
from datetime import datetime

def json_to_md(json_file, md_file):
    """将JSON文件转换为Markdown文件"""
    # 读取JSON数据
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    # 生成Markdown内容
    md_lines = []
    
    # 添加标题
    date_str = os.path.basename(md_file).replace('producthunt-daily-', '').replace('.md', '')
    md_lines.append(f'# Product Hunt 每日产品 Top {len(products)} - {date_str}\n')
    
    # 添加产品信息
    for i, product in enumerate(products, 1):
        # 产品标题和链接
        md_lines.append(f"## {i}. [{product['name']}]({product['product_hunt_url']})")
        
        # 产品标签
        if product.get('label'):
            md_lines.append(f"\n*{product['label']}*")
        
        # 产品图片
        if product.get('image'):
            md_lines.append(f"\n[![]({product['image']})]({product['product_hunt_url']})")
        
        # 产品描述
        if product.get('description'):
            md_lines.append(f"\n> {product['description']}")
        
        # 主题标签
        if product.get('topics'):
            topics_str = ' '.join([f'`{topic}`' for topic in product['topics']])
            md_lines.append(f"\n主题：{topics_str}")
        
        # 投票数
        if product.get('votes') is not None:
            md_lines.append(f"\n投票数：{product['votes']}")
        
        # 添加空行分隔
        md_lines.append('\n')
    
    # 写入Markdown文件
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

if __name__ == '__main__':
    # 获取当前日期
    date = datetime.now().strftime('%Y-%m-%d')
    
    # 构建文件路径
    json_file = f'data/product_{date}.json'
    md_file = f'data/producthunt-daily-{date}.md'
    
    # 转换文件
    json_to_md(json_file, md_file)
    print(f'成功将 {json_file} 转换为 {md_file}')
