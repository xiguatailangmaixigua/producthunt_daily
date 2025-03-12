#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import logging
import time
import asyncio
import aiohttp
from datetime import datetime
import pytz
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取通义API密钥
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    logger.error("未找到DASHSCOPE_API_KEY环境变量，请在.env文件中设置")
    exit(1)

API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

async def translate_text(text, field_name=None, retry_count=0):
    """
    使用阿里通义大模型API翻译文本
    """
    if not text:
        return ""
    
    # 如果是topics列表，将其转换为字符串
    if isinstance(text, list):
        text = ", ".join(text)
    
    # 构建提示词
    prompt = f"请将以下英文文本翻译成中文，保持原文的格式和表情符号。翻译要自然、流畅，符合中文表达习惯：\n\n{text}"
    
    # 如果是特定字段，添加额外的提示
    if field_name:
        if field_name == "label":
            prompt = f"请将以下英文产品标签翻译成中文，保持简洁、有力：\n\n{text}"
        elif field_name == "description":
            prompt = f"请将以下英文产品描述翻译成中文，保持营销感和吸引力：\n\n{text}"
        elif field_name == "topics":
            prompt = f"请将以下英文主题标签翻译成中文，使用常见的中文技术/行业术语：\n\n{text}"
    
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "qwen-max",
        "input": {
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位精通简体中文的专业翻译，尤其擅长将英文产品信息翻译成浅显易懂的中文内容。\n\n规则：\n-翻译时要准确传达原文的事实和背景。\n-保留原始段落格式，以及保留专业术语和品牌名称。\n-保留原文的Emoji符号（如🧘/💡/🔍等）和排版结构（如👉/🔧）。\n-输出格式必须保留原始格式。\n\n翻译策略：\n1. 根据英文内容直译，保持原有格式，不要遗漏任何信息\n2. 根据直译的结果重新意译，遵守原意的前提下让内容更通俗易懂、符合中文表达习惯，但要保留原有格式不变"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        },
        "parameters": {}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if "output" in result and "text" in result["output"]:
                        return result["output"]["text"]
                    else:
                        logger.error(f"API返回格式错误: {result}")
                        return text
                elif response.status == 429:
                    # 速率限制，等待后重试
                    retry_delay = min(2 ** retry_count, 60)  # 指数退避策略
                    logger.warning(f"API速率限制，等待 {retry_delay} 秒后重试...")
                    await asyncio.sleep(retry_delay)
                    return await translate_text(text, field_name, retry_count + 1)
                else:
                    error_text = await response.text()
                    logger.error(f"API请求失败，状态码: {response.status}, 错误: {error_text}")
                    if retry_count < 3:  # 最多重试3次
                        retry_delay = min(2 ** retry_count, 60)
                        logger.info(f"等待 {retry_delay} 秒后重试...")
                        await asyncio.sleep(retry_delay)
                        return await translate_text(text, field_name, retry_count + 1)
                    return text
    except Exception as e:
        logger.error(f"翻译请求异常: {str(e)}")
        if retry_count < 3:
            retry_delay = min(2 ** retry_count, 60)
            logger.info(f"等待 {retry_delay} 秒后重试...")
            await asyncio.sleep(retry_delay)
            return await translate_text(text, field_name, retry_count + 1)
        return text

async def translate_product(product):
    try:
        # 初始化翻译结果
        translations = {}
        
        # 获取产品名称
        product_name = product.get("name", "")
        
        # 单独翻译label字段
        if "label" in product and product["label"]:
            logger.info(f"翻译label字段: {product['label'][:50]}...")
            label_zh = await translate_text(product["label"], "label")
            translations["label"] = label_zh
            logger.info(f"label字段翻译结果: {label_zh[:50]}...")
        
        # 单独翻译topics字段
        if "topics" in product and product["topics"]:
            topics_str = ", ".join(product["topics"])
            logger.info(f"翻译topics字段: {topics_str[:50]}...")
            topics_zh_str = await translate_text(topics_str, "topics")
            # 将翻译结果转换为列表
            topics_zh = [t.strip() for t in topics_zh_str.split(',')]
            translations["topics"] = topics_zh
            logger.info(f"topics字段翻译结果: {topics_zh}")
        
        # 处理integrated_content
        combined_content = ""
        if product.get('description'):
            combined_content += product['description'] + "\n\n"
        
        
        if combined_content:
            logger.info(f"翻译integrated_content字段...")
            logger.info(f"正在调用API翻译产品: {product_name}")
            
            # 构建特殊的提示词，要求概括内容、提取关键词，去除社交语言
            prompt = f"""你是世界上最专业的翻译工具，擅长英文和中文互译。你是一位精通英文和中文的专业翻译，尤其擅长将IT公司黑话和专业词汇翻译成简洁易懂的地道表达。你的任务是将以下关于产品"{product_name}"的内容翻译成地道的中文，风格与科普杂志或日常对话相似。

### 翻译要求：
1. 保持专业术语的准确性
2. 概括内容，提取核心价值和关键功能
3. 去除营销和社交语言，保持客观描述
4. 使用简洁、清晰的表达方式

### 规则：
- 产品名字"{product_name}"保留原样，不翻译
- 以下是常见的AI相关术语词汇对应表：
  * Transformer -> Transformer
  * LLM/Large Language Model -> 大语言模型
  * Generative AI -> 生成式 AI
  * API -> API
  * SaaS -> SaaS

### 策略：
分成两次翻译，并且打印每一次结果：
1. 根据英文内容直译，保持原有格式，不要遗漏任何信息
2. 根据第一次直译的结果重新意译，遵守原意的前提下让内容更通俗易懂、符合中文表达习惯，但要保留原有格式不变

### 格式约束：
只返回重新意译结果，不包含markdown格式，确保结果简洁、专业、易于理解

原文内容：
"""
            prompt += combined_content
            
            headers = {
                "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "qwen-max",
                "input": {
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是世界上最专业的翻译工具，擅长英文和中文互译。你是一位精通英文和中文的专业翻译，尤其擅长将IT公司黑话和专业词汇翻译成简洁易懂的地道表达。你的任务是将以下内容翻译成地道的中文，风格与科普杂志或日常对话相似"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                "parameters": {}
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(API_URL, headers=headers, json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            if "output" in result and "text" in result["output"]:
                                content_zh = result["output"]["text"]
                                translations["integrated_content"] = content_zh
                                logger.info(f"integrated_content字段翻译结果: {content_zh[:50]}...")
                            else:
                                logger.error(f"API返回格式错误: {result}")
                        else:
                            error_text = await response.text()
                            logger.error(f"API请求失败，状态码: {response.status}, 错误: {error_text}")
            except Exception as e:
                logger.error(f"翻译integrated_content时出错: {str(e)}")
        
        # 更新产品对象
        if "label" in translations:
            product["label_zh"] = translations["label"]
            logger.info(f"设置 label_zh 字段: {translations['label'][:50]}...")
        
        if "topics" in translations:
            product["topics_zh"] = translations["topics"]
            logger.info(f"设置 topics_zh 字段: {translations['topics']}")
        
        if "integrated_content" in translations:
            product["content_zh"] = translations["integrated_content"]
            logger.info(f"设置 content_zh 字段: {translations['integrated_content'][:50]}...")
        
        return product
    except Exception as e:
        logger.error(f"翻译产品 {product.get('name', 'unknown')} 时出错: {str(e)}")
        return product

async def main():
    try:
        logger.info("开始执行翻译程序...")
        
        # 解析命令行参数
        import argparse
        parser = argparse.ArgumentParser(description='翻译产品信息为中文')
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
        
        # 读取JSON文件
        json_file_path = f"data/product_{date_str}.json"
        if not os.path.exists(json_file_path):
            logger.error(f"文件不存在: {json_file_path}")
            return
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        logger.info(f"成功读取 {len(products)} 个产品信息")
        
        # 翻译产品信息
        translated_products = []
        for product in products:
            translated_product = await translate_product(product)
            translated_products.append(translated_product)
        
        # 保存翻译后的JSON文件
        output_file_path = f"data/product_{date_str}_zh.json"
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(translated_products, f, ensure_ascii=False, indent=2)
        
        logger.info(f"翻译完成，已保存到: {output_file_path}")
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}", exc_info=True)
    finally:
        logger.info("翻译程序执行完成")

if __name__ == "__main__":
    asyncio.run(main())
