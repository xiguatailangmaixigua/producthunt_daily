import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import puppeteer from 'puppeteer';
import { marked } from 'marked';

// ESM中需要这样获取 __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 生成HTML模板
 * @param {string} markdown - 已转换为HTML的Markdown内容
 * @param {Object} options - 配置选项
 * @returns {string} - 完整的HTML模板
 */
function generateHtmlTemplate(markdown, options = {}) {
    const {
        title = '',
        darkMode = false,
        width = 800,
        fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        customCss = ''
    } = options;

    const theme = darkMode ? 'dark' : 'light';
    const backgroundColor = darkMode ? '#1e1e1e' : '#ffffff';
    const textColor = darkMode ? '#ffffff' : '#333333';
    
    return `
    <!DOCTYPE html>
    <html lang="zh-CN" data-theme="${theme}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${title}</title>
        <style>
            :root {
                --background-color: ${backgroundColor};
                --text-color: ${textColor};
                --border-color: ${darkMode ? '#444' : '#eaeaea'};
                --link-color: ${darkMode ? '#58a6ff' : '#0366d6'};
                --heading-color: ${darkMode ? '#ffffff' : '#111111'};
                --quote-bg: ${darkMode ? '#2d333b' : '#f6f8fa'};
                --quote-border: ${darkMode ? '#444d56' : '#dfe2e5'};
                --code-bg: ${darkMode ? '#2d333b' : '#f6f8fa'};
            }
            
            body {
                font-family: ${fontFamily};
                line-height: 1.6;
                color: var(--text-color);
                background-color: var(--background-color);
                max-width: ${width}px;
                margin: 0 auto;
                padding: 20px;
                word-wrap: break-word;
            }
            
            h1, h2, h3, h4, h5, h6 {
                margin-top: 24px;
                margin-bottom: 16px;
                font-weight: 600;
                line-height: 1.25;
                color: var(--heading-color);
            }
            
            h1 { font-size: 2em; border-bottom: 1px solid var(--border-color); padding-bottom: 0.3em; }
            h2 { font-size: 1.5em; border-bottom: 1px solid var(--border-color); padding-bottom: 0.3em; }
            h3 { font-size: 1.25em; }
            h4 { font-size: 1em; }
            
            p, ul, ol {
                margin-top: 0;
                margin-bottom: 16px;
            }
            
            a {
                color: var(--link-color);
                text-decoration: none;
            }
            
            a:hover {
                text-decoration: underline;
            }
            
            img {
                max-width: 100%;
                box-sizing: border-box;
                background-color: var(--background-color);
                border-radius: 4px;
            }
            
            blockquote {
                padding: 0 1em;
                color: ${darkMode ? '#9ea7b3' : '#6a737d'};
                border-left: 0.25em solid var(--quote-border);
                background-color: var(--quote-bg);
                margin: 0 0 16px 0;
            }
            
            pre {
                background-color: var(--code-bg);
                border-radius: 3px;
                padding: 16px;
                overflow: auto;
                font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            }
            
            code {
                background-color: var(--code-bg);
                border-radius: 3px;
                padding: 0.2em 0.4em;
                font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            }
            
            pre code {
                background-color: transparent;
                padding: 0;
            }
            
            table {
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 16px;
            }
            
            table th, table td {
                padding: 6px 13px;
                border: 1px solid var(--border-color);
            }
            
            table tr {
                background-color: var(--background-color);
                border-top: 1px solid var(--border-color);
            }
            
            table tr:nth-child(2n) {
                background-color: ${darkMode ? '#2d333b' : '#f6f8fa'};
            }
            
            hr {
                height: 0.25em;
                padding: 0;
                margin: 24px 0;
                background-color: var(--border-color);
                border: 0;
            }
            
            /* 自定义样式 */
            ${customCss}
        </style>
    </head>
    <body>
        <div class="markdown-body">
            ${markdown}
        </div>
    </body>
    </html>
    `;
}

/**
 * 将Markdown文件转换为图片
 * @param {string} markdownFilePath - Markdown文件路径
 * @param {Object} customOptions - 自定义配置选项
 * @returns {Promise<string>} - 生成的图片路径
 */
async function convertMarkdownToImage(markdownFilePath, customOptions = {}) {
    try {
        // 读取markdown文件
        const markdown = fs.readFileSync(markdownFilePath, 'utf-8');
        const fileName = path.basename(markdownFilePath, '.md');
        
        // 确保输出目录存在
        const outputDir = customOptions.outputDir || path.join(__dirname, '..', 'images');
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
        
        // 生成输出路径
        const outputPath = customOptions.outputPath || path.join(outputDir, `${fileName}.png`);
        
        // 默认配置
        const defaultOptions = {
            title: fileName,
            width: 800,
            quality: 100,
            darkMode: false,
            padding: 20,
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
            customCss: '',
            fullPage: true,
            waitUntil: 'networkidle0',
            omitBackground: false
        };
        
        // 合并默认配置和自定义配置
        const options = { ...defaultOptions, ...customOptions };
        
        // 将Markdown转换为HTML
        const htmlContent = marked(markdown);
        
        // 生成完整的HTML模板
        const html = generateHtmlTemplate(htmlContent, options);
        
        // 启动浏览器
        const browser = await puppeteer.launch({
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        try {
            // 创建新页面
            const page = await browser.newPage();
            
            // 设置视口大小
            await page.setViewport({
                width: options.width,
                height: 800, // 初始高度，会根据内容自动调整
                deviceScaleFactor: 2 // 提高分辨率
            });
            
            // 加载HTML内容
            await page.setContent(html, {
                waitUntil: options.waitUntil
            });
            
            // 等待所有图片加载完成
            await page.evaluate(() => {
                return Promise.all(
                    Array.from(document.querySelectorAll('img'))
                        .filter(img => !img.complete)
                        .map(img => new Promise(resolve => {
                            img.onload = img.onerror = resolve;
                        }))
                );
            });
            
            // 截图
            await page.screenshot({
                path: outputPath,
                fullPage: options.fullPage,
                omitBackground: options.omitBackground
            });
            
            console.log(`✅ 成功将 ${fileName}.md 转换为图片: ${outputPath}`);
            return outputPath;
        } finally {
            // 确保浏览器关闭
            await browser.close();
        }
    } catch (error) {
        console.error(`❌ 转换 ${path.basename(markdownFilePath)} 失败:`, error);
        throw error;
    }
}

/**
 * 批量转换目录下的所有Markdown文件
 * @param {string} sourceDir - 源目录
 * @param {Object} options - 转换选项
 * @returns {Promise<Array<string>>} - 生成的所有图片路径
 */
async function batchConvertMarkdownFiles(sourceDir = '', options = {}) {
    // 如果未指定源目录，使用默认的data目录
    const dataDir = sourceDir || path.join(__dirname, '..', 'data');
    
    try {
        // 读取目录下的所有文件
        const files = fs.readdirSync(dataDir);
        
        // 过滤出.md文件
        const markdownFiles = files.filter(file => file.endsWith('.md'));
        
        if (markdownFiles.length === 0) {
            console.log(`⚠️ 警告: 在 ${dataDir} 目录下没有找到Markdown文件`);
            return [];
        }
        
        console.log(`🔍 找到 ${markdownFiles.length} 个Markdown文件，开始转换...`);
        
        // 转换每个markdown文件
        const conversionPromises = markdownFiles.map(file => {
            const filePath = path.join(dataDir, file);
            return convertMarkdownToImage(filePath, options);
        });
        
        // 等待所有转换完成
        const results = await Promise.allSettled(conversionPromises);
        
        // 统计成功和失败的数量
        const successful = results.filter(r => r.status === 'fulfilled').length;
        const failed = results.filter(r => r.status === 'rejected').length;
        
        console.log(`📊 转换完成: ${successful} 成功, ${failed} 失败`);
        
        // 返回所有成功转换的图片路径
        return results
            .filter(r => r.status === 'fulfilled')
            .map(r => r.value);
    } catch (error) {
        console.error(`❌ 批量转换失败:`, error);
        throw error;
    }
}

// 如果直接运行此脚本，则处理默认data目录下的所有markdown文件
if (import.meta.url === `file://${process.argv[1]}`) {
    const args = process.argv.slice(2);
    const sourceDir = args[0] ? path.resolve(args[0]) : '';
    
    // 自定义配置
    const options = {
        width: 1200,         // 图片宽度
        quality: 100,        // 图片质量
        darkMode: false,     // 是否使用暗色模式
        fullPage: true,      // 是否截取整个页面
        waitUntil: 'networkidle0', // 等待网络空闲
        customCss: `
            /* 产品猎手特定样式 */
            .markdown-body {
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            h1 {
                color: #da552f;
                text-align: center;
                margin-bottom: 30px;
            }
            h2 {
                color: #da552f;
                margin-top: 30px;
            }
            img {
                display: block;
                margin: 20px auto;
                max-height: 400px;
                border: 1px solid #eaeaea;
            }
            blockquote {
                background-color: #f9f9f9;
                border-left: 4px solid #da552f;
                padding: 10px 15px;
                margin: 20px 0;
            }
            hr {
                border: none;
                height: 1px;
                background-color: #eaeaea;
                margin: 30px 0;
            }
        `
    };
    
    batchConvertMarkdownFiles(sourceDir, options)
        .then(imagePaths => {
            if (imagePaths.length > 0) {
                console.log('🎉 所有图片已生成:');
                imagePaths.forEach(path => console.log(`  - ${path}`));
            }
        })
        .catch(err => {
            console.error('❌ 程序执行失败:', err);
            process.exit(1);
        });
}

// 导出函数，以便其他模块可以使用
export { convertMarkdownToImage, batchConvertMarkdownFiles };
