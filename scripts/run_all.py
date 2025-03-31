#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import subprocess
import argparse
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def run_script(script_path, description, date_str=None):
    """运行指定的脚本"""
    logging.info(f"开始执行{description}...")
    
    try:
        cmd = [sys.executable, script_path]
        if date_str:
            cmd.extend(['--date', date_str])
            
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        # 输出脚本的标准输出和标准错误
        if result.stdout:
            logging.info(result.stdout)
        
        if result.stderr:
            logging.warning(result.stderr)
        
        logging.info(f"{description}执行完成")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"{description}执行失败: {str(e)}")
        if e.stdout:
            logging.info(e.stdout)
        if e.stderr:
            logging.error(e.stderr)
        return False
    except Exception as e:
        logging.error(f"{description}执行失败: {str(e)}")
        return False

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='一键运行热门内容抓取流程')
    parser.add_argument('--date', type=str, help='指定日期，格式为YYYY-MM-DD，默认为当前日期')
    parser.add_argument('--mode', type=int, choices=[1, 2, 3, 4], help='微信公众号发布方式：1=保存到草稿箱，2=直接发布，3=生成HTML和封面图片，4=跳过发布')
    parser.add_argument('--non-interactive', action='store_true', help='非交互模式，不等待用户输入')
    parser.add_argument('--source', type=str, choices=['producthunt', 'github', 'all'], default='all', help='抓取源：producthunt=ProductHunt，github=GitHub Trending，all=全部')
    args = parser.parse_args()
    
    # 获取日期
    if args.date:
        date_str = args.date
    else:
        # 获取当前日期
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    logging.info(f"开始执行一键运行程序...（日期：{date_str}）")
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 定义要执行的脚本及其描述
    producthunt_scripts = [
        {
            "path": os.path.join(script_dir, "product_hunt_list_to_md.py"),
            "description": "获取Product Hunt每日热门产品"
        },
        {
            "path": os.path.join(script_dir, "translate_to_chinese.py"),
            "description": "翻译产品信息为中文"
        },
        {
            "path": os.path.join(script_dir, "generate_chinese_md.py"),
            "description": "生成中文Markdown文件"
        }
        # {
        #     "path": os.path.join(script_dir, "generate_cover_image.py"),
        #     "description": "生成微信公众号封面图片"
        # }
    ]

    github_scripts = [
        {
            "path": os.path.join(script_dir, "run_github_trending.py"),
            "description": "获取GitHub Trending仓库",
            "args": ["--time", "daily"]
        }
    ]
    
    # 根据source参数决定执行哪些脚本
    if args.source in ['producthunt', 'all']:
        logging.info("开始执行Product Hunt抓取流程...")
        for script in producthunt_scripts:
            success = run_script(script["path"], script["description"], date_str)
            if not success:
                logging.error(f"由于{script['description']}失败，停止执行后续步骤")
                return
        logging.info("Product Hunt抓取流程执行完成")

    if args.source in ['github', 'all']:
        logging.info("开始执行GitHub Trending抓取流程...")
        for script in github_scripts:
            cmd = [sys.executable, script["path"]]
            if date_str:
                cmd.extend(['--date', date_str])
            if "args" in script:
                cmd.extend(script["args"])
                
            try:
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                if result.stdout:
                    logging.info(result.stdout)
                if result.stderr:
                    logging.warning(result.stderr)
                    
                logging.info(f"{script['description']}执行完成")
            except subprocess.CalledProcessError as e:
                logging.error(f"{script['description']}执行失败: {str(e)}")
                if e.stdout:
                    logging.info(e.stdout)
                if e.stderr:
                    logging.error(e.stderr)
                return
            except Exception as e:
                logging.error(f"{script['description']}执行失败: {str(e)}")
                return
        logging.info("GitHub Trending抓取流程执行完成")
    
    logging.info("一键运行程序执行完成")

if __name__ == "__main__":
    main()
