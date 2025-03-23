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

    async def fetch_with_drission_page(self):
        """使用DrissionPage获取Product Hunt页面内容"""
        logger.info("尝试使用DrissionPage获取Product Hunt页面内容...")
        
        # 检查DrissionPage是否可用
        if 'DrissionPage' not in sys.modules:
            logger.error("DrissionPage库未安装，无法使用此方法")
            return False
        
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
            
            # 设置页面大小
            page.set.window.size(1920, 1080)
            
            # 访问Product Hunt主页
            logger.info("访问Product Hunt主页...")
            page.get('https://www.producthunt.com')
            
            # 等待页面加载完成
            time.sleep(random.uniform(3, 5))
            
            # 模拟人类行为：随机滚动
            for _ in range(3):
                # 随机滚动距离
                scroll_distance = random.randint(300, 700)
                page.scroll.down(scroll_distance)
                # 随机等待
                time.sleep(random.uniform(1, 3))
            
            # 保存页面源代码以便分析
            page_source = page.html
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            html_file = f"producthunt_drission_{timestamp}.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(page_source)
            logger.info(f"已保存页面源代码到 {html_file}")
            
            # 使用BeautifulSoup解析页面
            logger.info("尝试使用BeautifulSoup解析页面...")
            soup = BeautifulSoup(page_source, 'html.parser')
            # 查找所有产品section
            product_sections = soup.find_all('section', attrs={'data-test': re.compile(r'^post-item-')})
            logger.info(f"使用BeautifulSoup找到 {len(product_sections)} 个产品section")
            
            if product_sections:
                self.product_elements = []
                self.product_info = {}
                
                for i, section in enumerate(product_sections[:15]):  # 只处理前15个
                    try:
                        # 获取产品链接和名称
                        product_links = section.find_all('a', href=lambda href: href and '/posts/' in href)
                        if not product_links:
                            continue
                            
                        # 第一个链接是产品图片，第二个链接是产品名称，第三个链接是产品描述
                        product_url = product_links[1]['href']  # 使用产品名称链接
                        if not product_url.startswith('http'):
                            product_url = 'https://www.producthunt.com' + product_url
                        
                        # 获取产品名称
                        product_name = product_links[1].text.strip()
                        
                        # 获取产品描述（第三个链接的文本）
                        product_description = product_links[2].text.strip() if len(product_links) > 2 else ""
                        
                        # 获取主题标签
                        topics = []
                        topic_links = section.find_all('a', href=re.compile(r'^/topics/'))
                        for topic_link in topic_links:
                            topic = topic_link.text.strip()
                            if topic:
                                topics.append(topic)
                        
                        # 获取投票数
                        vote_button = section.find('button', attrs={'data-test': 'vote-button'})
                        vote_count = 0
                        if vote_button:
                            vote_text = vote_button.find('div', class_='text-14').text.strip()
                            try:
                                vote_count = int(vote_text) if vote_text != '—' else 0
                            except ValueError:
                                pass
                        
                        # 缓存元素信息
                        self.product_info[i] = {
                            'link': product_url,
                            'text': product_name,
                            'description': product_description,
                            'topics': topics,
                            'votes': vote_count,
                            'location': {'x': 0, 'y': 0},
                            'size': {'width': 0, 'height': 0}
                        }
                        logger.info(f"成功处理产品 {i+1}: {product_name}")
                    except Exception as e:
                        logger.error(f"处理产品section {i} 时出错: {str(e)}")
                
                logger.info(f"成功缓存 {len(self.product_info)} 个产品元素的信息")
                
                # 关闭页面
                page.quit()
                
                return len(self.product_info) > 0
            
            logger.warning("未找到产品section")
            
            # 关闭页面
            page.quit()
            
            return False
            
        except Exception as e:
            logger.error(f"使用DrissionPage获取Product Hunt页面内容时出错: {str(e)}")
            
            # 确保页面关闭
            try:
                page.quit()
            except:
                pass
                
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
    parser = argparse.ArgumentParser(description='获取Product Hunt每日热门产品并生成Markdown文件')
    parser.add_argument('--date', type=str, help='指定日期，格式为YYYY-MM-DD，默认为今天')
    args = parser.parse_args()

    # 获取指定日期或今天的日期
    if args.date:
        try:
            date_obj = datetime.strptime(args.date, '%Y-%m-%d')
            date_str = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            logger.error("日期格式错误，请使用YYYY-MM-DD格式")
            return
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    logger.info(f"获取 {date_str} 的Product Hunt热门产品")

    # 初始化爬虫
    scraper = ProductHuntScraper()
    
 
    try:
        success = await scraper.fetch_with_drission_page()
    except Exception as e:
        logger.error(f"使用DrissionPage方法获取产品列表失败: {str(e)}")
    
    # 如果所有方法都失败，退出程序
    if not success:
        logger.error("所有获取产品列表的方法都失败，程序退出")
        return
    
    # 获取产品详细信息并生成Markdown文件
    products = []
    
    # 获取产品元素数量
    product_count = len(scraper.product_info)
    logger.info(f"找到 {product_count} 个产品")
    
    # 尝试使用DrissionPage直接从产品信息构建数据
    logger.info("尝试使用DrissionPage方法构建产品数据...")
    try:
        # 直接从RSS数据构建产品信息
        product_data = {}  # 用于合并同一产品的不同部分
        
        for i, info in scraper.product_info.items():
            if i >= 45:  # 只处理前45个（可能每个产品有多个条目）
                break
            
            text = info.get('text', '').strip()
            link = info.get('link', '')
            
            if not link:
                continue
            
            # 提取产品ID
            product_id = link.split('/posts/')[-1] if '/posts/' in link else ""
            
            if not product_id:
                continue
            
            # 初始化产品数据
            if product_id not in product_data:
                product_data[product_id] = {
                    'name': '',
                    'description': '',
                    'product_hunt_url': link,
                    'created_at': info.get('published', ''),
                    'id': product_id,
                    'label': '',
                    'topics': [],
                    'votes': 0,
                    'visit_url': '',
                    'image': ''
                }
            
            
            logger.info('开始处理产品链接: %s', link)  
           
            # 尝试从链接中提取产品网站
            try:
                # 访问产品页面
                logger.info(f"尝试获取产品 {product_id} 的详细信息...")
                
                # 尝试使用DrissionPage获取产品详细信息
                try:
                    if not hasattr(scraper, 'page') or not scraper.page:
                        scraper.init_drission_page()
                    
                    page = scraper.page
                    page.get(link)
                    logger.info(f"使用DrissionPage访问产品页面: {link}")
                    
                    # 等待页面加载
                    time.sleep(5)  # 增加等待时间
                    
                    # 保存页面源代码以便调试
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    debug_file = f"producthunt_product_{product_id}_{timestamp}.html"
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(page.html)
                    logger.info(f"已保存产品页面源代码到 {debug_file}")
                    
                    # 获取页面源代码
                    soup = BeautifulSoup(page.html, 'html.parser')
                    
                    # 获取产品名称和label
                    h1_element = soup.find('h1', class_='text-24')
                    if h1_element:
                        product_name = h1_element.text.strip()
                        if product_name:
                            product_data[product_id]['name'] = product_name
                            logger.info(f"使用DrissionPage获取到产品名称: {product_name}")
                            
                            # 查找h1的下一个兄弟元素作为label
                            label_div = h1_element.find_next_sibling('div', class_='text-18')
                            if label_div:
                                label = label_div.text.strip()
                                product_data[product_id]['label'] = label
                                logger.info(f"使用DrissionPage获取到产品label: {label}")
                                
                                # 如果成功获取到label，则将产品添加到列表中
                                # if product_id not in products:
                                #     products.append(product_id)
                            
                    # 获取产品描述
                    description = ""
                    
                    # 先尝试从header_section的下一个div获取
                    header_section = soup.find('section', class_='group/header-base')
                    if header_section:
                        next_div = header_section.find_next_sibling('div')
                        if next_div:
                            description = next_div.text.strip()
                            logger.info(f"从header_section获取到description: {description}")
                    
                    # 如果没有获取到description，尝试从styles_htmlText类获取
                    if not description:
                        html_text_div = soup.find('div', class_=re.compile(r'styles_htmlText__.*'))
                        if html_text_div:
                            description = html_text_div.text.strip()
                            logger.info(f"从styles_htmlText获取到description: {description}")
                    
                    if description:
                        product_data[product_id]['description'] = description
                    
                    # 寻找"Visit"按钮或链接
                    visit_links = soup.find_all('a', text=re.compile(r'Visit|Website', re.IGNORECASE))
                    if visit_links:
                        product_data[product_id]['visit_url'] = visit_links[0].get('href', '')
                        logger.info(f"使用DrissionPage从文本中获取到产品访问链接: {product_data[product_id]['visit_url']}")
                    else:
                        # 尝试查找包含"visit"或"website"的链接
                        visit_links = soup.find_all('a', href=re.compile(r'http'))
                        for link_elem in visit_links:
                            link_text = link_elem.text.strip().lower()
                            if 'visit' in link_text or 'website' in link_text:
                                product_data[product_id]['visit_url'] = link_elem.get('href', '')
                                logger.info(f"使用DrissionPage从文本中获取到产品访问链接: {product_data[product_id]['visit_url']}")
                                break
                    
                    # 寻找产品图片image1
                    # 获取产品图片
                    image = ""
                    try:
                        # 尝试从data-test="post-header-image"的元素中获取图片URL
                        header_image = soup.find(attrs={'data-test': 'post-header-image'})
                        logger.info(f"header_image: {header_image}")
                        if header_image:
                            style = header_image.get('style', '')
                            if style:
                                # 使用正则表达式提取URL
                                urls = re.findall(r'url\((https://ph-files\.imgix\.net/[^?]+)', style)
                                if urls:
                                    # 获取第一个URL
                                    image = urls[0]
                                    logger.info(f"成功获取产品图片: {image}")
                    except Exception as e:
                        logger.error(f"获取产品图片失败: {str(e)}")
                    
                    # 寻找主题标签
                    topic_elements = soup.find_all('a', href=re.compile(r'/topics/'))
                    if topic_elements:
                        topics = [elem.text.strip() for elem in topic_elements if elem.text.strip()]
                        if topics:
                            product_data[product_id]['topics'] = topics
                            logger.info(f"使用DrissionPage获取到主题标签: {topics}")
                    
                    # 寻找投票数
                    vote_elements = soup.find_all(attrs={"data-test": "vote-button"})
                    if vote_elements:
                        vote_text = vote_elements[0].text.strip()
                        if "Upvote" in vote_text:
                            votes_str = vote_text.replace("Upvote", "").strip()
                            votes_str = votes_str.replace(",", "")
                            if votes_str.isdigit():
                                product_data[product_id]['votes'] = int(votes_str)
                                logger.info(f"使用DrissionPage获取到投票数: {product_data[product_id]['votes']}")
                    else:
                        # 尝试查找包含数字的元素
                        vote_elements = soup.find_all(text=re.compile(r'\d+\s*upvote', re.IGNORECASE))
                        if vote_elements:
                            for vote_text in vote_elements:
                                votes_match = re.search(r'(\d+)', vote_text)
                                if votes_match:
                                    product_data[product_id]['votes'] = int(votes_match.group(1))
                                    logger.info(f"使用DrissionPage从文本中获取到投票数: {product_data[product_id]['votes']}")
                                    break
                    # 获取产品图片和描述
                    try:
                        image = ""
                        header_image = soup.find(attrs={'data-test': 'post-header-image'})
                        logger.info(f"header_image: {header_image}")
                        
                        # 获取图片URL
                        if header_image:
                            style = header_image.get('style', '')
                            if style:
                                urls = re.findall(r'url\((https://ph-files\.imgix\.net/[^?]+)', style)
                                if urls:
                                    image = urls[0]
                                    product_data[product_id]['image'] = image
                                    logger.info(f"成功从style属性获取产品图片: {image}")
                        
                        # 如果从style属性没有找到图片，尝试从meta标签获取
                        if not image:
                            meta_image = soup.find('meta', property='og:image')
                            if meta_image:
                                image_url = meta_image.get('content', '')
                                if image_url and 'ph-files.imgix.net' in image_url:
                                    image = image_url.split('?')[0]
                                    product_data[product_id]['image'] = image
                                    logger.info(f"成功从meta标签获取产品图片: {image}")
                        
                        # 获取产品描述
                        if header_image:
                            parent_section = header_image.find_parent('section')
                            if parent_section:
                                # 查找紧邻的描述文本
                                next_div = parent_section.find('div')
                                if next_div:
                                    description = next_div.get_text(strip=True)
                                    if description:
                                        product_data[product_id]['description'] = description
                                        logger.info(f"成功获取产品描述: {description[:100]}...")
                    except Exception as e:
                        logger.error(f"获取产品图片和描述失败: {str(e)}")
                except Exception as e:
                    logger.warning(f"使用DrissionPage获取产品 {product_id} 的详细信息失败: {str(e)}")
                    
                    # 如果DrissionPage失败，尝试使用requests
                    try:
                        response = requests.get(link, headers=HEADERS, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # 寻找"Visit"按钮或链接
                            visit_links = soup.find_all('a', text=re.compile(r'Visit|Website', re.IGNORECASE))
                            if visit_links:
                                product_data[product_id]['visit_url'] = visit_links[0].get('href', '')
                                logger.info(f"获取到产品访问链接: {product_data[product_id]['visit_url']}")
                            else:
                                # 尝试查找包含"visit"或"website"的链接
                                visit_links = soup.find_all('a', href=re.compile(r'http'))
                                for link_elem in visit_links:
                                    link_text = link_elem.text.strip().lower()
                                    if 'visit' in link_text or 'website' in link_text:
                                        product_data[product_id]['visit_url'] = link_elem.get('href', '')
                                        logger.info(f"从文本中获取到产品访问链接: {product_data[product_id]['visit_url']}")
                                        break
        
                            
                            # 寻找主题标签
                            topic_elements = soup.find_all('a', href=re.compile(r'/topics/'))
                            if topic_elements:
                                topics = [elem.text.strip() for elem in topic_elements if elem.text.strip()]
                                if topics:
                                    product_data[product_id]['topics'] = topics
                                    logger.info(f"获取到主题标签: {topics}")
                            
                            # 寻找投票数
                            vote_elements = soup.find_all(attrs={"data-test": "vote-button"})
                            if vote_elements:
                                vote_text = vote_elements[0].text.strip()
                                if "Upvote" in vote_text:
                                    votes_str = vote_text.replace("Upvote", "").strip()
                                    votes_str = votes_str.replace(",", "")
                                    if votes_str.isdigit():
                                        product_data[product_id]['votes'] = int(votes_str)
                                        logger.info(f"获取到投票数: {product_data[product_id]['votes']}")
                            else:
                                # 尝试查找包含数字的元素
                                vote_elements = soup.find_all(text=re.compile(r'\d+\s*upvote', re.IGNORECASE))
                                if vote_elements:
                                    for vote_text in vote_elements:
                                        votes_match = re.search(r'(\d+)', vote_text)
                                        if votes_match:
                                            product_data[product_id]['votes'] = int(votes_match.group(1))
                                            logger.info(f"从文本中获取到投票数: {product_data[product_id]['votes']}")
                                            break
                    except Exception as e:
                        logger.warning(f"获取产品 {product_id} 的额外信息时出错: {str(e)}")
            except Exception as e:
                logger.warning(f"处理链接 {i} 时出错: {str(e)}")
        
        # 将合并后的产品数据添加到产品列表中
        for product_id, product in product_data.items():
            # 只添加有名称的产品
            if product['name'] and product['label']:
                # 查找对应的产品信息，获取图片URL
                for i, info in scraper.product_info.items():
                    if '/posts/' in info.get('link', '') and product_id in info.get('link', ''):
                        # 使用在fetch_product_list中获取的图片URL
                        if 'image' in info and info['image']:
                            product['image'] = info['image']
                            logger.info(f"使用列表点击方式获取的图片URL: {product['image']}")
                            break
                
                products.append(product)
                logger.info(f"使用备用方法添加产品: {product['name']}")
    except Exception as e:
        logger.error(f"使用备用方法构建产品数据失败: {str(e)}")
    
    # 如果仍然没有获取到任何产品，退出程序
    if not products:
        logger.error("无法获取任何产品信息，程序退出")
        return
    
    # 保存产品信息到JSON文件
    output_file = f'data/product_{date_str}.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    logger.info(f"成功保存 {len(products)} 个产品信息到 {output_file}")
    
    # 关闭Selenium驱动
    if hasattr(scraper, 'driver') and scraper.driver:
        scraper.driver.quit()
        logger.info("已关闭Selenium驱动")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())