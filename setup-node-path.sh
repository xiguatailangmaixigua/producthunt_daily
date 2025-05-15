#!/bin/bash

# 确保 Node.js 的路径被正确加载
export N_PREFIX=$HOME/.n
export PATH=$N_PREFIX/bin:$PATH

# 显示 Node.js 版本
echo "Node.js 版本："
node -v

# 创建别名，方便使用
echo "创建别名..."
echo 'alias md2img="node '$PWD'/jsScript/split-markdown.js"' >> ~/.zshrc
echo 'alias md2img-single="node '$PWD'/jsScript/convert-single-file.js"' >> ~/.zshrc

echo "配置完成！请运行以下命令使配置生效："
echo "source ~/.zshrc"
echo ""
echo "之后您可以使用以下命令："
echo "md2img <markdown文件路径>       # 将Markdown文件按产品分割并转换为多张图片"
echo "md2img-single <markdown文件路径> # 将整个Markdown文件转换为一张图片"
