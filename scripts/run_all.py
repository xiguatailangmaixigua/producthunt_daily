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
    # parser = argparse.ArgumentParser(description='一键运行Product Hunt热门应用处理流程')
    # # parser.add_argument('--date', type=str, help='指定日期，格式为YYYY-MM-DD，默认为当前日期')
    # # parser.add_argument('--mode', type=int, choices=[1, 2, 3, 4], help='微信公众号发布方式：1=保存到草稿箱，2=直接发布，3=生成HTML和封面图片，4=跳过发布')
    # args = parser.parse_args()
    
    # # 获取日期
    # if args.date:
    #     date_str = args.date
    # else:
    #     # 获取当前日期
    #     date_str = datetime.now().strftime('%Y-%m-%d')
    
    # logging.info(f"开始执行一键运行程序...（日期：{date_str}）")
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 定义要执行的脚本及其描述
    scripts = [
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
        },
        # {
        #     "path": os.path.join(script_dir, "generate_cover_image.py"),
        #     "description": "生成微信公众号封面图片"
        # }
    ]
    
    # 依次执行每个脚本
    for script in scripts:
        success = run_script(script["path"], script["description"])
        if not success:
            logging.error(f"由于{script['description']}失败，停止执行后续步骤")
            return
    
    # 询问是否发布到微信公众号
    # if args.non_interactive and args.mode:
    #     choice = str(args.mode)
    # elif args.non_interactive:
    #     choice = "3"
    # else:
    #     print("\n请选择微信公众号发布方式：")
    #     print("1. 保存到微信公众号草稿箱（需要配置API凭证）")
    #     print("2. 直接发布到微信公众号（需要配置API凭证和IP白名单）")
    #     print("3. 生成HTML和封面图片，手动发布")
    #     print("4. 跳过微信公众号发布")
    #     choice = input("请输入选项（1-4）: ").strip()
    
    # if choice == "1":
    #     # 保存到微信公众号草稿箱
    #     draft_script = os.path.join(script_dir, "save_to_wechat_draft.py")
    #     run_script(draft_script, "保存到微信公众号草稿箱", date_str)
    # elif choice == "2":
    #     # 直接发布到微信公众号
    #     wechat_script = os.path.join(script_dir, "publish_to_wechat.py")
    #     run_script(wechat_script, "发布到微信公众号", date_str)
    # elif choice == "3":
    #     # 提示用户手动发布
    #     html_file_path = os.path.abspath(f"data/{date_str}_wechat.html")
    #     cover_image_path = os.path.abspath(f"assets/cover_{date_str}.jpg")
        
    #     logging.info(f"您可以手动将以下文件内容复制到微信公众号后台进行发布：")
    #     logging.info(f"HTML文件：{html_file_path}")
    #     logging.info(f"封面图片：{cover_image_path}")
        
    #     logging.info("手动发布步骤：")
    #     logging.info("1. 打开微信公众号后台（https://mp.weixin.qq.com/）")
    #     logging.info('2. 点击"图文消息" -> "写图文消息"')
    #     logging.info('3. 在编辑器中点击"HTML"按钮')
    #     logging.info("4. 打开生成的HTML文件，复制其中的全部内容")
    #     logging.info("5. 粘贴到微信公众号编辑器的HTML编辑框中")
    #     logging.info("6. 上传封面图片")
    #     logging.info('7. 编辑标题（建议使用"Product Hunt 每日精选 YYYY-MM-DD"格式）')
    #     logging.info('8. 点击"发布"按钮')
    # else:
    #     logging.info("跳过微信公众号发布步骤")
    
    logging.info("一键运行程序执行完成")

if __name__ == "__main__":
    main()
