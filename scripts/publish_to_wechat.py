#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
import requests
import markdown
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 加载环境变量
load_dotenv()

# 微信公众号API相关配置
WECHAT_APPID = os.getenv('WECHAT_APPID')
WECHAT_APPSECRET = os.getenv('WECHAT_APPSECRET')
WECHAT_TOKEN_URL = 'https://api.weixin.qq.com/cgi-bin/token'
WECHAT_DRAFT_URL = 'https://api.weixin.qq.com/cgi-bin/draft/add'
WECHAT_PUBLISH_URL = 'https://api.weixin.qq.com/cgi-bin/freepublish/submit'
WECHAT_MATERIAL_URL = 'https://api.weixin.qq.com/cgi-bin/material/add_material'

class WeChatPublisher:
    def __init__(self):
        self.access_token = None
        self.token_expires = 0
        self.check_credentials()
    
    def check_credentials(self):
        """检查微信公众号API凭证是否存在"""
        if not WECHAT_APPID or not WECHAT_APPSECRET:
            logging.error("微信公众号API凭证未设置，请在.env文件中设置WECHAT_APPID和WECHAT_APPSECRET")
            raise ValueError("微信公众号API凭证未设置")
    
    def get_access_token(self):
        """获取微信公众号API访问令牌"""
        # 如果令牌未过期，直接返回
        if self.access_token and time.time() < self.token_expires:
            return self.access_token
        
        # 获取新的访问令牌
        params = {
            'grant_type': 'client_credential',
            'appid': WECHAT_APPID,
            'secret': WECHAT_APPSECRET
        }
        
        try:
            response = requests.get(WECHAT_TOKEN_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'access_token' in data:
                self.access_token = data['access_token']
                self.token_expires = time.time() + data['expires_in'] - 300  # 提前5分钟过期
                logging.info("成功获取微信公众号访问令牌")
                return self.access_token
            else:
                logging.error(f"获取微信公众号访问令牌失败: {data}")
                raise Exception(f"获取微信公众号访问令牌失败: {data}")
        
        except Exception as e:
            logging.error(f"获取微信公众号访问令牌时发生错误: {str(e)}")
            raise
    
    def upload_image(self, image_path):
        """上传图片到微信公众号素材库"""
        access_token = self.get_access_token()
        url = f"{WECHAT_MATERIAL_URL}?access_token={access_token}&type=image"
        
        try:
            with open(image_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(url, files=files)
                response.raise_for_status()
                data = response.json()
                
                if 'media_id' in data:
                    logging.info(f"成功上传图片: {image_path}")
                    return data['media_id']
                else:
                    logging.error(f"上传图片失败: {data}")
                    raise Exception(f"上传图片失败: {data}")
        
        except Exception as e:
            logging.error(f"上传图片时发生错误: {str(e)}")
            raise
    
    def create_draft(self, title, content, thumb_media_id=None):
        """创建微信公众号草稿"""
        access_token = self.get_access_token()
        url = f"{WECHAT_DRAFT_URL}?access_token={access_token}"
        
        # 构建文章内容
        articles = [{
            "title": title,
            "content": content,
            "author": "Product Hunt Daily",
            "digest": f"Product Hunt每日精选 - {datetime.now().strftime('%Y-%m-%d')}",
            "thumb_media_id": thumb_media_id if thumb_media_id else "",
            "show_cover_pic": 1,
            "need_open_comment": 1,
            "only_fans_can_comment": 0
        }]
        
        data = {"articles": articles}
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            if 'media_id' in result:
                logging.info(f"成功创建微信公众号草稿，media_id: {result['media_id']}")
                return result['media_id']
            else:
                logging.error(f"创建微信公众号草稿失败: {result}")
                raise Exception(f"创建微信公众号草稿失败: {result}")
        
        except Exception as e:
            logging.error(f"创建微信公众号草稿时发生错误: {str(e)}")
            raise
    
    def publish_draft(self, media_id):
        """发布微信公众号草稿"""
        access_token = self.get_access_token()
        url = f"{WECHAT_PUBLISH_URL}?access_token={access_token}"
        
        data = {"media_id": media_id}
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            if 'publish_id' in result:
                logging.info(f"成功发布微信公众号文章，publish_id: {result['publish_id']}")
                return result['publish_id']
            else:
                logging.error(f"发布微信公众号文章失败: {result}")
                raise Exception(f"发布微信公众号文章失败: {result}")
        
        except Exception as e:
            logging.error(f"发布微信公众号文章时发生错误: {str(e)}")
            raise

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
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;">
            {html_content}
            <hr>
            <p style="color: #888; font-size: 14px;">本文由 Product Hunt Daily 自动生成，每日更新最新科技产品信息。</p>
        </div>
        """
        
        return styled_html
    
    except Exception as e:
        logging.error(f"转换Markdown为HTML时发生错误: {str(e)}")
        raise

def main():
    """主函数"""
    logging.info("开始执行微信公众号发布程序...")
    
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
        
        # 构建文章标题
        title = f"Product Hunt 每日精选 - {today}"
        
        # 初始化微信公众号发布器
        publisher = WeChatPublisher()
        
        # 上传封面图片（如果有）
        thumb_media_id = None
        cover_image_path = "assets/cover.jpg"
        if os.path.exists(cover_image_path):
            thumb_media_id = publisher.upload_image(cover_image_path)
        
        # 创建草稿
        media_id = publisher.create_draft(title, html_content, thumb_media_id)
        
        # 发布文章
        publish_id = publisher.publish_draft(media_id)
        
        logging.info(f"成功发布微信公众号文章: {title}")
        logging.info("微信公众号发布程序执行完成")
    
    except Exception as e:
        logging.error(f"微信公众号发布程序执行失败: {str(e)}")

if __name__ == "__main__":
    main()
