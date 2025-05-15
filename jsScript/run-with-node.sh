#!/bin/bash

# 设置 Node.js 环境变量
export N_PREFIX=$HOME/.n
export PATH=$N_PREFIX/bin:$PATH

# 显示 Node.js 版本，确认环境设置正确
echo "使用的 Node.js 版本:"
node -v

# 运行指定的脚本
echo "开始运行脚本..."
node markdown2image.js "../data/producthunt-daily-2025-05-13.md"
