import { convertMarkdownToImage } from './markdown2image.js';

// 获取命令行参数
const filePath = process.argv[2];

if (!filePath) {
  console.error('请提供 Markdown 文件路径');
  process.exit(1);
}

// 自定义配置
const options = {
  width: 1200,         // 图片宽度
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

// 转换单个文件
convertMarkdownToImage(filePath, options)
  .then(imagePath => {
    console.log(`🎉 图片已生成: ${imagePath}`);
  })
  .catch(err => {
    console.error('❌ 转换失败:', err);
    process.exit(1);
  });
