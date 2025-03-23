#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
import pytz
import asyncio
import argparse
from datetime import datetime
from dotenv import load_dotenv
import dashscope
from dashscope.aigc.generation import Generation

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 设置API密钥
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

async def translate_text(text, field_name=""):
    """使用阿里通义大模型API翻译文本"""
    if not text or len(text.strip()) == 0:
        return ""
    
    # 翻译提示
    prompt = f"""
    你是一位精通简体中文的专业翻译，尤其擅长将英文技术术语翻译成浅显易懂的中文内容。
    
    请将以下英文内容翻译成中文：
    {text}
    
    ##要求：
    -1. 直接翻译，不要添加任何解释或额外内容
    -2. 使用技术领域的专业术语
    -3. 翻译要流畅自然，符合中文表达习惯
    -4. 专有名词和品牌名称保留原文
    -5. 如果是多个词组用逗号分隔的列表，请保持相同格式翻译

    ##翻译策略：
    -1. 根据英文内容直译，保持原有格式，不要遗漏任何信息
    -2. 根据直译的结果重新意译，遵守原意的前提下让内容更通俗易懂、符合中文表达习惯，但要保留原有格式不变
    
    ##注意：
    -代码和专业术语、公司或产品名字，如"cursor" 无需翻译
    -只返回最终翻译结果，不要在翻译结果中包含这些提示和要求
    -不要在翻译结果中包含"##要求"、"##翻译策略"、"##注意"等提示文本
    -不要在翻译结果中包含"直译结果"、"意译结果"等标记
    -严格按照原文的顺序进行翻译，不要改变内容的顺序
    -不要添加任何额外的标题、小标题或分类标签
    """
    
    try:
        response = Generation.call(
            model="qwen-max",
            prompt=prompt,
            result_format='message',
            max_tokens=4000,
            temperature=0.3,
            top_p=0.8,
        )
        
        if response.status_code == 200:
            translated_text = response.output.choices[0].message.content.strip()
            logger.info(f"成功翻译{field_name}字段，长度: {len(translated_text)} 字符")
            return translated_text
        else:
            logger.error(f"翻译{field_name}字段失败: {response.code} - {response.message}")
            return ""
    except Exception as e:
        logger.error(f"翻译{field_name}字段时出错: {str(e)}")
        return ""

async def translate_readme(text):
    """翻译README内容"""
    if not text or len(text.strip()) == 0:
        return ""
    
    # 对于README内容，我们只翻译前500个字符，避免超出API限制
    max_length = 500
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    # 翻译提示
    prompt = f"""
    你是一位精通简体中文的专业翻译，尤其擅长将英文技术文档翻译成浅显易懂的中文内容。\n\n规则：\n-翻译时要准确传达原文的事实和背景。\n-保留原始段落格式，以及保留专业术语和品牌名称。\n-保留原文的Emoji符号（如🧘/💡/🔍等）和排版结构（如👉/🔧）。\n-输出格式必须保留原始格式。\n\n翻译策略：\n1. 根据英文内容直译，保持原有格式，不要遗漏任何信息\n2. 根据直译的结果重新意译，遵守原意的前提下让内容更通俗易懂、符合中文表达习惯，但要保留原有格式不变
    
    {text}
    
    要求：
    1. 保持原文的格式和标点符号
    2. 使用技术领域的专业术语
    3. 翻译要流畅自然，符合中文表达习惯
    4. 专有名词和品牌名称保留原文
    5. 代码和命令行不要翻译
    6. 只返回最终翻译结果，不要在翻译结果中包含这些提示和要求
    7. 不要在翻译结果中包含"要求"、"翻译策略"、"规则"等提示文本
    8. 严格按照原文的顺序进行翻译，不要改变内容的顺序
    9. 不要在翻译结果中包含"直译结果"、"意译结果"等标记
    10. 不要添加任何额外的标题、小标题或分类标签
    """
    
    try:
        response = Generation.call(
            model="qwen-max",
            prompt=prompt,
            result_format='message',
            max_tokens=4000,
            temperature=0.3,
            top_p=0.8,
        )
        
        if response.status_code == 200:
            translated_text = response.output.choices[0].message.content.strip()
            logger.info(f"成功翻译README内容，长度: {len(translated_text)} 字符")
            return translated_text
        else:
            logger.error(f"翻译README内容失败: {response.code} - {response.message}")
            return ""
    except Exception as e:
        logger.error(f"翻译README内容时出错: {str(e)}")
        return ""

async def translate_repo(repo):
    """翻译仓库信息"""
    logger.info(f"开始翻译仓库 {repo['name']} 的信息")
    
    # 翻译描述
    if 'description' in repo and repo['description']:
        repo['description_zh'] = await translate_text(repo['description'], "description")
    
    # 翻译主题标签
    if 'topics' in repo and repo['topics'] and len(repo['topics']) > 0:
        topics_text = ", ".join(repo['topics'])
        translated_topics = await translate_text(topics_text, "topics")
        
        # 分割翻译后的主题
        if translated_topics:
            repo['topics_zh'] = [topic.strip() for topic in translated_topics.split(',')]
        else:
            repo['topics_zh'] = []
    
    logger.info(f"完成仓库 {repo['name']} 的翻译")
    return repo

async def translate_repos(repos):
    """翻译所有仓库信息"""
    logger.info(f"开始翻译 {len(repos)} 个仓库的信息")
    
    translated_repos = []
    for repo in repos:
        translated_repo = await translate_repo(repo)
        translated_repos.append(translated_repo)
    
    logger.info(f"完成所有仓库的翻译")
    return translated_repos

async def main():
    try:
        logger.info("开始执行GitHub Trending翻译程序...")
        
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='翻译GitHub Trending仓库信息')
        parser.add_argument('--time', type=str, default='daily', choices=['daily', 'weekly', 'monthly'], help='时间范围: daily, weekly, monthly')
        parser.add_argument('--lang', type=str, default='', help='编程语言')
        parser.add_argument('--date', type=str, default='', help='日期，格式为YYYY-MM-DD，默认为当前日期')
        parser.add_argument('--limit', type=int, default=0, help='限制处理的仓库数量')
        args = parser.parse_args()
        
        # 设置日期
        if args.date:
            date_str = args.date
        else:
            date_str = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"使用当前日期: {date_str}")
        
        # 构建JSON文件路径
        language_suffix = f"_{args.lang}" if args.lang else ""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        json_file = os.path.join(data_dir, f"github-trending-{args.time}{language_suffix}-{date_str}.json")
        
        # 检查JSON文件是否存在
        if not os.path.exists(json_file):
            logger.error(f"JSON文件不存在: {json_file}")
            return
        
        # 读取JSON文件
        with open(json_file, 'r', encoding='utf-8') as f:
            repos = json.load(f)
        
        logger.info(f"从文件 {json_file} 中读取到 {len(repos)} 个仓库")
        
        # 如果设置了限制，则只处理指定数量的仓库
        if args.limit and args.limit > 0:
            repos = repos[:args.limit]
            logger.info(f"限制处理仓库数量为: {args.limit}")
        
        # 翻译仓库信息
        translated_repos = await translate_repos(repos)
        
        # 保存翻译后的JSON文件
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(translated_repos, f, ensure_ascii=False, indent=2)
        
        logger.info(f"翻译后的JSON文件已保存到: {json_file}")
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
