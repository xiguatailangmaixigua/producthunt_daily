#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import markdown
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def convert_markdown_to_html(md_file_path):
    """将Markdown文件转换为HTML格式"""
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 转换Markdown为HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'codehilite', 'nl2br']
        )
        
        # 添加微信公众号样式
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Product Hunt 每日精选</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 100%;
                    margin: 0;
                    padding: 15px;
                }}
                h2 {{
                    margin-top: 30px;
                    margin-bottom: 10px;
                    font-size: 24px;
                    color: #333;
                }}
                h2 a {{
                    color: #1a73e8;
                    text-decoration: none;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 4px;
                    margin: 10px 0;
                }}
                p {{
                    margin: 10px 0;
                }}
                strong {{
                    font-weight: 600;
                }}
                hr {{
                    border: 0;
                    height: 1px;
                    background: #eee;
                    margin: 30px 0;
                }}
                a {{
                    color: #1a73e8;
                    text-decoration: none;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 15px;
                    border-top: 1px solid #eee;
                    font-size: 14px;
                    color: #888;
                }}
            </style>
        </head>
        <body>
            {html_content}
            <div class="footer">
                <p>本文由 Product Hunt Daily 自动生成，每日更新最新科技产品信息。</p>
            </div>
        </body>
        </html>
        """
        
        return styled_html
    
    except Exception as e:
        logging.error(f"转换Markdown为HTML时发生错误: {str(e)}")
        raise

def main():
    """主函数"""
    logging.info("开始执行生成微信公众号HTML程序...")
    
    try:
        # 获取当前日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 构建文件路径
        md_file_path = f"data/{today}_zh.md"
        
        # 检查文件是否存在
        if not os.path.exists(md_file_path):
            logging.error(f"Markdown文件不存在: {md_file_path}")
            return
        
        # 转换Markdown为HTML
        html_content = convert_markdown_to_html(md_file_path)
        
        # 保存HTML文件
        html_file_path = f"data/{today}_wechat.html"
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logging.info(f"成功生成微信公众号HTML文件: {html_file_path}")
        logging.info("生成微信公众号HTML程序执行完成")
    
    except Exception as e:
        logging.error(f"生成微信公众号HTML程序执行失败: {str(e)}")

if __name__ == "__main__":
    main()
