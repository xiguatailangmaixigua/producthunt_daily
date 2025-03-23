#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import argparse
import asyncio
import subprocess
import pytz
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def run_script(script_name, args=None):
    """运行指定的脚本"""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    cmd = ['python', script_path]
    
    if args:
        cmd.extend(args)
    
    logger.info(f"运行脚本: {' '.join(cmd)}")
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if stdout:
        logger.info(f"脚本输出: {stdout.decode()}")
    
    if stderr:
        logger.error(f"脚本错误: {stderr.decode()}")
    
    if process.returncode != 0:
        logger.error(f"脚本 {script_name} 执行失败，返回码: {process.returncode}")
        return False
    
    logger.info(f"脚本 {script_name} 执行成功")
    return True

async def main():
    try:
        logger.info("开始执行GitHub Trending获取流程...")
        
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='获取GitHub Trending仓库并生成Markdown文件')
        parser.add_argument('--date', type=str, help='指定日期，格式为YYYY-MM-DD')
        parser.add_argument('--time', type=str, choices=['daily', 'weekly', 'monthly'], 
                            default='daily', help='时间范围: daily, weekly, monthly')
        parser.add_argument('--lang', type=str, default='', help='编程语言，例如python, javascript等')
        parser.add_argument('--limit', type=int, default=0, help='限制获取的仓库数量')
        args = parser.parse_args()
        
        # 设置日期
        if args.date:
            date_str = args.date
        else:
            beijing_tz = pytz.timezone('Asia/Shanghai')
            current_time = datetime.now(beijing_tz)
            date_str = current_time.strftime('%Y-%m-%d')
        logger.info(f"使用当前日期: {date_str}")
        
        # 设置时间范围
        time_range = args.time
        logger.info(f"使用时间范围: {time_range}")
        
        # 设置限制数量
        limit = args.limit
        if limit > 0:
            logger.info(f"限制获取仓库数量为: {limit}")
        
        # 构建脚本参数
        script_args = []
        script_args.extend(['--date', date_str])
        script_args.extend(['--time', time_range])
        if args.lang:
            script_args.extend(['--lang', args.lang])
        if limit > 0:
            script_args.extend(['--limit', str(limit)])
        
        # 步骤1: 获取GitHub Trending仓库
        logger.info("步骤1: 获取GitHub Trending仓库")
        success = await run_script('github_trending.py', script_args)
        if not success:
            logger.error("获取GitHub Trending仓库失败，流程终止")
            return
        
        # 步骤2: 翻译仓库信息
        logger.info("步骤2: 翻译仓库信息")
        success = await run_script('translate_github_trending.py', script_args)
        if not success:
            logger.error("翻译仓库信息失败，流程终止")
            return
        
        # 步骤3: 生成中文Markdown
        logger.info("步骤3: 生成中文Markdown")
        success = await run_script('generate_github_trending_md.py', script_args)
        if not success:
            logger.error("生成中文Markdown失败，流程终止")
            return
        
        logger.info("GitHub Trending获取流程执行完成")
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
