#!/bin/bash

# 使用项目本地的Node.js环境
export N_PREFIX=$HOME/.n
export PATH=$N_PREFIX/bin:$PATH

# 执行脚本
node ./jsScript/split-markdown.js "$@"
