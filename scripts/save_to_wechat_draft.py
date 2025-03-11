#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import requests
import markdown
import json
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
WECHAT_MEDIA_UPLOAD_URL = 'https://api.weixin.qq.com/cgi-bin/material/add_material'

class WechatDraftPublisher:
    def __init__(self):
        self.appid = WECHAT_APPID
        self.appsecret = WECHAT_APPSECRET
        self.check_credentials()
        self.access_token = None
    
    def check_credentials(self):
        """检查微信公众号API凭证是否存在"""
        if not self.appid or not self.appsecret:
            logging.error("微信公众号API凭证未设置，请在.env文件中设置WECHAT_APPID和WECHAT_APPSECRET")
            raise ValueError("微信公众号API凭证未设置")
    
    def get_access_token(self):
        """获取微信公众号访问令牌"""
        try:
            params = {
                'grant_type': 'client_credential',
                'appid': self.appid,
                'secret': self.appsecret
            }
            
            # 输出请求信息，便于调试
            logging.info(f"正在请求访问令牌，URL: {WECHAT_TOKEN_URL}")
            logging.info(f"请求参数: grant_type=client_credential, appid={self.appid[:4]}..., secret={self.appsecret[:4]}...")
            
            response = requests.get(WECHAT_TOKEN_URL, params=params)
            
            # 输出响应状态码
            logging.info(f"响应状态码: {response.status_code}")
            
            # 尝试解析响应内容
            try:
                result = response.json()
                logging.info(f"响应内容: {result}")
            except:
                logging.error(f"无法解析响应内容为JSON: {response.text}")
                raise ValueError(f"无法解析响应内容为JSON: {response.text}")
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                logging.info("成功获取微信公众号访问令牌")
                return self.access_token
            elif 'errcode' in result and result['errcode'] == 40164:
                # IP白名单错误
                ip_error_msg = result.get('errmsg', '')
                current_ip = ip_error_msg.split('invalid ip ')[1].split(' ')[0] if 'invalid ip ' in ip_error_msg else "未知"
                
                error_msg = f"IP白名单错误: {result}"
                logging.error(error_msg)
                
                # 提供解决方案
                logging.error(f"请在微信公众平台添加以下IP到白名单: {current_ip}")
                logging.error("1. 登录微信公众平台 https://mp.weixin.qq.com/")
                logging.error("2. 点击左侧菜单的'开发'→'基本配置'")
                logging.error("3. 在'IP白名单'部分，点击'修改'按钮")
                logging.error(f"4. 添加IP地址 {current_ip}")
                logging.error("5. 点击'确定'保存更改")
                logging.error("6. 等待几分钟，然后重新运行脚本")
                
                raise ValueError(error_msg)
            else:
                error_msg = f"获取微信公众号访问令牌失败: {result}"
                logging.error(error_msg)
                raise ValueError(error_msg)
        
        except Exception as e:
            error_msg = f"获取微信公众号访问令牌时发生错误: {str(e)}"
            logging.error(error_msg)
            raise ValueError(error_msg)
    
    def upload_image(self, image_path):
        """上传图片到微信公众号素材库"""
        try:
            if not self.access_token:
                self.get_access_token()
            
            url = f"{WECHAT_MEDIA_UPLOAD_URL}?access_token={self.access_token}&type=image"
            logging.info(f"正在上传图片，URL: {url}")
            
            # 检查文件是否存在
            if not os.path.exists(image_path):
                logging.error(f"图片文件不存在: {image_path}")
                return None
            
            # 准备文件数据
            files = {
                'media': (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg')
            }
            
            # 发送请求
            response = requests.post(url, files=files)
            
            # 输出响应状态码
            logging.info(f"响应状态码: {response.status_code}")
            
            # 尝试解析响应内容
            try:
                result = response.json()
                logging.info(f"响应内容: {result}")
            except:
                logging.error(f"无法解析响应内容为JSON: {response.text}")
                return None
            
            if 'media_id' in result:
                media_id = result['media_id']
                logging.info(f"成功上传图片，media_id: {media_id}")
                return media_id
            else:
                error_msg = f"上传图片失败: {result}"
                logging.error(error_msg)
                return None
        
        except Exception as e:
            logging.error(f"上传图片时发生错误: {str(e)}")
            return None
        finally:
            # 关闭文件
            if 'files' in locals() and 'media' in files:
                files['media'][1].close()
    
    def convert_markdown_to_html(self, md_file_path):
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
    
    def read_image_as_base64(self, image_path):
        """读取图片并转换为Base64编码"""
        try:
            import base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
        
        except Exception as e:
            logging.error(f"读取图片时发生错误: {str(e)}")
            raise
    
    def save_to_draft(self, title, content, thumb_media_id=None):
        """保存文章到微信公众号草稿箱"""
        try:
            if not self.access_token:
                self.get_access_token()
            
            url = f"{WECHAT_DRAFT_URL}?access_token={self.access_token}"
            logging.info(f"正在请求保存到草稿箱，URL: {url}")
            
            # 准备文章数据
            article = {
                "title": title,
                "content": content,
                "digest": "",  # 摘要，可以留空
                "author": "PH日报",  # 作者名称不能超过8个字符
                "content_source_url": "",  # 原文链接，可以留空
                "need_open_comment": 0  # 是否打开评论，0不打开
            }
            
            # 如果有封面图片素材ID，添加到文章数据中
            if thumb_media_id:
                article["thumb_media_id"] = thumb_media_id
            
            data = {
                "articles": [article]
            }
            
            # 输出请求数据摘要
            logging.info(f"请求数据: 标题={title}, 内容长度={len(content)}字符")
            
            # 确保正确处理中文字符编码
            headers = {
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            # 使用json.dumps确保中文字符正确编码，禁用ASCII转义
            json_data = json.dumps(data, ensure_ascii=False)
            response = requests.post(url, data=json_data.encode('utf-8'), headers=headers)
            
            # 输出响应状态码
            logging.info(f"响应状态码: {response.status_code}")
            
            # 尝试解析响应内容
            try:
                result = response.json()
                logging.info(f"响应内容: {result}")
            except:
                logging.error(f"无法解析响应内容为JSON: {response.text}")
                return False
            
            if result.get('errcode') == 0 or 'media_id' in result:
                logging.info("成功保存文章到微信公众号草稿箱")
                if 'media_id' in result:
                    logging.info(f"草稿箱media_id: {result['media_id']}")
                return True
            else:
                error_msg = f"保存文章到微信公众号草稿箱失败: {result}"
                logging.error(error_msg)
                return False
        
        except Exception as e:
            logging.error(f"保存文章到微信公众号草稿箱时发生错误: {str(e)}")
            return False

def main():
    """主函数"""
    logging.info("开始执行保存到微信公众号草稿箱程序...")
    
    try:
        # 获取当前日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 构建文件路径
        md_file_path = f"data/{today}_zh.md"
        cover_image_path = "assets/cover.jpg"
        
        # 检查文件是否存在
        if not os.path.exists(md_file_path):
            logging.error(f"Markdown文件不存在: {md_file_path}")
            return
        
        if not os.path.exists(cover_image_path):
            logging.warning(f"封面图片不存在: {cover_image_path}")
        
        # 初始化微信公众号发布器
        publisher = WechatDraftPublisher()
        
        # 转换Markdown为HTML
        html_content = publisher.convert_markdown_to_html(md_file_path)
        
        # 保存HTML文件，方便调试
        html_file_path = f"data/{today}_wechat_draft.html"
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logging.info(f"已保存HTML文件: {html_file_path}")
        
        # 构建文章标题
        title = f"Product Hunt 每日精选 {today}"
        
        # 上传封面图片
        thumb_media_id = None
        if os.path.exists(cover_image_path):
            logging.info(f"正在上传封面图片: {cover_image_path}")
            thumb_media_id = publisher.upload_image(cover_image_path)
            if thumb_media_id:
                logging.info(f"成功上传封面图片，media_id: {thumb_media_id}")
            else:
                logging.warning("上传封面图片失败，将不使用封面图片")
        
        # 保存到草稿箱
        success = publisher.save_to_draft(title, html_content, thumb_media_id)
        
        if success:
            logging.info("成功保存文章到微信公众号草稿箱")
            logging.info(f"请登录微信公众平台，在草稿箱中查看并编辑文章")
            if not thumb_media_id:
                logging.info(f"记得手动上传封面图片: {os.path.abspath(cover_image_path)}")
        else:
            logging.error("保存文章到微信公众号草稿箱失败")
            logging.info("您可以手动将以下文件内容复制到微信公众号后台进行发布：")
            logging.info(f"HTML文件：{os.path.abspath(html_file_path)}")
            logging.info(f"封面图片：{os.path.abspath(cover_image_path)}")
        
        logging.info("保存到微信公众号草稿箱程序执行完成")
    
    except Exception as e:
        logging.error(f"保存到微信公众号草稿箱程序执行失败: {str(e)}")
        
        # 提供手动发布的说明
        today = datetime.now().strftime('%Y-%m-%d')
        html_file_path = f"data/{today}_wechat.html"
        cover_image_path = "assets/cover.jpg"
        
        if os.path.exists(html_file_path) and os.path.exists(cover_image_path):
            logging.info("您可以手动将以下文件内容复制到微信公众号后台进行发布：")
            logging.info(f"HTML文件：{os.path.abspath(html_file_path)}")
            logging.info(f"封面图片：{os.path.abspath(cover_image_path)}")

if __name__ == "__main__":
    main()
