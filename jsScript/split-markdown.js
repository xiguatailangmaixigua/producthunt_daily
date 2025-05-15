import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { convertMarkdownToImage } from './markdown2image.js';

// ESM中需要这样获取 __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 将Markdown文件按产品分割并转换为多张图片
 * @param {string} markdownFilePath - Markdown文件路径
 * @param {Object} options - 转换选项
 * @returns {Promise<Array<string>>} - 生成的所有图片路径
 */
async function splitMarkdownAndConvert(markdownFilePath, options = {}) {
    try {
        // 读取markdown文件
        const markdown = fs.readFileSync(markdownFilePath, 'utf-8');
        const fileName = path.basename(markdownFilePath, '.md');
        
        // 提取日期信息，用于生成图片文件名
        const dateMatch = fileName.match(/(\d{4}-\d{2}-\d{2})$/);
        const dateStr = dateMatch ? dateMatch[1] : '';
        
        // 确保临时目录存在
        const tempDir = path.join(__dirname, '..', 'temp');
        if (!fs.existsSync(tempDir)) {
            fs.mkdirSync(tempDir, { recursive: true });
        }
        
        // 确保输出目录存在
        const outputDir = options.outputDir || path.join(__dirname, '..', 'images');
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
        
        // 提取标题行
        const titleMatch = markdown.match(/^# (.+)$/m);
        const title = titleMatch ? titleMatch[1] : '';
        
        // 使用正则表达式分割Markdown文件
        // 匹配以 ## 开头的标题行，作为每个产品的开始
        const productSections = markdown.split(/^## \d+\./m).filter(section => section.trim());
        
        // 处理标题部分（如果有）
        let titleSection = '';
        if (title) {
            titleSection = `# ${title}\n\n`;
        }
        
        console.log(`🔍 找到 ${productSections.length} 个产品条目，开始转换...`);
        
        // 转换每个产品部分
        const conversionPromises = productSections.map(async (section, index) => {
            // 提取产品名称作为文件名的一部分
            const productNameMatch = section.match(/^([^\n]+)/);
            const productName = productNameMatch 
                ? productNameMatch[1].trim().replace(/[^\w\u4e00-\u9fa5]+/g, '-').substring(0, 30) 
                : `product-${index + 1}`;
            
            // 创建带有标题的完整Markdown内容
            const productContent = `${titleSection}## ${index + 1}.${section}`;
            
            // 创建临时Markdown文件
            const tempFilePath = path.join(tempDir, `${dateStr}-${productName}.md`);
            fs.writeFileSync(tempFilePath, productContent);
            
            // 设置输出路径
            const outputPath = path.join(outputDir, `${dateStr}-${productName}.png`);
            const productOptions = { 
                ...options, 
                outputPath 
            };
            
            // 转换为图片
            try {
                const imagePath = await convertMarkdownToImage(tempFilePath, productOptions);
                console.log(`✅ 成功将产品 ${index + 1} 转换为图片: ${imagePath}`);
                return imagePath;
            } catch (error) {
                console.error(`❌ 转换产品 ${index + 1} 失败:`, error);
                throw error;
            } finally {
                // 删除临时文件
                if (fs.existsSync(tempFilePath)) {
                    fs.unlinkSync(tempFilePath);
                }
            }
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
        console.error(`❌ 分割转换失败:`, error);
        throw error;
    }
}

// 获取当前日期字符串
function getCurrentDateString() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 如果直接运行此脚本
if (import.meta.url === `file://${process.argv[1]}`) {
    const args = process.argv.slice(2);
    let markdownFilePath = args[0];
    
    // 如果没有提供文件路径，使用当天日期的默认文件
    if (!markdownFilePath) {
        const currentDate = getCurrentDateString();
        markdownFilePath = path.join(__dirname, '..', 'data', `producthunt-daily-${currentDate}.md`);
        console.log(`未提供文件路径，将使用默认文件：${markdownFilePath}`);
        
        // 检查文件是否存在
        if (!fs.existsSync(markdownFilePath)) {
            console.error(`错误：默认文件 ${markdownFilePath} 不存在`);
            process.exit(1);
        }
    }
    
    // 自定义配置
    const options = {
        width: 1200,         // 图片宽度
        darkMode: false,     // 是否使用暗色模式
        fullPage: true,      // 是否截取整个页面
        waitUntil: 'networkidle0', // 等待网络空闲
        customCss: `
            /* 产品猎手特定样式 */
            body {
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                max-width: 1000px;
                margin: 0 auto;
                border: 1px solid #e1e4e8;
                border-radius: 10px;
            }
            .markdown-body {
                padding: 20px;
            }
            h1 {
                color: #e27730;
                text-align: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 1px solid #e1e4e8;
            }
            h2 {
                color: #333;
                margin-top: 10px;
                font-size: 1.5em;
            }
            p {
                margin: 8px 0;
            }
            a {
                color: #0366d6;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            img {
                display: block;
                margin: 20px auto;
                max-width: 90%;
                max-height: 400px;
                border-radius: 5px;
            }
            strong {
                font-weight: 600;
            }
            hr {
                border: none;
                height: 1px;
                background-color: #e1e4e8;
                margin: 20px 0;
            }
            .keyword {
                display: inline-block;
                margin-right: 10px;
            }
        `
    };
    
    splitMarkdownAndConvert(markdownFilePath, options)
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

export { splitMarkdownAndConvert };
