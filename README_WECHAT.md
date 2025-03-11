# 微信公众号发布指南

本项目支持将每日精选的Product Hunt产品信息自动发布到微信公众号。

## 功能概述

1. **获取Product Hunt每日热门产品**：自动抓取Product Hunt平台上的热门产品信息。
2. **翻译为中文**：使用阿里通义大模型API将产品信息翻译成中文。
3. **生成Markdown文件**：将翻译后的内容整理成美观的Markdown格式。
4. **生成封面图片**：自动生成适合微信公众号的封面图片，包含当日最热门产品的图标。
5. **生成HTML文件**：将Markdown内容转换为适合微信公众号的HTML格式。
6. **发布到微信公众号**：支持自动或手动将内容发布到微信公众号。

## 使用方法

### 一键执行

运行以下命令，将自动完成从获取数据到生成HTML文件的全部流程：

```bash
python scripts/run_all.py
```

脚本会询问是否要自动发布到微信公众号。如果选择"是"，将尝试使用API自动发布；如果选择"否"，将提供HTML文件和封面图片的路径，供您手动发布。

### 手动发布到微信公众号

如果您选择手动发布，或者自动发布因IP白名单等原因失败，请按照以下步骤操作：

1. 打开微信公众号后台（https://mp.weixin.qq.com/）
2. 点击"图文消息" -> "写图文消息"
3. 在编辑器中点击"HTML"按钮
4. 打开生成的HTML文件（位于`data/YYYY-MM-DD_wechat.html`），复制其中的全部内容
5. 粘贴到微信公众号编辑器的HTML编辑框中
6. 上传封面图片（位于`assets/cover.jpg`）
7. 编辑标题（建议使用"Product Hunt 每日精选 YYYY-MM-DD"格式）
8. 点击"发布"按钮

## 单独执行各步骤

如果您想单独执行某个步骤，可以使用以下命令：

### 1. 获取Product Hunt每日热门产品

```bash
python scripts/product_hunt_list_to_md.py
```

### 2. 翻译产品信息为中文

```bash
python scripts/translate_to_chinese.py
```

### 3. 生成中文Markdown文件

```bash
python scripts/generate_chinese_md.py
```

### 4. 生成封面图片

```bash
python scripts/generate_cover_image.py
```

### 5. 生成微信公众号HTML文件

```bash
python scripts/generate_wechat_html.py
```

### 6. 发布到微信公众号（需要配置API）

```bash
python scripts/publish_to_wechat.py
```

## 配置说明

### 环境变量

在项目根目录创建`.env`文件，并配置以下环境变量：

```
# 阿里通义大模型API密钥（用于翻译）
DASHSCOPE_API_KEY=your_dashscope_api_key

# 微信公众号API凭证（用于自动发布）
WECHAT_APPID=your_wechat_appid
WECHAT_APPSECRET=your_wechat_appsecret
```

### 微信公众号API配置

如果您希望使用自动发布功能，需要完成以下配置：

1. 登录微信公众平台（https://mp.weixin.qq.com/）
2. 获取AppID和AppSecret（开发 -> 基本配置）
3. 配置IP白名单（开发 -> 基本配置 -> IP白名单）
   - 添加运行脚本的服务器IP地址
4. 将AppID和AppSecret添加到`.env`文件中

## 封面图片生成说明

封面图片生成功能会自动：

1. 选择当日票数最高的产品
2. 下载产品的icon图标
3. 使用PIL库生成美观的封面图片，包含产品名称和图标
4. 保存为微信公众号推荐的尺寸（900x383像素）
5. 将图片保存到`assets/cover_日期.jpg`和`assets/cover.jpg`

封面图片采用随机颜色方案，每次生成的封面图片风格都会有所不同，增加视觉多样性。

## 故障排除

### 微信公众号API访问失败

如果遇到"IP白名单"错误，请确保：

1. 已在微信公众平台配置了运行脚本的服务器IP
2. 服务器IP没有变化（如使用动态IP，需要及时更新白名单）

如果仍然无法解决，请使用手动发布方式。
