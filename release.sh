#!/bin/bash

# 设置错误处理
set -e

docker buildx create --use

# 获取当前日期时间作为标签，格式如: 20240621
DATE_TAG=$(date +"%Y%m%d")

# 设置Docker镜像名称和远程仓库
IMAGE_NAME="chat2api"
REMOTE_REPO="swcoffee"

# 构建并推送多架构镜像
docker buildx build --platform linux/amd64,linux/arm64 -t ${REMOTE_REPO}/${IMAGE_NAME}:${DATE_TAG} --push .

echo "Docker多架构镜像 ${REMOTE_REPO}/${IMAGE_NAME}:${DATE_TAG} 已成功推送"
