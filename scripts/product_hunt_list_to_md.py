import os
import sys
import json
import time
import random
import logging
import asyncio
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv
from pytz import timezone
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import feedparser
import argparse
import urllib.request
from tenacity import retry, wait_exponential, stop_after_attempt
import requests
import tempfile
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('product_hunt.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 加载 .env 文件
load_dotenv()

# 创建 Dashscope 客户端实例
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

try:
    from DrissionPage import ChromiumPage
except ImportError:
    logger.warning("DrissionPage库未安装，将无法使用DrissionPage方法。可以使用 'pip install DrissionPage' 安装。")

class ProductHuntScraper:
    def __init__(self):
        self.driver = None
        self.product_elements = []
        self.product_info = {}
        self.page = None  # 用于DrissionPage
        self.temp_dir = None
        
    def __enter__(self):
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 删除临时目录及其内容
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
    def init_selenium_driver(self):
        """初始化Selenium驱动"""
        logger.info("====== WebDriver manager ======")
        
        # 设置Chrome选项
        chrome_options = webdriver.ChromeOptions()
        
        # 添加更多仿真真实浏览器的选项
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-browser-side-navigation")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"--user-agent={random.choice(['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'])}")
        
        # 添加更多语言和地区设置
        chrome_options.add_argument("--lang=en-US,en;q=0.9")
        chrome_options.add_argument("--accept-lang=en-US,en;q=0.9")
        
        # 禁用webdriver标志
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # 禁用cookie域名检查，解决cookie域名问题
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        # 添加更多实验性选项
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 1,
            "profile.default_content_setting_values.cookies": 1
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 创建WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 设置页面加载超时时间
        driver.set_page_load_timeout(60)
        
        # 执行JavaScript来修改webdriver标志
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'zh-CN']
            });
            window.chrome = {
                runtime: {}
            };
            """
        })
        
        self.driver = driver
        return driver

    async def fetch_with_drission_page(self, date_str):
        """使用DrissionPage获取Product Hunt页面内容"""
        try:
            logger.info(f"获取 {date_str} 的Product Hunt热门产品")
            logger.info("尝试使用DrissionPage获取Product Hunt页面内容...")
            
            # 初始化DrissionPage
            page = get_drission_page()
            
            # 设置页面加载超时时间
            try:
                page.set.load_timeout(30)
            except Exception as e:
                logger.warning("无法设置DrissionPage的超时时间，使用默认值")
            
            # 访问昨天的排行榜页面
            yesterday = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y/%-m/%-d')
            url = f'https://www.producthunt.com/leaderboard/daily/{yesterday}/all'
            logger.info(f"访问昨天的Product Hunt排行榜页面: {url}")
            page.get(url)
            
            # 获取页面源代码
            page_source = page.html
            if not page_source:
                raise Exception("获取页面源代码失败")
                
            # 保存页面源代码到临时文件
            try:
                # 确保临时目录存在
                if not os.path.exists(self.temp_dir):
                    os.makedirs(self.temp_dir)
                    
                temp_html_path = os.path.join(self.temp_dir, f'producthunt_drission_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
                with open(temp_html_path, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                logger.info(f"已保存页面源代码到 {os.path.basename(temp_html_path)}")
            except Exception as e:
                logger.error(f"保存页面源代码失败: {str(e)}")
            
            # 使用BeautifulSoup解析页面
            logger.info("尝试使用BeautifulSoup解析页面...")
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 查找所有产品section
            product_sections = soup.find_all('section', attrs={'data-test': re.compile(r'^post-item-')})
            logger.info(f"使用BeautifulSoup找到 {len(product_sections)} 个产品section")
            
            if product_sections:
                self.product_elements = []
                self.product_info = {}
                
                for i, section in enumerate(product_sections[:15]):
                    try:
                        # 获取产品链接和名称
                        product_links = section.find_all('a', href=lambda href: href and '/posts/' in href)
                        if not product_links:
                            continue
                            
                        # 第一个链接是产品图片，第二个链接是产品名称，第三个链接是产品描述
                        product_url = product_links[1]['href']  # 使用产品名称链接
                        if not product_url.startswith('http'):
                            product_url = 'https://www.producthunt.com' + product_url
                            
                        product_id = product_url.split('/')[-1]
                        
                        # 记录产品信息
                        self.product_info[i] = {
                            'link': product_url,
                            'id': product_id,
                            'text': product_links[1].text.strip()
                        }
                        
                        logger.info(f"成功处理产品 {i+1}: {product_links[1].text.strip()}")
                        
                    except Exception as e:
                        logger.warning(f"处理产品section {i} 时出错: {str(e)}")
                        continue
                
                logger.info(f"成功缓存 {len(self.product_info)} 个产品元素的信息")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"使用DrissionPage获取Product Hunt页面内容时出错: {str(e)}")
            return False

    def init_drission_page(self):
        """初始化DrissionPage"""
        # 检查DrissionPage是否可用
        if 'DrissionPage' not in sys.modules:
            logger.error("DrissionPage库未安装，无法使用此方法")
            return None
        
        try:
            # 创建ChromiumPage对象
            page = ChromiumPage()
            
            # 设置页面加载超时时间 (根据最新API调整)
            try:
                page.timeout = 30  # 新版本
            except:
                try:
                    page.set.load_timeout(30)  # 旧版本
                except:
                    # 如果两种方式都不支持，则忽略超时设置
                    logger.warning("无法设置DrissionPage的超时时间，使用默认值")
            
            self.page = page
            return page
        except Exception as e:
            logger.error(f"初始化DrissionPage失败: {str(e)}")
            return None

class Product:
    def __init__(self, name, product_hunt_url, label="", maker_introduction="", topics=None, 
                 votes=0, is_featured=False, created_at="", icon="", image="", visit_url="", description=""):
        self.name = name
        self.product_hunt_url = product_hunt_url
        self.label = label
        self.maker_introduction = maker_introduction
        self.topics = topics or []
        self.votes = votes
        self.is_featured = is_featured
        self.created_at = created_at
        self.icon = icon
        self.image = image
        self.visit_url = visit_url
        self.description = description

    def format_description(self, description):
        """格式化产品描述"""
        if not description:
            return ""
        # 去除多余的换行和空格
        description = ' '.join(description.split())
        # 限制长度为500个字符
        if len(description) > 500:
            description = description[:497] + "..."
        return description

    # def to_markdown(self):
    #     """转换为Markdown格式"""
    #     markdown = f"## [{self.name}]({self.product_hunt_url})\n"
    #     if self.icon:
    #         markdown += f"![icon]({self.icon})\n"
    #     markdown += f"**简介**：{self.label}\n"
    #     markdown += f"**详细介绍**：{self.format_description(self.maker_introduction)}\n"
        
    #     # 添加产品图片
    #     if self.image:
    #         markdown += f"![产品图片]({self.image})\n"
            
    #     # 添加产品描述
    #     if self.description:
    #         markdown += f"**产品描述**：{self.format_description(self.description)}\n"
            
    #     # 添加产品链接
    #     if self.visit_url:
    #         markdown += f"**访问链接**: [{self.name}]({self.visit_url})\n"
            
    #     markdown += f"**Product Hunt**: [View on Product Hunt]({self.product_hunt_url})\n\n"
        
    #     # 改进关键词格式
    #     keywords = []
    #     unique_topics = list(dict.fromkeys(self.topics))
    #     for topic in unique_topics:
    #         # 将英文单词直接添加，不分割字符
    #         if topic and topic.strip():  # 确保关键词不为空
    #             keywords.append(topic.strip())
    #     if keywords:
    #         markdown += f"**关键词**：{'、'.join(keywords)}\n"
    #     else:
    #         markdown += "**关键词**：暂无\n"
        
    #     markdown += f"**票数**: {self.votes}\n"
    #     markdown += f"**是否精选**：{'是' if self.is_featured else '否'}\n"
    #     markdown += f"**发布时间**：{self.created_at}\n\n"
    #     markdown += "---\n"
    #     return markdown

    def to_dict(self):
        """将产品对象转换为可JSON序列化的字典"""
        return {
            'name': self.name,
            'product_hunt_url': self.product_hunt_url,
            'label': self.label,
            'maker_introduction': self.maker_introduction,
            'topics': list(dict.fromkeys(self.topics)),  
            'votes': self.votes,
            'is_featured': self.is_featured,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S %z'),
            'icon': self.icon,
            'image': self.image,
            'visit_url': self.visit_url,
            'description': self.description
        }

def get_drission_page():
    """获取DrissionPage实例"""
    page = ChromiumPage()
    page.set.window.size(1920, 1080)
    return page

async def generate_markdown(products, date_str):
    """生成Markdown文件"""
    # 确保目录存在
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # # 生成markdown内容
    # markdown_content = f"# Product Hunt 每日精选 {date_str}\n\n"
    
    # for product in products:
    #     markdown_content += product.to_markdown()
    
    # # 保存markdown文件
    # output_file = os.path.join(data_dir, f"{date_str}.md")
    # with open(output_file, 'w', encoding='utf-8') as f:
    #     f.write(markdown_content)
    # logger.info(f"Markdown文件已保存到: {output_file}")
    
    # 保存JSON文件
    json_file = os.path.join(data_dir, f"product_{date_str}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump([product.to_dict() for product in products], f, ensure_ascii=False, indent=2)
    logger.info(f"JSON文件已保存到: {json_file}")

async def main():
    """主函数"""
    # 获取当前日期
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    with ProductHuntScraper() as scraper:
        # 尝试获取产品列表
        try:
            success = await scraper.fetch_with_drission_page(current_date)
            if not success:
                logger.error("使用DrissionPage获取Product Hunt页面内容失败")
                sys.exit(1)
                
            # 获取产品详细信息
            products = []
            product_count = len(scraper.product_info)
            logger.info(f"找到 {product_count} 个产品")
            
            # 尝试使用DrissionPage构建产品数据
            logger.info("尝试使用DrissionPage方法构建产品数据...")
            product_data = {}
            
            for i, info in scraper.product_info.items():
                product_url = info.get('link')
                product_id = info.get('id')
                
                if not product_url or not product_id:
                    continue
                    
                # 获取产品详细信息
                try:
                    page = get_drission_page()
                    logger.info(f"使用DrissionPage访问产品页面: {product_url}")
                    page.get(product_url)
                    
                    # 保存页面源代码到临时文件
                    temp_html_path = os.path.join(scraper.temp_dir, f'producthunt_product_{product_id}.html')
                    with open(temp_html_path, 'w', encoding='utf-8') as f:
                        f.write(page.html)
                    logger.info(f"已保存产品页面源代码到 {os.path.basename(temp_html_path)}")
                    
                    # 解析产品信息
                    soup = BeautifulSoup(page.html, 'html.parser')
                    
                    # 初始化产品数据
                    product_data[product_id] = {
                        'name': '',
                        'description': '',
                        'product_hunt_url': product_url,
                        'created_at': '',
                        'id': product_id,
                        'label': '',
                        'topics': [],
                        'votes': 0,
                        'visit_url': '',
                        'image': ''
                    }
                    
                    # 获取产品名称和label
                    h1_element = soup.find('h1', class_='text-24')
                    if h1_element:
                        product_name = h1_element.text.strip()
                        if product_name:
                            product_data[product_id]['name'] = product_name
                            logger.info(f"使用DrissionPage获取到产品名称: {product_name}")
                            
                            # 获取label
                            label_div = h1_element.find_next_sibling('div', class_='text-18')
                            if label_div:
                                label = label_div.text.strip()
                                product_data[product_id]['label'] = label
                                logger.info(f"使用DrissionPage获取到产品label: {label}")
                    
                    # 获取产品描述
                    html_text_div = soup.find('div', class_=re.compile(r'styles_htmlText__.*'))
                    if html_text_div:
                        description = html_text_div.text.strip()
                        product_data[product_id]['description'] = description
                        logger.info(f"从styles_htmlText获取到description: {description}")
                    
                    # 获取visit_url
                    primary_link = soup.find('script', string=re.compile(r'"primaryLink".*?"url"'))
                    if primary_link:
                        url_match = re.search(r'"primaryLink".*?"url":"([^"]+)"', primary_link.string)
                        if url_match:
                            visit_url = url_match.group(1)
                            product_data[product_id]['visit_url'] = visit_url
                            logger.info(f"从primaryLink获取到visit_url: {visit_url}")
                    
                    # 获取主题标签
                    topic_elements = soup.find_all('a', href=re.compile(r'^/topics/'))
                    if topic_elements:
                        topics = list({topic.text.strip() for topic in topic_elements if topic.text.strip()})
                        product_data[product_id]['topics'] = topics
                        logger.info(f"使用DrissionPage获取到主题标签: {topics}")
                    
                    # 获取投票数
                    vote_elements = soup.find_all(attrs={"data-test": "vote-button"})
                    if vote_elements and len(vote_elements) > 0:
                        vote_text = vote_elements[0].text.strip()
                        votes_str = re.search(r'\d+', vote_text)
                        if votes_str:
                            product_data[product_id]['votes'] = int(votes_str.group())
                            logger.info(f"使用DrissionPage获取到投票数: {product_data[product_id]['votes']}")
                    
                    # 获取产品图片
                    meta_image = soup.find('meta', property='og:image')
                    if meta_image:
                        image_url = meta_image.get('content', '')
                        if image_url and 'ph-files.imgix.net' in image_url:
                            image = image_url.split('?')[0]
                            product_data[product_id]['image'] = image
                            logger.info(f"成功从meta标签获取产品图片: {image}")
                    
                except Exception as e:
                    logger.warning(f"获取产品 {product_id} 详细信息失败: {str(e)}")
                    continue
            
            # 将产品数据添加到列表
            for product_id, product in product_data.items():
                if product['name'] and product['label']:
                    products.append(product)
                    logger.info(f"使用备用方法添加产品: {product['name']}")
            
            # 保存产品信息到JSON文件
            output_file = f'data/product_{current_date}.json'
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功保存 {len(products)} 个产品信息到 {output_file}")
            
        except Exception as e:
            logger.error(f"获取产品信息失败: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())