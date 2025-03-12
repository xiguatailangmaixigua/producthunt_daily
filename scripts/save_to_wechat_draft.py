#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import logging
import requests
import argparse
import traceback
import markdown
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 微信公众号配置
WECHAT_APPID = os.getenv('WECHAT_APPID')
WECHAT_APPSECRET = os.getenv('WECHAT_APPSECRET')

class WechatDraftPublisher:
    """微信公众号草稿箱发布器"""
    
    def __init__(self):
        """初始化微信公众号发布器"""
        self.appid = WECHAT_APPID
        self.appsecret = WECHAT_APPSECRET
        self.access_token = None
        
        if not self.appid or not self.appsecret:
            logging.error("微信公众号配置错误，请检查环境变量WECHAT_APPID和WECHAT_APPSECRET")
            raise ValueError("微信公众号配置错误，请检查环境变量WECHAT_APPID和WECHAT_APPSECRET")
        
        logging.info(f"微信公众号配置加载成功，APPID: {self.appid[:4]}...")
    
    def get_access_token(self):
        """获取微信公众号访问令牌"""
        try:
            # 构建请求URL和参数
            url = "https://api.weixin.qq.com/cgi-bin/token"
            params = {
                'grant_type': 'client_credential',
                'appid': self.appid,
                'secret': self.appsecret
            }
            
            # 输出请求信息（隐藏敏感信息）
            logging.info(f"正在请求访问令牌，URL: {url}")
            safe_params = {
                'grant_type': params['grant_type'],
                'appid': params['appid'][:4] + '...',
                'secret': params['secret'][:4] + '...'
            }
            logging.info(f"请求参数: {', '.join([f'{k}={v}' for k, v in safe_params.items()])}")
            
            # 发送请求
            response = requests.get(url, params=params)
            
            # 处理响应
            logging.info(f"响应状态码: {response.status_code}")
            result = response.json()
            logging.info(f"响应内容: {result}")
            
            # 检查响应是否成功
            if response.status_code == 200 and "access_token" in result:
                self.access_token = result["access_token"]
                return self.access_token
            else:
                # 检查是否是IP白名单错误
                if "errcode" in result and result["errcode"] == 40164:
                    # 提取IP地址
                    errmsg = result.get("errmsg", "")
                    ip_match = re.search(r"invalid ip (\d+\.\d+\.\d+\.\d+)", errmsg)
                    ip_address = ip_match.group(1) if ip_match else "未知IP"
                    
                    # 记录错误并提供解决方案
                    logging.error(f"IP白名单错误: {result}")
                    logging.error(f"请在微信公众平台添加以下IP到白名单: {ip_address}")
                    logging.error("1. 登录微信公众平台 https://mp.weixin.qq.com/")
                    logging.error("2. 点击左侧菜单的'开发'→'基本配置'")
                    logging.error("3. 在'IP白名单'部分，点击'修改'按钮")
                    logging.error(f"4. 添加IP地址 {ip_address}")
                    logging.error("5. 点击'确定'保存更改")
                    logging.error("6. 等待几分钟，然后重新运行脚本")
                else:
                    # 其他错误
                    error_code = result.get("errcode", "未知错误码")
                    error_msg = result.get("errmsg", "未知错误")
                    logging.error(f"获取访问令牌失败，错误码: {error_code}, 错误信息: {error_msg}")
                
                raise Exception(f"获取微信公众号访问令牌时发生错误: {result.get('errmsg', '未知错误')}")
        
        except requests.exceptions.RequestException as e:
            logging.error(f"获取微信公众号访问令牌时发生网络错误: {str(e)}")
            raise
        
        except json.JSONDecodeError as e:
            logging.error(f"获取微信公众号访问令牌时发生JSON解析错误: {str(e)}")
            raise
        
        except Exception as e:
            logging.error(f"获取微信公众号访问令牌时发生错误: {str(e)}")
            raise
    
    def upload_image(self, image_path):
        """上传图片到微信公众号素材库"""
        try:
            # 获取访问令牌
            access_token = self.get_access_token()
            if not access_token:
                logging.error("无法获取访问令牌，无法上传图片")
                return None
            
            # 构建请求URL - 使用永久素材接口
            url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
            logging.info(f"正在上传图片，URL: {url}")
            
            # 检查文件是否存在
            if not os.path.exists(image_path):
                logging.error(f"图片文件不存在: {image_path}")
                return None
            
            # 准备文件数据
            with open(image_path, 'rb') as f:
                files = {
                    'media': (os.path.basename(image_path), f, 'image/jpeg')
                }
                
                # 发送请求
                response = requests.post(url, files=files)
            
            # 处理响应
            logging.info(f"响应状态码: {response.status_code}")
            response_data = response.json()
            logging.info(f"响应内容: {response_data}")
            
            # 检查响应是否成功
            if response.status_code == 200 and "media_id" in response_data:
                return response_data["media_id"]
            else:
                if "errcode" in response_data and response_data["errcode"] != 0:
                    error_code = response_data.get("errcode")
                    error_msg = response_data.get("errmsg", "未知错误")
                    logging.error(f"上传图片失败，错误码: {error_code}, 错误信息: {error_msg}")
                else:
                    logging.error(f"上传图片失败，响应: {response_data}")
                return None
        
        except Exception as e:
            logging.error(f"上传图片时发生错误: {str(e)}")
            return None
        finally:
            # 确保文件被关闭
            if 'f' in locals() and not f.closed:
                f.close()
    
    def convert_markdown_to_html(self, md_file_path, json_file_path=None):
        """将Markdown文件转换为HTML格式，优化为卡片式布局"""
        try:
            # 如果提供了JSON文件路径，则直接从JSON文件中读取数据
            if json_file_path and os.path.exists(json_file_path):
                logging.info(f"从JSON文件读取产品数据: {json_file_path}")
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    products = json.load(f)
                
                # 提取日期
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', json_file_path)
                date_str = date_match.group(0) if date_match else datetime.now().strftime('%Y-%m-%d')
                
                # 生成产品卡片
                formatted_products = []
                
                for i, product in enumerate(products, 1):
                    # 获取产品信息
                    product_name = product.get('name', f'产品 {i}')
                    product_url = product.get('product_hunt_url', '#')
                    icon_url = product.get('icon', '')
                    image_url = product.get('image', '')
                    label = product.get('label_zh', product.get('label', ''))
                    description = product.get('description_zh', product.get('description', ''))
                    content = product.get('content_zh', '')
                    topics = ', '.join(product.get('topics_zh', product.get('topics', [])))
                    votes = product.get('votes', 0)
                    
                    # 创建卡片式布局
                    card_html = f"""
                    <div class="product-card">
                        <div class="product-header">
                            <div class="product-icon">
                                <img src="{icon_url}" alt="图标" />
                            </div>
                            <h2 class="product-title">{product_name}</h2>
                        </div>
                        
                        <div class="product-image">
                            <img src="{image_url}" alt="{product_name}" />
                        </div>
                        
                        <div class="product-info">
                            <div class="product-label">{label}</div>
                            <div class="product-description">{description}</div>
                            <div class="product-content">{content[:200]}...</div>
                            <div class="product-meta">
                                <div class="product-votes"><span class="vote-count">▲ {votes}</span> 票</div>
                                <div class="product-topics">{topics}</div>
                            </div>
                            <div class="product-links">
                                <a href="{product_url}" class="product-link">在 Product Hunt 上查看</a>
                            </div>
                        </div>
                    </div>
                    """
                    formatted_products.append(card_html)
            else:
                # 如果没有提供JSON文件路径，则从Markdown文件中提取数据（保留原有逻辑）
                with open(md_file_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                # 转换Markdown为HTML
                html_content = markdown.markdown(
                    md_content,
                    extensions=['tables', 'fenced_code', 'codehilite', 'nl2br']
                )
                
                # 处理HTML内容，将每个产品转换为卡片式布局
                # 提取日期
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', md_file_path)
                date_str = date_match.group(0) if date_match else datetime.now().strftime('%Y-%m-%d')
                
                # 替换产品部分为卡片式布局
                # 1. 分割每个产品（通过<h2>标签）
                products_html = re.split(r'<h2>', html_content)
                
                # 第一部分是空的或者可能包含其他内容，从第二部分开始是产品
                formatted_products = []
                
                if len(products_html) > 1:
                    for i, product_html in enumerate(products_html[1:], 1):
                        # 提取产品名称和链接
                        name_link_match = re.search(r'<a href="([^"]+)">([^<]+)</a>', product_html)
                        if name_link_match:
                            product_url = name_link_match.group(1)
                            product_name = name_link_match.group(2)
                        else:
                            product_url = "#"
                            product_name = f"产品 {i}"
                        
                        # 提取图标
                        icon_match = re.search(r'<p><img alt="图标" src="([^"]+)"', product_html)
                        icon_url = icon_match.group(1) if icon_match else ""
                        
                        # 提取简介
                        intro_match = re.search(r'<strong>简介</strong>：([^<]+)', product_html)
                        intro = intro_match.group(1) if intro_match else ""
                        
                        # 提取详细介绍
                        detail_match = re.search(r'<strong>详细介绍</strong>：([^<]+)', product_html)
                        detail = detail_match.group(1) if detail_match else ""
                        
                        # 提取产品图片 - 修复图片提取方式
                        image_match = re.search(r'<p><img alt="产品图片" src="([^"]+)"', product_html)
                        image_url = image_match.group(1) if image_match else ""
                        
                        # 提取产品描述
                        description_match = re.search(r'<strong>产品描述</strong>：([^<]+)', product_html)
                        description = description_match.group(1) if description_match else ""
                        
                        # 提取关键词
                        topics_match = re.search(r'<strong>关键词</strong>：([^<]+)', product_html)
                        topics = topics_match.group(1) if topics_match else ""
                        
                        # 提取票数
                        votes_match = re.search(r'<strong>票数</strong>: (\d+)', product_html)
                        votes = votes_match.group(1) if votes_match else "0"
                        
                        # 创建卡片式布局
                        card_html = f"""
                        <div class="product-card">
                            <div class="product-header">
                                <div class="product-icon">
                                    <img src="{icon_url}" alt="图标" />
                                </div>
                                <h2 class="product-title">{product_name}</h2>
                            </div>
                            
                            <div class="product-image">
                                <img src="{image_url}" alt="{product_name}" />
                            </div>
                            
                            <div class="product-info">
                                <div class="product-label">{intro}</div>
                                <div class="product-description">{description}</div>
                                <div class="product-meta">
                                    <div class="product-votes"><span class="vote-count">▲ {votes}</span> 票</div>
                                    <div class="product-topics">{topics}</div>
                                </div>
                                <div class="product-links">
                                    <a href="{product_url}" class="product-link">在 Product Hunt 上查看</a>
                                </div>
                            </div>
                        </div>
                        """
                        formatted_products.append(card_html)
            
            # 组合所有产品卡片
            formatted_html = f"""
            <div class="header">
                <h1>PH今日热榜 | {date_str}</h1>
            </div>
            <div class="products-container">
                {"".join(formatted_products)}
            </div>
            """
            
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
                        background-color: #f8f8f8;
                        margin: 0;
                        padding: 0;
                    }}
                    
                    .header {{
                        text-align: center;
                        padding: 20px 15px;
                        background-color: #fff;
                        margin-bottom: 20px;
                        border-bottom: 1px solid #eaeaea;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                    }}
                    
                    .header h1 {{
                        margin: 0;
                        font-size: 22px;
                        font-weight: 600;
                        color: #333;
                    }}
                    
                    .products-container {{
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 0 15px;
                    }}
                    
                    .product-card {{
                        background-color: #fff;
                        border-radius: 12px;
                        overflow: hidden;
                        margin-bottom: 25px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                        transition: transform 0.2s ease, box-shadow 0.2s ease;
                    }}
                    
                    .product-header {{
                        padding: 16px;
                        border-bottom: 1px solid #f0f0f0;
                        display: flex;
                        align-items: center;
                    }}
                    
                    .product-icon {{
                        width: 36px;
                        height: 36px;
                        margin-right: 12px;
                        border-radius: 8px;
                        overflow: hidden;
                        flex-shrink: 0;
                    }}
                    
                    .product-icon img {{
                        width: 100%;
                        height: 100%;
                        object-fit: cover;
                    }}
                    
                    .product-title {{
                        margin: 0;
                        font-size: 18px;
                        font-weight: 600;
                        color: #333;
                        flex-grow: 1;
                    }}
                    
                    .product-image {{
                        width: 100%;
                        height: auto;
                        background-color: #f5f5f5;
                        text-align: center;
                        max-height: 400px;
                        overflow: hidden;
                    }}
                    
                    .product-image img {{
                        width: 100%;
                        height: auto;
                        display: block;
                        object-fit: cover;
                    }}
                    
                    .product-info {{
                        padding: 20px;
                    }}
                    
                    .product-label {{
                        margin-bottom: 12px;
                        font-size: 16px;
                        color: #444;
                        font-weight: 500;
                    }}
                    
                    .product-description {{
                        margin-bottom: 16px;
                        font-size: 15px;
                        color: #666;
                        line-height: 1.5;
                    }}
                    
                    .product-content {{
                        margin-bottom: 16px;
                        font-size: 14px;
                        color: #666;
                        line-height: 1.5;
                        border-left: 3px solid #f0f0f0;
                        padding-left: 12px;
                    }}
                    
                    .product-meta {{
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 16px;
                        padding: 10px 0;
                        border-top: 1px solid #f0f0f0;
                        border-bottom: 1px solid #f0f0f0;
                    }}
                    
                    .product-votes {{
                        font-size: 14px;
                        color: #666;
                    }}
                    
                    .vote-count {{
                        color: #ff6154;
                        font-weight: 600;
                    }}
                    
                    .product-topics {{
                        font-size: 13px;
                        color: #888;
                        max-width: 60%;
                    }}
                    
                    .product-links {{
                        margin-top: 16px;
                        display: flex;
                        justify-content: flex-end;
                    }}
                    
                    .product-link {{
                        display: inline-block;
                        padding: 8px 16px;
                        background-color: #ff6154;
                        color: white;
                        text-decoration: none;
                        border-radius: 6px;
                        font-size: 14px;
                        font-weight: 500;
                        transition: background-color 0.2s;
                    }}
                    
                    .product-link:hover {{
                        background-color: #e55a4f;
                    }}
                    
                    .footer {{
                        margin: 40px 15px 30px;
                        padding-top: 20px;
                        border-top: 1px solid #eee;
                        font-size: 13px;
                        color: #888;
                        text-align: center;
                    }}
                    
                    /* 响应式设计 */
                    @media (max-width: 600px) {{
                        .product-meta {{
                            flex-direction: column;
                            align-items: flex-start;
                            gap: 8px;
                        }}
                        
                        .product-topics {{
                            max-width: 100%;
                        }}
                        
                        .product-header {{
                            padding: 12px;
                        }}
                        
                        .product-info {{
                            padding: 15px;
                        }}
                    }}
                </style>
            </head>
            <body>
                {formatted_html}
                <div class="footer">
                    <p>本文由 Product Hunt Daily 自动生成，每日更新最新科技产品信息。</p>
                    <p>Powered by ReadPo</p>
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
    
    def save_to_wechat_draft(self, title, content, thumb_media_id=None):
        """保存文章到草稿箱"""
        try:
            # 获取访问令牌
            access_token = self.get_access_token()
            if not access_token:
                logging.error("无法获取访问令牌，无法保存到草稿箱")
                return False
            
            # 构建请求URL
            url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
            logging.info(f"正在请求保存到草稿箱，URL: {url}")
            
            # 构建文章数据
            articles = [{
                "title": title,
                "author": "Product Hunt Daily",
                "digest": "每日精选科技产品推荐",
                "content": content,
                "content_source_url": "https://www.producthunt.com/",
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 0,
                "only_fans_can_comment": 0
            }]
            
            data = {
                "articles": articles
            }
            
            # 发送请求
            logging.info(f"请求数据: 标题={title}, 内容长度={len(content)}字符")
            response = requests.post(url, json=data)
            
            # 处理响应
            logging.info(f"响应状态码: {response.status_code}")
            response_data = response.json()
            logging.info(f"响应内容: {response_data}")
            
            # 检查响应是否成功
            if response.status_code == 200 and "media_id" in response_data:
                return response_data["media_id"]
            else:
                if "errcode" in response_data and response_data["errcode"] != 0:
                    error_code = response_data.get("errcode")
                    error_msg = response_data.get("errmsg", "未知错误")
                    logging.error(f"保存到草稿箱失败，错误码: {error_code}, 错误信息: {error_msg}")
                else:
                    logging.error(f"保存到草稿箱失败，响应: {response_data}")
                return False
        
        except Exception as e:
            logging.error(f"保存文章到微信公众号草稿箱时发生错误: {str(e)}")
            return False

    def generate_html_from_json(self, json_file_path, date_str=None):
        """从JSON文件生成HTML内容"""
        try:
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 如果未提供日期，从文件名中提取
            if not date_str:
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', json_file_path)
                date_str = date_match.group(0) if date_match else datetime.now().strftime('%Y-%m-%d')
            
            # 生成HTML内容
            html_content = self._create_html_content(data, date_str)
            
            return html_content
        except Exception as e:
            logging.error(f"从JSON生成HTML时出错: {str(e)}")
            traceback.print_exc()
            return None
    
    def generate_markdown_for_doocs(self, json_file_path, date_str=None):
        """从JSON文件生成适合doocs/md编辑器的Markdown内容"""
        try:
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 如果未提供日期，从文件名中提取
            if not date_str:
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', json_file_path)
                date_str = date_match.group(0) if date_match else datetime.now().strftime('%Y-%m-%d')
            
            # 创建Markdown内容
            markdown_content = f"# Product Hunt 今日热榜 | {date_str}\n\n"
            
            # 添加简介
            markdown_content += "本文介绍 Product Hunt 上今日最受欢迎的产品，帮助您发现新的优质应用和工具。\n\n"
            
            # 处理每个产品
            for i, product in enumerate(data, 1):
                product_name = product.get('name', '')
                product_url = product.get('product_hunt_url', '')
                icon_url = product.get('icon', '')
                image_url = product.get('image', '')
                
                # 使用默认图片URL，当原始URL为空时
                if not icon_url:
                    icon_url = "https://ph-static.imgix.net/ph-logo-1.png"
                if not image_url:
                    image_url = "https://ph-static.imgix.net/ph-logo-1.png"
                
                label = product.get('label_zh', product.get('label', ''))
                description = product.get('description_zh', product.get('description', ''))
                content = product.get('content_zh', product.get('maker_introduction', ''))
                
                # 截断过长的内容
                if content and len(content) > 300:
                    content = content[:300] + "..."
                
                topics = product.get('topics_zh', product.get('topics', []))
                topics_str = '、'.join(topics) if isinstance(topics, list) else topics
                votes = product.get('votes', 0)
                
                # 产品卡片（Markdown格式）
                markdown_content += f"## {i}. {product_name}\n\n"
                
                if image_url:
                    markdown_content += f"![{product_name}]({image_url})\n\n"
                
                markdown_content += f"**{label}**\n\n"
                
                if description:
                    markdown_content += f"{description}\n\n"
                
                if content:
                    markdown_content += f"### 产品介绍\n{content}\n\n"
                
                markdown_content += f"**标签**: {topics_str}\n\n"
                markdown_content += f"**票数**: {votes}\n\n"
                markdown_content += f"**链接**: [{product_name}]({product_url})\n\n"
                
                # 分隔线
                if i < len(data):
                    markdown_content += "---\n\n"
            
            # 页脚
            markdown_content += "---\n\n"
            markdown_content += "本文由 [ReadPo](https://readpo.com) 自动生成，旨在为中文用户提供优质的国外产品推荐。\n"
            
            return markdown_content
        except Exception as e:
            logging.error(f"从JSON生成Markdown时出错: {str(e)}")
            traceback.print_exc()
            return None
    
    def _create_html_content(self, data, date_str):
        # 生成HTML内容
        html_content = f"""
        <div class="header">
            <h1>PH今日热榜 | {date_str}</h1>
        </div>
        <div class="products-container">
        """
        
        # 处理每个产品
        for i, product in enumerate(data, 1):
            product_name = product.get('name', '')
            product_url = product.get('product_hunt_url', '')
            icon_url = product.get('icon', '')
            image_url = product.get('image', '')
            
            # 使用默认图片URL，当原始URL为空时
            if not icon_url:
                icon_url = "https://ph-static.imgix.net/ph-logo-1.png"
            if not image_url:
                image_url = "https://ph-static.imgix.net/ph-logo-1.png"
            
            label = product.get('label_zh', product.get('label', ''))
            description = product.get('description_zh', product.get('description', ''))
            content = product.get('content_zh', product.get('maker_introduction', ''))
            
            # 截断过长的内容
            if content and len(content) > 300:
                content = content[:300] + "..."
            
            topics = product.get('topics_zh', product.get('topics', []))
            topics_str = '、'.join(topics) if isinstance(topics, list) else topics
            votes = product.get('votes', 0)
            
            # 产品卡片（HTML格式）
            html_content += f"""
            <div class="product-card">
                <div class="product-header">
                    <div class="product-icon">
                        <img src="{icon_url}" alt="图标" />
                    </div>
                    <h2 class="product-title">{product_name}</h2>
                </div>
                
                <div class="product-image">
                    <img src="{image_url}" alt="{product_name}" />
                </div>
                
                <div class="product-info">
                    <div class="product-label">{label}</div>
                    <div class="product-description">{description}</div>
                    <div class="product-content">{content}</div>
                    <div class="product-meta">
                        <div class="product-votes"><span class="vote-count">▲ {votes}</span> 票</div>
                        <div class="product-topics">{topics_str}</div>
                    </div>
                    <div class="product-links">
                        <a href="{product_url}" class="product-link">在 Product Hunt 上查看</a>
                    </div>
                </div>
            </div>
            """
        
        # 结束容器
        html_content += """
        </div>
        """
        
        return html_content
    
    def _generate_full_html(self, html_content):
        """生成完整的HTML文档，包括CSS样式"""
        css_styles = """
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f9f9f9;
                margin: 0;
                padding: 20px 0;
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .header h1 {
                margin: 0;
                font-size: 22px;
                font-weight: 600;
                color: #333;
            }
            
            .products-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 0 15px;
            }
            
            .product-card {
                background-color: #fff;
                border-radius: 12px;
                overflow: hidden;
                margin-bottom: 25px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            
            .product-header {
                padding: 16px;
                border-bottom: 1px solid #f0f0f0;
                display: flex;
                align-items: center;
            }
            
            .product-icon {
                width: 36px;
                height: 36px;
                margin-right: 12px;
                border-radius: 8px;
                overflow: hidden;
                flex-shrink: 0;
            }
            
            .product-icon img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            
            .product-title {
                margin: 0;
                font-size: 18px;
                font-weight: 600;
                color: #333;
                flex-grow: 1;
            }
            
            .product-image {
                width: 100%;
                height: auto;
                background-color: #f5f5f5;
                text-align: center;
                max-height: 400px;
                overflow: hidden;
            }
            
            .product-image img {
                width: 100%;
                height: auto;
                display: block;
                object-fit: cover;
            }
            
            .product-info {
                padding: 20px;
            }
            
            .product-label {
                margin-bottom: 12px;
                font-size: 16px;
                color: #444;
                font-weight: 500;
            }
            
            .product-description {
                margin-bottom: 16px;
                font-size: 15px;
                color: #666;
                line-height: 1.5;
            }
            
            .product-content {
                margin-bottom: 16px;
                font-size: 14px;
                color: #666;
                line-height: 1.5;
                border-left: 3px solid #f0f0f0;
                padding-left: 12px;
            }
            
            .product-meta {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
                padding: 10px 0;
                border-top: 1px solid #f0f0f0;
                border-bottom: 1px solid #f0f0f0;
            }
            
            .product-votes {
                font-size: 14px;
                color: #666;
            }
            
            .vote-count {
                color: #ff6154;
                font-weight: 600;
            }
            
            .product-topics {
                font-size: 14px;
                color: #666;
            }
            
            .product-links {
                text-align: right;
            }
            
            .product-link {
                display: inline-block;
                padding: 8px 16px;
                background-color: #ff6154;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                transition: background-color 0.2s ease;
            }
            
            .product-link:hover {
                background-color: #e55549;
            }
            
            .footer {
                text-align: center;
                margin-top: 40px;
                color: #999;
                font-size: 14px;
            }
            
            .footer a {
                color: #ff6154;
                text-decoration: none;
            }
            
            @media (max-width: 600px) {
                body {
                    padding: 10px 0;
                }
                
                .products-container {
                    padding: 0 10px;
                }
                
                .product-header {
                    padding: 12px;
                }
                
                .product-icon {
                    width: 30px;
                    height: 30px;
                }
                
                .product-title {
                    font-size: 16px;
                }
                
                .product-info {
                    padding: 15px;
                }
                
                .product-label {
                    font-size: 15px;
                }
                
                .product-description {
                    font-size: 14px;
                }
                
                .product-content {
                    font-size: 13px;
                }
            }
        </style>
        """
        
        full_html = f"""<!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Product Hunt 今日热榜</title>
            {css_styles}
        </head>
        <body>
            {html_content}
            <div class="footer">
                <p>Powered by <a href="https://readpo.com" target="_blank">ReadPo</a></p>
            </div>
        </body>
        </html>
        """
        
        return full_html

def main():
    """主函数"""
    try:
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='生成微信公众号草稿')
        parser.add_argument('--date', type=str, help='日期，格式为YYYY-MM-DD')
        parser.add_argument('--json', type=str, help='JSON文件路径')
        parser.add_argument('--output', type=str, help='输出HTML文件路径')
        parser.add_argument('--md', action='store_true', help='生成Markdown文件（适用于doocs/md编辑器）')
        parser.add_argument('--mode', type=str, choices=['draft', 'publish', 'html'], 
                          help='操作模式：draft=保存到草稿箱，publish=直接发布，html=生成HTML和封面图片')
        args = parser.parse_args()
        
        # 获取日期
        date_str = args.date
        if not date_str:
            # 默认使用当前日期
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 确定JSON文件路径
        json_file_path = args.json
        if not json_file_path:
            json_file_path = os.path.join('data', f'product_{date_str}_zh.json')
            if not os.path.exists(json_file_path):
                json_file_path = os.path.join('data', f'product_{date_str}.json')
        
        # 检查JSON文件是否存在
        if not os.path.exists(json_file_path):
            logging.error(f"JSON文件不存在: {json_file_path}")
            return
        
        # 创建微信公众号发布器
        publisher = WechatDraftPublisher()
        
        # 如果指定了生成Markdown文件
        if args.md:
            # 生成Markdown内容
            markdown_content = publisher.generate_markdown_for_doocs(json_file_path, date_str)
            
            # 确定输出路径
            output_dir = 'wechat_md'
            os.makedirs(output_dir, exist_ok=True)
            output_file = args.output or os.path.join(output_dir, f'ph_daily_{date_str}.md')
            
            # 保存Markdown文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logging.info(f"已生成Markdown文件并保存到: {output_file}")
            logging.info(f"完成! 请将生成的Markdown文件内容复制到 https://doocs.github.io/md 进行排版")
            return
        
        # 生成HTML内容
        html_content = publisher.generate_html_from_json(json_file_path, date_str)
        
        if not html_content:
            logging.error("生成HTML内容失败")
            return
        
        # 如果指定了输出文件路径，则保存到文件
        if args.output:
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(publisher._generate_full_html(html_content))
            
            logging.info(f"已生成HTML文件并保存到: {args.output}")
            return
        
        # 根据模式执行不同的操作
        if args.mode == 'draft':
            # 保存到微信公众号草稿箱
            success = publisher.save_to_wechat_draft(f"PH今日热榜 | {date_str}", html_content)
            if success:
                logging.info("已成功保存到微信公众号草稿箱")
            else:
                logging.error("保存到微信公众号草稿箱失败")
        elif args.mode == 'publish':
            # 直接发布到微信公众号
            logging.info("直接发布到微信公众号功能尚未实现")
        elif args.mode == 'html':
            # 生成HTML和封面图片，保存到data目录
            html_file_path = os.path.join('data', f'{date_str}_wechat.html')
            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(publisher._generate_full_html(html_content))
            logging.info(f"已生成HTML文件并保存到: {html_file_path}")
        else:
            # 创建drafts目录（如果不存在）
            drafts_dir = 'drafts'
            if not os.path.exists(drafts_dir):
                os.makedirs(drafts_dir)
            
            # 保存HTML文件
            html_file_path = os.path.join(drafts_dir, f'ph_daily_{date_str}.html')
            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(publisher._generate_full_html(html_content))
            
            logging.info(f"已生成HTML文件并保存到: {html_file_path}")
            
            # 询问是否保存到微信公众号草稿箱
            try:
                import sys
                # 检查是否在交互式环境中运行
                if sys.stdin.isatty():
                    choice = input("是否保存到微信公众号草稿箱？(y/n): ").strip().lower()
                    if choice == 'y':
                        # 保存到微信公众号草稿箱
                        success = publisher.save_to_wechat_draft(f"PH今日热榜 | {date_str}", html_content)
                        if success:
                            logging.info("已成功保存到微信公众号草稿箱")
                        else:
                            logging.error("保存到微信公众号草稿箱失败")
                    else:
                        logging.info("已跳过保存到微信公众号草稿箱")
                else:
                    logging.info("在非交互式环境中运行，自动跳过保存到微信公众号草稿箱")
            except KeyboardInterrupt:
                logging.info("用户取消操作")
            except Exception as e:
                logging.error(f"保存到微信公众号草稿箱时发生错误: {str(e)}")
                logging.info("已跳过保存到微信公众号草稿箱")
        
        # 提示用户使用doocs/md编辑器
        logging.info("提示：如果您在微信公众号中发现样式丢失的问题，可以尝试使用doocs/md编辑器")
        logging.info("使用以下命令生成适合doocs/md的Markdown文件：")
        logging.info(f"python scripts/generate_wechat_md.py --date {date_str}")
        logging.info("然后将生成的Markdown内容复制到 https://doocs.github.io/md 进行排版")
    
    except Exception as e:
        logging.error(f"发生错误: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
