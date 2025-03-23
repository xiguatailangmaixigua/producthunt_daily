import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_driver():
    """创建一个能够绕过Cloudflare检测的Selenium驱动"""
    logger.info("创建能够绕过Cloudflare检测的Selenium驱动...")
    
    # 设置Chrome选项
    chrome_options = webdriver.ChromeOptions()
    
    # 添加仿真真实浏览器的选项
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 随机用户代理
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # 语言和地区设置
    chrome_options.add_argument("--lang=en-US,en;q=0.9")
    chrome_options.add_argument("--accept-lang=en-US,en;q=0.9")
    
    # 禁用webdriver标志
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # 禁用cookie域名检查
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
    
    return driver

def bypass_cloudflare(driver, url):
    """尝试绕过Cloudflare挑战"""
    logger.info(f"尝试访问URL并绕过Cloudflare挑战: {url}")
    
    # 访问URL
    driver.get(url)
    
    # 等待页面加载
    time.sleep(5)
    
    # 检查是否遇到Cloudflare挑战页面
    if "请稍候" in driver.title or "Just a moment" in driver.title or "Checking your browser" in driver.page_source:
        logger.info("检测到Cloudflare挑战页面，等待验证通过...")
        
        # 增加等待时间，让Cloudflare验证完成
        time.sleep(30)
        
        # 模拟人类行为：随机鼠标移动
        actions = ActionChains(driver)
        for _ in range(5):
            # 随机坐标
            x, y = random.randint(100, 700), random.randint(100, 500)
            actions.move_by_offset(x, y).perform()
            time.sleep(random.uniform(0.5, 2))
        
        # 随机滚动
        for _ in range(3):
            scroll_amount = random.randint(100, 300)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(1, 3))
        
        # 再次等待
        time.sleep(30)
        
        # 刷新页面
        driver.refresh()
        time.sleep(10)
        
        # 再次检查是否仍然在Cloudflare挑战页面
        if "请稍候" in driver.title or "Just a moment" in driver.title or "Checking your browser" in driver.page_source:
            logger.warning("仍然在Cloudflare挑战页面，尝试更长时间等待...")
            time.sleep(60)
            driver.refresh()
            time.sleep(10)
    
    logger.info(f"当前页面标题: {driver.title}")
    return driver

if __name__ == "__main__":
    # 测试代码
    driver = create_driver()
    try:
        bypass_cloudflare(driver, "https://www.producthunt.com/")
        print("页面源代码:", driver.page_source[:500])  # 只打印前500个字符
    finally:
        driver.quit()
