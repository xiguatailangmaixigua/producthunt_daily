#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
import traceback
import asyncio
import argparse
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def get_repo_details(driver, repo_url):
    """获取仓库详细信息"""
    logger.info(f"访问仓库详情页: {repo_url}")
    
    try:
        # 访问仓库页面
        driver.get(repo_url)
        logger.info("等待仓库页面加载...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article.markdown-body"))
        )
        
        # 获取README内容
        readme_content = ""
        try:
            readme_element = driver.find_element(By.CSS_SELECTOR, "article.markdown-body")
            readme_content = readme_element.get_attribute("innerHTML")
            logger.info(f"成功获取README内容，长度: {len(readme_content)} 字符")
        except Exception as e:
            logger.error(f"获取README内容时出错: {str(e)}")
        
        # 获取README图片
        readme_images = []
        try:
            # 使用JavaScript获取所有图片，排除徽章和小图标
            script = """
            const images = Array.from(document.querySelectorAll('article.markdown-body img'));
            return images
                .filter(img => {
                    const width = img.width || 0;
                    const height = img.height || 0;
                    const src = img.src || '';
                    // 排除徽章和小图标
                    return (width > 100 || height > 100) && 
                           !src.includes('badge') && 
                           !src.includes('shield');
                })
                .map(img => img.src)
                .filter(src => src);
            """
            readme_images = driver.execute_script(script)
            logger.info(f"成功获取README图片，数量: {len(readme_images)}")
            
            if readme_images:
                logger.info(f"找到README图片: {readme_images[0]}")
        except Exception as e:
            logger.error(f"获取README图片时出错: {str(e)}")
        
        # 获取详细描述
        description = ""
        try:
            # 使用JavaScript获取About部分的描述
            script = """
            // 尝试获取About部分的描述
            const aboutSection = document.querySelector('div[data-test-selector="about-section"]');
            if (aboutSection) {
                const descElement = aboutSection.querySelector('p');
                return descElement ? descElement.textContent.trim() : '';
            }
            
            // 备选方案：尝试其他可能包含描述的元素
            const selectors = [
                'div.BorderGrid-cell p',
                'div.f4.my-3',
                'span[itemprop="description"]'
            ];
            
            for (const selector of selectors) {
                const element = document.querySelector(selector);
                if (element && element.textContent.trim()) {
                    return element.textContent.trim();
                }
            }
            
            return '';
            """
            description = driver.execute_script(script)
            
            if description:
                logger.info(f"成功获取详细描述，长度: {len(description)} 字符")
        except Exception as e:
            logger.error(f"获取详细描述时出错: {str(e)}")
        
        # 获取主题标签
        topics = []
        try:
            # 使用JavaScript获取主题标签
            script = """
            const topics = Array.from(document.querySelectorAll('a.topic-tag'));
            return topics.map(topic => topic.textContent.trim()).filter(topic => topic);
            """
            topics = driver.execute_script(script)
            
            if topics:
                logger.info(f"成功获取主题标签，数量: {len(topics)}")
        except Exception as e:
            logger.error(f"获取主题标签时出错: {str(e)}")
        
        # 获取关注者数量
        watchers_count = 0
        try:
            # 使用JavaScript获取关注者数量
            script = """
            const socialCount = Array.from(document.querySelectorAll('a.social-count'));
            for (const count of socialCount) {
                if (count.getAttribute('href').endsWith('/watchers')) {
                    return count.getAttribute('aria-label').replace(/,/g, '').match(/\\d+/)[0];
                }
            }
            return 0;
            """
            watchers_count_str = driver.execute_script(script)
            if watchers_count_str:
                watchers_count = int(watchers_count_str)
                logger.info(f"成功获取关注者数量: {watchers_count}")
        except Exception as e:
            logger.error(f"获取关注者数量时出错: {str(e)}")
        
        # 返回仓库详情
        return {
            "description": description,
            "topics": topics,
            "readme_images": readme_images
        }
    
    except Exception as e:
        logger.error(f"获取仓库详情时出错: {str(e)}")
        return {}

async def get_trending_repos(driver, time_range="daily", language=""):
    """获取GitHub Trending仓库列表"""
    logger.info(f"获取GitHub Trending仓库列表，时间范围: {time_range}，语言: {language or '所有'}")
    
    # 构建URL
    url = "https://github.com/trending"
    if language:
        url += f"/{language}"
    url += f"?since={time_range}"
    
    logger.info(f"访问GitHub Trending页面: {url}")
    
    # 访问页面
    driver.get(url)
    
    # 等待页面加载
    logger.info("等待页面加载...")
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article.Box-row"))
        )
    except:
        logger.error("页面加载超时")
        return []
    
    # 使用JavaScript获取仓库列表信息，避免Selenium的stale element问题
    repos_js = """
        const repoArticles = document.querySelectorAll('article.Box-row');
        const repos = [];
        
        for (const article of repoArticles) {
            try {
                // 仓库名称和URL
                const titleElement = article.querySelector('h2 a');
                if (!titleElement) continue;
                
                const repoPath = titleElement.getAttribute('href').substring(1);
                const repoUrl = 'https://github.com/' + repoPath;
                
                // 仓库描述
                const descriptionElement = article.querySelector('p');
                const description = descriptionElement ? descriptionElement.textContent.trim() : '';
                
                // 编程语言
                const languageElement = article.querySelector('[itemprop="programmingLanguage"]');
                const language = languageElement ? languageElement.textContent.trim() : '';
                
                // 星标数
                const starsElement = article.querySelector('a[href*="stargazers"]');
                const stars = starsElement ? starsElement.textContent.trim().replace(',', '') : '';
                
                repos.push({
                    name: repoPath,
                    url: repoUrl,
                    description: description,
                    language: language,
                    stars: stars
                });
            } catch (e) {
                console.error('Error parsing repo:', e);
            }
        }
        
        return repos;
    """
    
    try:
        repos = driver.execute_script(repos_js)
        logger.info(f"找到 {len(repos)} 个仓库")
        return repos
    except Exception as e:
        logger.error(f"获取仓库列表出错: {str(e)}")
        return []

async def generate_markdown(repos, date_str, time_range="daily", language=""):
    """生成Markdown文件"""
    # 确保目录存在
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 生成标题
    time_range_text = {
        "daily": "今日",
        "weekly": "本周",
        "monthly": "本月"
    }.get(time_range, "今日")
    
    language_text = f"({language})" if language else ""
    
    # 生成markdown内容
    markdown_content = f"# GitHub {time_range_text}热门项目 {language_text} {date_str}\n\n"
    
    for repo in repos:
        markdown_content += f"## [{repo['name']}]({repo['url']})\n\n"
        
        # 仓库描述
        if repo['description']:
            markdown_content += f"{repo['description']}\n\n"
        
        # 主题标签
        if 'topics' in repo and repo['topics'] and len(repo['topics']) > 0:
            markdown_content += "**主题**: "
            topics_str = ", ".join([f"`{topic}`" for topic in repo['topics']])
            markdown_content += f"{topics_str}\n\n"
        
        # 基本信息
        info_parts = []
        if repo['language']:
            info_parts.append(f"**语言**: {repo['language']}")
        if repo['stars']:
            info_parts.append(f"**星标**: {repo['stars']}")
        
        if info_parts:
            markdown_content += " | ".join(info_parts) + "\n\n"
        
        # 添加README图片
        if 'readme_images' in repo and repo['readme_images'] and len(repo['readme_images']) > 0:
            markdown_content += "**预览**:\n\n"
            for img_url in repo['readme_images'][:1]:  # 只显示第一张图片
                markdown_content += f"![{repo['name']}]({img_url})\n\n"
        
        markdown_content += "\n"
    
    # 保存markdown文件
    language_suffix = f"_{language}" if language else ""
    markdown_file = os.path.join(data_dir, f"github-trending-{time_range}{language_suffix}-{date_str}.md")
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    logger.info(f"Markdown文件已保存到: {markdown_file}")
    
    # 保存JSON文件
    json_file = os.path.join(data_dir, f"github-trending-{time_range}{language_suffix}-{date_str}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON文件已保存到: {json_file}")

async def main():
    try:
        logger.info("开始执行GitHub Trending获取程序...")
        
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='获取GitHub Trending仓库')
        parser.add_argument('--date', type=str, help='指定日期，格式为YYYY-MM-DD')
        parser.add_argument('--time', type=str, choices=['daily', 'weekly', 'monthly'], 
                            default='daily', help='时间范围: daily, weekly, monthly')
        parser.add_argument('--lang', type=str, default='', help='编程语言，例如python, javascript等')
        parser.add_argument('--limit', type=int, default=0, help='限制获取的仓库数量')
        parser.add_argument('--no-details', action='store_true', help='不获取仓库详情')
        args = parser.parse_args()
        
        if args.date:
            date_str = args.date
            logger.info(f"使用当前日期: {date_str}")
        else:
            # 获取当前日期
            current_time = datetime.now()
            date_str = current_time.strftime('%Y-%m-%d')
            logger.info(f"使用当前日期: {date_str}")
        
        logger.info(f"获取GitHub Trending仓库列表，时间范围: {args.time}，语言: {args.lang or '所有'}")
        
        # 设置Chrome选项
        options = Options()
        options.add_argument("--headless")  # 无头模式
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        
        # 设置用户代理
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # 初始化WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # 获取仓库列表
        repos = await get_trending_repos(driver, args.time, args.lang)
        
        # 如果设置了限制，则只取指定数量的仓库
        if args.limit and args.limit > 0:
            repos = repos[:args.limit]
            logger.info(f"限制获取仓库数量为: {args.limit}")
        
        # 获取仓库详情
        if not args.no_details:
            enhanced_repos = []
            for repo in repos:
                try:
                    logger.info(f"获取仓库 {repo['name']} 的详情页内容")
                    details = await get_repo_details(driver, repo['url'])
                    
                    # 添加新获取的字段
                    repo['description'] = details['description']
                    repo['topics'] = details['topics']
                    repo['readme_images'] = details['readme_images']
                    
                    enhanced_repos.append(repo)
                except Exception as e:
                    logger.error(f"获取仓库 {repo['name']} 详情时出错: {str(e)}")
                    # 即使出错，也添加基本信息
                    repo['description'] = ""
                    repo['topics'] = []
                    repo['readme_images'] = []
                    enhanced_repos.append(repo)
            
            repos = enhanced_repos
        
        logger.info(f"成功获取到 {len(repos)} 个仓库")
        
        # 不再生成英文Markdown文件，只保存JSON文件
        
        # 确保目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # 保存JSON文件
        language_suffix = f"_{args.lang}" if args.lang else ""
        json_file = os.path.join(data_dir, f"github-trending-{args.time}{language_suffix}-{date_str}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(repos, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON文件已保存到: {json_file}")
        
        # 检查JSON文件是否生成正确
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                check_repos = json.load(f)
            logger.info(f"JSON文件检查成功，包含 {len(check_repos)} 个仓库")
        except Exception as e:
            logger.error(f"JSON文件检查失败: {str(e)}")
        
        # 关闭浏览器
        driver.quit()
        
        logger.info("程序执行完成")
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
