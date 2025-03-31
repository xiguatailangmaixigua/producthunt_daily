#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
import pytz
import argparse
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def generate_repo_markdown(repo):
    """生成单个仓库的Markdown内容"""
    markdown = f"## [{repo['name']}]({repo['url']})\n\n"
    
    # 描述
    if repo.get('description_zh'):
        markdown += f"{repo['description_zh']}\n\n"
    elif repo.get('description'):
        markdown += f"{repo['description']}\n\n"

    # 项目地址
    markdown += f"🔗 项目地址：{repo['url']}\n\n"
        
    # README中的第一张图片
    if repo.get('readme_images') and len(repo['readme_images']) > 0:
        markdown += f"![]({repo['readme_images'][0]})\n\n"
    
    # 统计信息
    stats = []
    if repo.get('language'):
        stats.append(f"**语言**: {repo['language']}")
    if repo.get('stars'):
        stats.append(f"**星标**: {repo['stars']}")
    
    if stats:
        markdown += " | ".join(stats) + "\n\n"
    
    # 主题标签
    if repo.get('topics_zh') and len(repo['topics_zh']) > 0:
        markdown += "**主题**: " + ", ".join([f"`{topic}`" for topic in repo['topics_zh']]) + "\n\n"
    elif repo.get('topics') and len(repo['topics']) > 0:
        markdown += "**主题**: " + ", ".join([f"`{topic}`" for topic in repo['topics']]) + "\n\n"
    
    return markdown

def generate_markdown_content(repos, date_str, time_range="daily", language=""):
    """生成Markdown内容"""
    # 时间范围文本
    time_range_text = {
        "daily": "今日",
        "weekly": "本周",
        "monthly": "本月"
    }.get(time_range, "今日")
    
    language_text = f"({language})" if language else ""
    
    # 生成标题
    markdown_content = f"# GitHub {time_range_text}热门项目 {language_text} {date_str}\n\n"
    
    # 添加简介
    markdown_content += f"> 以下是 GitHub {time_range_text}热门项目列表，通过爬取 GitHub Trending 页面获取，帮助您了解当前最热门的开源项目。\n\n"
    
    markdown_content += "---\n\n"
    
    # 生成详细内容
    for repo in repos:
        markdown_content += generate_repo_markdown(repo)
        markdown_content += "---\n\n"
    
    return markdown_content

def main():
    try:
        logger.info("开始生成GitHub Trending中文Markdown文件...")
        
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='生成GitHub Trending中文Markdown文件')
        parser.add_argument('--date', type=str, help='指定日期，格式为YYYY-MM-DD')
        parser.add_argument('--time', type=str, choices=['daily', 'weekly', 'monthly'], 
                            default='daily', help='时间范围: daily, weekly, monthly')
        parser.add_argument('--lang', type=str, default='', help='编程语言，例如python, javascript等')
        parser.add_argument('--limit', type=int, default=0, help='限制处理的仓库数量')
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
        
        # 确保目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # 读取JSON文件
        language_suffix = f"_{args.lang}" if args.lang else ""
        json_file_path = os.path.join(data_dir, f"github-trending-{args.time}{language_suffix}-{date_str}.json")
        
        if not os.path.exists(json_file_path):
            logger.error(f"文件不存在: {json_file_path}")
            return
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            repos = json.load(f)
        
        logger.info(f"成功读取 {len(repos)} 个仓库信息")
        
        # 如果设置了限制，则只处理指定数量的仓库
        if args.limit and args.limit > 0:
            repos = repos[:args.limit]
            logger.info(f"限制处理仓库数量为: {args.limit}")
        
        # 生成Markdown内容
        markdown_content = generate_markdown_content(repos, date_str, args.time, args.lang)
        
        # 保存Markdown文件
        markdown_file_path = os.path.join(data_dir, f"github-trending-{args.time}{language_suffix}-{date_str}.md")
        with open(markdown_file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Markdown文件已保存到: {markdown_file_path}")
        logger.info("生成Markdown文件完成")
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")

if __name__ == "__main__":
    main()
