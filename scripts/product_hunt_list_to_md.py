import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from dashscope import Generation
from bs4 import BeautifulSoup
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import random
from producthunt import ProductHunt
import requests
import feedparser
import re
from tenacity import retry, wait_exponential, stop_after_attempt
import cloudscraper
import asyncio
import logging

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

class ProductHuntScraper:
    def __init__(self):
        self.driver = None
        self.product_elements = []
        self.product_info = {}

    def init_selenium_driver(self):
        """初始化Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920x1080')
        
        # 添加更真实的用户代理和请求头
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--accept-language=zh-CN,zh;q=0.9,en;q=0.8')
        chrome_options.add_argument('--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8')
        chrome_options.add_argument('--sec-ch-ua="Google Chrome";v="120", "Chromium";v="120", "Not=A?Brand";v="99"')
        chrome_options.add_argument('--sec-ch-ua-mobile=?0')
        chrome_options.add_argument('--sec-ch-ua-platform="macOS"')
        
        # 禁用自动化控制特征
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 使用 webdriver_manager 自动安装匹配的 ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 修改 webdriver 和 navigator 特征
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            "acceptLanguage": "zh-CN,zh;q=0.9,en;q=0.8",
            "platform": "MacIntel"
        })
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']})")
        self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")

    async def fetch_product_list(self):
        """获取产品列表页面内容"""
        try:
            logging.info("访问Product Hunt主页...")
            self.driver.get('https://www.producthunt.com')
            
            logging.info("等待页面加载...")
            time.sleep(15)  # 增加等待时间
            
            # 尝试滚动页面以触发内容加载
            logging.info("滚动页面以加载更多内容...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            
            logging.info("收集产品元素...")
            # 使用更多的选择器组合
            selectors = [
                "article",
                "div[class*='item_']",
                "div[class*='post_']",
                "div > a[href*='/posts/']",
                "a[href*='/posts/']",
                "div[class*='item'] a[href*='/posts/']"
            ]
            
            self.product_elements = []
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    self.product_elements = elements
                    logging.info(f"使用选择器 '{selector}' 找到 {len(elements)} 个产品元素")
                    break
                
            if not self.product_elements:
                logging.warning("使用预定义选择器未找到产品元素，尝试查找所有链接...")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                self.product_elements = [link for link in all_links if '/posts/' in link.get_attribute("href", "")]
            
            logging.info(f"找到 {len(self.product_elements)} 个产品元素")

            # 获取每个元素的基本信息
            for i, element in enumerate(self.product_elements[:15]):
                try:
                    # 获取链接
                    if element.tag_name == 'a':
                        link = element.get_attribute("href")
                    else:
                        link = element.find_element(By.CSS_SELECTOR, "a[href*='/posts/']").get_attribute("href")

                    if link and '/posts/' in link:
                        # 获取元素的HTML内容
                        html = element.get_attribute('outerHTML')
                        # 获取元素的文本内容
                        text = element.text
                        # 获取元素的位置
                        location = element.location
                        # 获取元素的大小
                        size = element.size

                        self.product_info[i] = {
                            'element': element,
                            'link': link,
                            'html': html,
                            'text': text,
                            'location': location,
                            'size': size
                        }

                except Exception as e:
                    logging.error(f"获取产品元素信息时出错: {str(e)}")

            logging.info(f"成功缓存 {len(self.product_info)} 个产品元素的信息")
            
            # 打印每个元素的基本信息供选择
            for i, info in self.product_info.items():
                logging.info(f"\n元素 {i}:")
                logging.info(f"链接: {info['link']}")
                logging.info(f"文本: {info['text'][:200]}...")  # 只显示前200个字符
                logging.info(f"位置: {info['location']}")
                logging.info(f"大小: {info['size']}\n")

            return True
            
        except Exception as e:
            logging.error(f"获取产品列表时出错: {str(e)}")
            return False

    async def get_product_by_index(self, index):
        """根据索引获取指定的产品信息"""
        if index not in self.product_info:
            logging.error(f"索引 {index} 不存在")
            return None

        info = self.product_info[index]
        return await self.get_product_info(info['link'])

    async def fetch_with_selenium(self):
        """使用Selenium获取Product Hunt页面内容"""
        try:
            # 获取产品列表
            success = await self.fetch_product_list()
            if not success:
                return []

            # 获取前2个不重复的产品的信息
            products = []
            processed_urls = set()
            i = 0
            count = 0
            
            while count < 10 and i < len(self.product_info):
                info = self.product_info[i]
                if info['link'] not in processed_urls:
                    product = await self.get_product_by_index(i)
                    if product:
                        products.append(product)
                        processed_urls.add(info['link'])
                        count += 1
                        logging.info(f"成功获取第 {count} 个产品的信息")
                    time.sleep(random.uniform(1, 3))
                i += 1
            
            return products
            
        except Exception as e:
            logging.error(f"获取数据时出错: {str(e)}")
            return []
        finally:
            if self.driver:
                self.driver.quit()

    def get_product_elements(self):
        """获取产品元素列表"""
        return self.product_elements

    async def get_product_info(self, product_url):
        """获取产品详细信息"""
        driver = self.driver
        driver.get(product_url)
        logging.info(f"访问产品页面: {product_url}")

        try:
            # 等待页面加载
            wait = WebDriverWait(driver, 15)
            
            # 获取产品名称
            name_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
            name = name_element.text.strip()
            
            # 获取产品简介（label）- 通常在标题下方的小段落
            try:
                # 首先尝试获取标题下方的第一个div中的文本
                label_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1 + div")))
                label = label_element.text.strip()
                
                # 如果没有找到或文本为空，尝试其他选择器
                if not label:
                    # 尝试查找包含产品描述的div
                    label_elements = driver.find_elements(By.CSS_SELECTOR, "div.text-base, div.text-md, div.text-lg")
                    for elem in label_elements:
                        text = elem.text.strip()
                        if text and len(text) > 10:  # 确保文本有一定长度
                            label = text
                            break
            except Exception as e:
                logging.error(f"获取label失败: {str(e)}")
                label = ""
            
            # 获取产品描述（Maker的介绍）
            maker_introduction = ""
            try:
                # 保存页面源代码以便调试
                with open('temp_page.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                logging.info("已保存页面源代码到temp_page.html")
                
                # 查找包含"Hey Product Hunt"的文本
                logging.info("尝试查找包含'Hey Product Hunt'的文本")
                
                # 使用更简单的选择器，查找所有文本节点
                all_elements = driver.find_elements(By.TAG_NAME, "div")
                logging.info(f"找到 {len(all_elements)} 个div元素")
                
                # 查找包含"Hey Product Hunt"的元素
                hey_ph_elements = []
                for i, elem in enumerate(all_elements):
                    try:
                        text = elem.text.strip()
                        if "Hey Product Hunt" in text and len(text) > 100:
                            hey_ph_elements.append((i, elem, text))
                            logging.info(f"找到包含'Hey Product Hunt'的元素 {i}: {text[:150]}...")
                    except:
                        continue
                
                logging.info(f"找到 {len(hey_ph_elements)} 个包含'Hey Product Hunt'的元素")
                
                # 处理找到的元素
                if hey_ph_elements:
                    # 选择最短的包含"Hey Product Hunt"的元素，这通常是Maker的发言
                    hey_ph_elements.sort(key=lambda x: len(x[2]))
                    _, _, text = hey_ph_elements[0]
                    
                    # 提取"Hey Product Hunt"开始的部分
                    hey_ph_index = text.find("Hey Product Hunt")
                    if hey_ph_index >= 0:
                        maker_introduction = text[hey_ph_index:]
                        logging.info(f"提取的Maker介绍: {maker_introduction[:150]}...")
                
                # 如果没有找到包含"Hey Product Hunt"的文本，尝试查找Maker的发言
                if not maker_introduction:
                    logging.info("没有找到包含'Hey Product Hunt'的文本，尝试查找Maker的发言")
                    
                    # 查找包含"Maker"标记的元素
                    maker_elements = []
                    for i, elem in enumerate(all_elements):
                        try:
                            text = elem.text.strip()
                            if "Maker" in text and len(text) > 100:
                                maker_elements.append((i, elem, text))
                                logging.info(f"找到包含'Maker'的元素 {i}: {text[:150]}...")
                        except:
                            continue
                    
                    logging.info(f"找到 {len(maker_elements)} 个包含'Maker'的元素")
                    
                    # 处理找到的Maker元素
                    if maker_elements:
                        # 选择最短的包含"Maker"的元素，这通常是Maker的发言
                        maker_elements.sort(key=lambda x: len(x[2]))
                        _, _, text = maker_elements[0]
                        
                        # 提取Maker发言
                        # 尝试找到Maker后面的第一段文本
                        maker_index = text.find("Maker")
                        if maker_index >= 0:
                            # 跳过"Maker"及其后面的一些字符，找到实际内容的开始
                            content_start = text.find("\n", maker_index)
                            if content_start >= 0:
                                maker_introduction = text[content_start:].strip()
                                logging.info(f"提取的Maker介绍: {maker_introduction[:150]}...")
                
                # 如果仍然没有找到描述，使用标签作为描述
                if not maker_introduction and label and len(label) > 10:
                    logging.info("没有找到Maker发言，使用标签作为描述")
                    maker_introduction = label
            except Exception as e:
                logging.error(f"获取Maker介绍失败: {str(e)}")
                maker_introduction = ""
                
            # 如果仍然没有描述，使用标签作为描述
            if not maker_introduction and label and len(label) > 10:
                logging.info("使用label作为描述")
                maker_introduction = label
            
            # 获取产品描述（图片下方的文本）
            description = ""
            try:
                # 方法1：尝试获取产品页面的meta描述
                try:
                    meta_desc = driver.find_element(By.XPATH, "//meta[@name='description']")
                    if meta_desc:
                        description = meta_desc.get_attribute("content")
                        logging.info(f"方法1：使用meta描述: {description[:150]}...")
                except Exception as e:
                    logging.error(f"方法1获取描述失败: {str(e)}")
                
                # 方法2：尝试获取产品页面的og:description
                if not description or len(description) < 30:
                    try:
                        og_desc = driver.find_element(By.XPATH, "//meta[@property='og:description']")
                        if og_desc:
                            description = og_desc.get_attribute("content")
                            logging.info(f"方法2：使用og:description: {description[:150]}...")
                    except Exception as e:
                        logging.error(f"方法2获取描述失败: {str(e)}")
                
                # 方法3：尝试获取产品简介文本
                if not description or len(description) < 30:
                    try:
                        # 查找可能包含产品描述的元素
                        desc_elements = driver.find_elements(By.TAG_NAME, "p")
                        for elem in desc_elements:
                            try:
                                text = elem.text.strip()
                                if text and len(text) > 50 and "Upvote" not in text and "Visit" not in text:
                                    description = text
                                    logging.info(f"方法3：找到产品描述文本: {description[:150]}...")
                                    break
                            except:
                                continue
                    except Exception as e:
                        logging.error(f"方法3获取描述失败: {str(e)}")
                
                # 如果仍然没有找到描述，使用标签作为描述
                if not description and label and len(label) > 10:
                    logging.info("没有找到描述，使用标签作为描述")
                    description = label
            except Exception as e:
                logging.error(f"获取description失败: {str(e)}")
                description = ""
                
            # 如果仍然没有描述，使用标签作为描述
            if not description and label and len(label) > 10:
                logging.info("使用label作为描述")
                description = label
            
            # 获取产品图片
            try:
                # 尝试多种方式获取产品图片
                image = ""
                
                # 方法1：尝试获取产品详情页顶部元素中的背景图片
                try:
                    header_element = driver.find_element(By.CSS_SELECTOR, "[data-test='post-header-image']")
                    style_attr = header_element.get_attribute("style")
                    
                    # 从style属性中提取图片URL
                    if style_attr and "url(" in style_attr:
                        start_idx = style_attr.find("url(") + 4
                        end_idx = style_attr.find(")", start_idx)
                        image = style_attr[start_idx:end_idx]
                        # 清理URL（移除可能的引号）
                        image = image.strip("'\"")
                        logging.info(f"方法1成功获取产品图片: {image}")
                except Exception as e:
                    logging.error(f"方法1获取image失败: {str(e)}")
                
                # 方法2：尝试获取产品缩略图
                if not image:
                    try:
                        image_elements = driver.find_elements(By.TAG_NAME, "img")
                        for img in image_elements:
                            src = img.get_attribute("src")
                            if src and ("producthunt" in src or "ph-static" in src) and "thumbnail" in src:
                                image = src
                                logging.info(f"方法2成功获取产品图片: {image}")
                                break
                    except Exception as e:
                        logging.error(f"方法2获取image失败: {str(e)}")
                
                # 方法3：尝试获取og:image元标签
                if not image:
                    try:
                        meta_image = driver.find_element(By.XPATH, "//meta[@property='og:image']")
                        if meta_image:
                            image = meta_image.get_attribute("content")
                            logging.info(f"方法3成功获取产品图片: {image}")
                    except Exception as e:
                        logging.error(f"方法3获取image失败: {str(e)}")
            except Exception as e:
                logging.error(f"获取image失败: {str(e)}")
                image = ""
                
            # 获取产品主题/关键词
            try:
                topic_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/topics/']")
                topics = [elem.text.strip() for elem in topic_elements if elem.text.strip()]
            except:
                topics = []
            
            # 获取投票数
            try:
                # 直接从投票按钮获取投票数
                vote_button = driver.find_element(By.CSS_SELECTOR, "[data-test='vote-button']")
                vote_text = vote_button.text
                
                # 提取数字部分
                if "Upvote" in vote_text:
                    votes_str = vote_text.replace("Upvote", "").strip()
                    # 处理可能的数字格式（如"1,234"）
                    votes_str = votes_str.replace(",", "")
                    votes = int(votes_str) if votes_str.isdigit() else 0
                else:
                    votes = 0
            except Exception as e:
                logging.error(f"获取投票数失败: {str(e)}")
                votes = 0
                
            # 检查是否为精选产品
            try:
                featured_elements = driver.find_elements(By.CSS_SELECTOR, "span.text-golden")
                is_featured = len(featured_elements) > 0
            except:
                is_featured = False
                
            # 获取产品访问链接
            try:
                # 尝试多种方式获取产品访问链接
                visit_url = ""
                
                # 方法1：尝试获取"Visit"按钮的链接
                try:
                    visit_buttons = driver.find_elements(By.XPATH, "//a[contains(., 'Visit') or contains(., 'visit')]")
                    for btn in visit_buttons:
                        href = btn.get_attribute("href")
                        if href and href != product_url and not href.endswith("#"):
                            visit_url = href
                            logging.info(f"方法1成功获取访问链接: {visit_url}")
                            break
                except Exception as e:
                    logging.error(f"方法1获取访问链接失败: {str(e)}")
                
                # 方法2：尝试获取任何外部链接
                if not visit_url:
                    try:
                        # 查找所有链接
                        all_links = driver.find_elements(By.TAG_NAME, "a")
                        for link in all_links:
                            href = link.get_attribute("href")
                            # 排除Product Hunt内部链接和空链接
                            if href and "producthunt.com/r/" in href:
                                visit_url = href
                                logging.info(f"方法2成功获取访问链接: {visit_url}")
                                break
                    except Exception as e:
                        logging.error(f"方法2获取访问链接失败: {str(e)}")
                
                # 方法3：尝试从页面源代码中提取
                if not visit_url:
                    try:
                        # 在页面源代码中查找可能的重定向链接
                        page_source = driver.page_source
                        soup = BeautifulSoup(page_source, 'html.parser')
                        redirect_links = soup.find_all('a', href=lambda href: href and ('redirect' in href or '/r/' in href))
                        
                        for link in redirect_links:
                            href = link.get('href')
                            if href and href != product_url:
                                # 如果链接是相对路径，转换为绝对路径
                                if href.startswith('/'):
                                    href = f"https://www.producthunt.com{href}"
                                visit_url = href
                                logging.info(f"方法3成功获取访问链接: {visit_url}")
                                break
                    except Exception as e:
                        logging.error(f"方法3获取访问链接失败: {str(e)}")
                        
                # 方法4：从JavaScript数据中提取
                if not visit_url:
                    try:
                        logging.info("尝试从JavaScript数据中提取访问链接")
                        # 查找包含redirectPath的脚本内容
                        scripts = soup.find_all('script')
                        for script in scripts:
                            if script.string and 'redirectPath' in script.string:
                                # 使用正则表达式提取redirectPath值
                                import re
                                redirect_paths = re.findall(r'redirectPath:"(/r/[^"]+)"', script.string)
                                if redirect_paths:
                                    redirect_path = redirect_paths[0]
                                    visit_url = f"https://www.producthunt.com{redirect_path}"
                                    logging.info(f"方法4成功获取访问链接: {visit_url}")
                                    break
                    except Exception as e:
                        logging.error(f"方法4获取访问链接失败: {str(e)}")
                
                # 方法5：模拟点击"Visit"按钮
                if not visit_url:
                    try:
                        logging.info("尝试模拟点击'Visit'按钮")
                        # 查找所有可能的"Visit"按钮
                        visit_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Visit') or contains(., 'visit')]")
                        visit_buttons.extend(driver.find_elements(By.CSS_SELECTOR, "a.font-medium, a.text-base, a.text-lg"))
                        
                        for button in visit_buttons:
                            try:
                                # 尝试点击按钮
                                button.click()
                                # 等待一下，让页面有时间响应
                                time.sleep(2)
                                
                                # 获取当前URL，可能已经重定向
                                current_url = driver.current_url
                                
                                # 如果已经重定向到其他网站，记录该URL
                                if "producthunt.com" not in current_url and current_url != product_url:
                                    visit_url = current_url
                                    logging.info(f"方法5成功获取访问链接: {visit_url}")
                                    # 返回到产品页面
                                    driver.get(product_url)
                                    time.sleep(2)
                                    break
                                
                                # 如果没有重定向，检查是否打开了新标签页
                                if len(driver.window_handles) > 1:
                                    # 切换到新标签页
                                    driver.switch_to.window(driver.window_handles[1])
                                    visit_url = driver.current_url
                                    logging.info(f"方法5成功获取访问链接(新标签页): {visit_url}")
                                    # 关闭新标签页并返回原标签页
                                    driver.close()
                                    driver.switch_to.window(driver.window_handles[0])
                                    break
                                
                                # 返回到产品页面
                                driver.get(product_url)
                                time.sleep(2)
                            except Exception as e:
                                logging.error(f"点击按钮失败: {str(e)}")
                                # 确保返回到产品页面
                                driver.get(product_url)
                                time.sleep(2)
                    except Exception as e:
                        logging.error(f"方法5获取访问链接失败: {str(e)}")
            except Exception as e:
                logging.error(f"获取visit_url失败: {str(e)}")
                visit_url = ""
            
            # 获取产品图标
            try:
                icon_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img[alt*='logo'], img[alt*='icon']")))
                icon = icon_element.get_attribute("src")
            except:
                try:
                    # 备选方法：获取任何可能的图标
                    icon_elements = driver.find_elements(By.CSS_SELECTOR, "img")
                    for elem in icon_elements:
                        src = elem.get_attribute("src")
                        if src and ("logo" in src.lower() or "icon" in src.lower()):
                            icon = src
                            break
                    else:
                        # 如果没有找到明确的图标，使用第一个图片
                        if icon_elements:
                            icon = icon_elements[0].get_attribute("src")
                        else:
                            icon = ""
                except:
                    icon = ""
            
            # 创建产品对象
            product = Product(
                name=name,
                product_hunt_url=product_url,
                label=label,
                maker_introduction=maker_introduction,
                topics=topics,
                votes=votes,
                is_featured=is_featured,
                created_at=datetime.now(),
                icon=icon,
                image=image,
                visit_url=visit_url,
                description=description
            )
            
            logging.info(f"成功获取产品 {name} 的信息")
            return product
            
        except Exception as e:
            logging.error(f"获取产品信息失败: {str(e)}")
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

    def to_markdown(self):
        """转换为Markdown格式"""
        markdown = f"## [{self.name}]({self.product_hunt_url})\n"
        if self.icon:
            markdown += f"![icon]({self.icon})\n"
        markdown += f"**简介**：{self.label}\n"
        markdown += f"**详细介绍**：{self.format_description(self.maker_introduction)}\n"
        
        # 添加产品图片
        if self.image:
            markdown += f"![产品图片]({self.image})\n"
            
        # 添加产品描述
        if self.description:
            markdown += f"**产品描述**：{self.format_description(self.description)}\n"
            
        # 添加产品链接
        if self.visit_url:
            markdown += f"**访问链接**: [{self.name}]({self.visit_url})\n"
            
        markdown += f"**Product Hunt**: [View on Product Hunt]({self.product_hunt_url})\n\n"
        
        # 改进关键词格式
        keywords = []
        unique_topics = list(dict.fromkeys(self.topics))
        for topic in unique_topics:
            # 将英文单词直接添加，不分割字符
            if topic and topic.strip():  # 确保关键词不为空
                keywords.append(topic.strip())
        if keywords:
            markdown += f"**关键词**：{'、'.join(keywords)}\n"
        else:
            markdown += "**关键词**：暂无\n"
        
        markdown += f"**票数**: {self.votes}\n"
        markdown += f"**是否精选**：{'是' if self.is_featured else '否'}\n"
        markdown += f"**发布时间**：{self.created_at}\n\n"
        markdown += "---\n"
        return markdown

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
    
    # 生成markdown内容
    markdown_content = f"# Product Hunt 每日精选 {date_str}\n\n"
    
    for product in products:
        markdown_content += product.to_markdown()
    
    # 保存markdown文件
    output_file = os.path.join(data_dir, f"{date_str}.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    logger.info(f"Markdown文件已保存到: {output_file}")
    
    # 保存JSON文件
    json_file = os.path.join(data_dir, f"product_{date_str}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump([product.to_dict() for product in products], f, ensure_ascii=False, indent=2)
    logger.info(f"JSON文件已保存到: {json_file}")

async def main():
    try:
        logger.info("开始执行主程序...")
        load_dotenv()
        
        # 获取当前北京时间
        beijing_tz = pytz.timezone('Asia/Shanghai')
        current_time = datetime.now(beijing_tz)
        date_str = current_time.strftime('%Y-%m-%d')
        
        logger.info(f"获取 {date_str} 的产品列表...")
        
        # 获取产品列表
        scraper = ProductHuntScraper()
        scraper.init_selenium_driver()
        products = await scraper.fetch_with_selenium()
        
        if not products:
            logger.error("未能获取到产品列表")
            return
            
        logger.info(f"成功获取到 {len(products)} 个产品")
        
        # 生成markdown文件
        await generate_markdown(products, date_str)
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}", exc_info=True)
    finally:
        logger.info("程序执行完成")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())