# GitHub Trending 爬取工具

这个工具用于爬取 GitHub Trending 页面上的热门项目，并生成中英文的 Markdown 和 JSON 文件。

## 功能特点

- 爬取 GitHub Trending 页面上的热门项目
- 支持按日期、时间范围（每日、每周、每月）和编程语言进行筛选
- 使用阿里通义大模型 API 将项目描述翻译成中文
- 生成美观的 Markdown 文件，方便在博客或网站上展示
- 保存完整的项目数据为 JSON 格式，便于后续处理

## 安装依赖

```bash
pip install selenium webdriver-manager pytz python-dotenv dashscope
```

## 使用方法

### 一键执行全部流程

使用 `run_github_trending.py` 脚本可以一键执行全部流程：

```bash
python scripts/run_github_trending.py [--date YYYY-MM-DD] [--time daily|weekly|monthly] [--lang 语言名称]
```

参数说明：
- `--date`：指定日期，格式为 YYYY-MM-DD，默认为当前日期
- `--time`：时间范围，可选值为 daily（每日）、weekly（每周）、monthly（每月），默认为 daily
- `--lang`：编程语言，例如 python、javascript 等，默认为所有语言

### 分步执行

也可以分步执行各个脚本：

1. 获取 GitHub Trending 项目：

```bash
python scripts/github_trending.py [--date YYYY-MM-DD] [--time daily|weekly|monthly] [--lang 语言名称]
```

2. 翻译项目描述：

```bash
python scripts/translate_github_trending.py [--date YYYY-MM-DD] [--time daily|weekly|monthly] [--lang 语言名称]
```

3. 生成中文 Markdown 文件：

```bash
python scripts/generate_github_trending_md.py [--date YYYY-MM-DD] [--time daily|weekly|monthly] [--lang 语言名称]
```

## 文件说明

执行脚本后，会在 `data` 目录下生成以下文件：

- `github-trending-{time}-{date}.md`：英文 Markdown 文件
- `github-trending-{time}-{date}.json`：英文 JSON 文件
- `github-trending-{time}-{date}_zh.json`：中文 JSON 文件
- `github-trending-{time}-{date}_zh.md`：中文 Markdown 文件

其中，`{time}` 为时间范围（daily、weekly、monthly），`{date}` 为日期（YYYY-MM-DD）。如果指定了编程语言，文件名中会包含语言名称。

## 环境变量

需要在 `.env` 文件中设置阿里通义大模型 API 密钥：

```
DASHSCOPE_API_KEY=your_api_key
```

## 注意事项

- 脚本使用 Selenium 爬取 GitHub Trending 页面，需要安装 Chrome 浏览器
- 翻译功能依赖于阿里通义大模型 API，需要有效的 API 密钥
- 爬取过程中可能会受到网络状况和 GitHub 页面结构变化的影响
