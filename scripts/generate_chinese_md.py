#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import logging
import re
from datetime import datetime
import pytz
from dotenv import load_dotenv
import urllib.parse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

def clean_translation_content(content):
    """清理翻译内容，去掉"第一次直译"和"第二次意译"的标记，只保留第二次意译的内容"""
    if not content:
        return content
    
    # 查找第二次意译的内容
    second_translation_match = re.search(r'###\s*第二次意译\s*([\s\S]+?)(?=###|$)', content)
    if second_translation_match:
        # 返回第二次意译的内容，并去掉可能的前后空白
        return second_translation_match.group(1).strip()
    
    # 如果没有找到第二次意译，则去掉第一次直译的标记
    content = re.sub(r'###\s*第一次直译\s*', '', content)
    
    return content.strip()

def clean_url(url):
    """清理URL，去掉查询参数"""
    if not url:
        return url
    parsed_url = urllib.parse.urlparse(url)
    clean_url = urllib.parse.urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
    return clean_url

def generate_chinese_markdown(products, date_str):
    """生成中文版的Markdown文件"""
    logger.info("开始生成中文Markdown文件...")
    
    markdown_content = f"# ProductHunt热门应用 | {date_str}\n\n"
    
    for i, product in enumerate(products, 1):
        # 获取产品信息
        name = product.get('name', '')
        product_hunt_url = product.get('product_hunt_url', '')
        
        # 清理URL，去掉查询参数
        product_hunt_url = clean_url(product_hunt_url)
        visit_url = clean_url(product.get('visit_url', ''))
        
        # 使用label_zh作为标语
        label_zh = product.get('label_zh', product.get('label', ''))
        
        # 使用content_zh作为介绍，如果没有则回退到其他字段
        if 'content_zh' in product:
            detailed_content = product.get('content_zh', '')
            # 清理翻译内容
            detailed_content = clean_translation_content(detailed_content)
        else:
            # 向后兼容
            maker_introduction_zh = product.get('maker_introduction_zh', product.get('maker_introduction', ''))
            # 限制maker_introduction的长度
            if maker_introduction_zh and len(maker_introduction_zh) > 500:
                maker_introduction_zh = maker_introduction_zh[:500] + "..."
            detailed_content = maker_introduction_zh
        
        topics_zh = product.get('topics_zh', product.get('topics', []))
        votes = product.get('votes', 0)
        is_featured = product.get('is_featured', False)
        created_at = product.get('created_at', '')
        icon = product.get('icon', '')
        image = product.get('image', '')
        
        # 生成Markdown内容
        markdown_content += f"## [{i}. {name}]({product_hunt_url})\n"
        markdown_content += f"**简介**：{label_zh}\n"
        markdown_content += f"**功能**：{detailed_content}\n"
        markdown_content += f"**产品网站**: {visit_url}\n"
        markdown_content += f"**Product Hunt**: {product_hunt_url}\n\n"
        
        # 添加图片
        markdown_content += f"![]({image})\n"
        
        # 添加主题标签
        if topics_zh:
            if isinstance(topics_zh, list):
                markdown_content += f"**关键词**：{', '.join(topics_zh)}\n"
            else:
                markdown_content += f"**关键词**：{topics_zh}\n"
        
        # 添加投票数
        markdown_content += f"**票数**: 🔺{votes}\n"
        
        # 添加是否精选
        markdown_content += f"**是否精选**：{'是' if is_featured else '否'}\n"
        
        # 添加发布时间
        markdown_content += f"**发布时间**：{created_at}\n\n"
        
        # 添加分隔线
        markdown_content += "---\n\n"
    
    # 移除最后一个分隔线
    if markdown_content.endswith("---\n\n"):
        markdown_content = markdown_content[:-5]
    
    # 保存Markdown文件
    output_file_path = f"data/producthunt-daily-{date_str}.md"
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    logger.info(f"中文Markdown文件已保存到: {output_file_path}")
    
    return output_file_path

def main():
    try:
        logger.info("开始执行生成中文Markdown程序...")
        
        # 解析命令行参数
        import argparse
        parser = argparse.ArgumentParser(description='生成中文Markdown文件')
        parser.add_argument('--date', type=str, help='指定日期，格式为YYYY-MM-DD')
        args = parser.parse_args()
        
        if args.date:
            date_str = args.date
            logger.info(f"使用指定日期: {date_str}")
        else:
            # 获取当前日期
            beijing_tz = pytz.timezone('Asia/Shanghai')
            current_time = datetime.now(beijing_tz)
            date_str = current_time.strftime('%Y-%m-%d')
            logger.info(f"使用当前日期: {date_str}")
        
        # 读取翻译后的JSON文件
        json_file_path = f"data/product_{date_str}_zh.json"
        if not os.path.exists(json_file_path):
            logger.error(f"文件不存在: {json_file_path}")
            return
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        logger.info(f"成功读取 {len(products)} 个产品信息")
        
        # 生成中文Markdown文件
        output_file_path = generate_chinese_markdown(products, date_str)
        
        logger.info(f"中文Markdown文件已生成: {output_file_path}")
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}", exc_info=True)
    finally:
        logger.info("生成中文Markdown程序执行完成")

if __name__ == "__main__":
    main()
