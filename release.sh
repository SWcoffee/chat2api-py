#!/bin/bash

# 设置错误处理
set -e

# 获取当前日期时间作为标签，格式如: 20240621
DATE_TAG=$(date +"%Y%m%d")

# 设置Docker镜像名称和远程仓库
IMAGE_NAME="chat2api"
REMOTE_REPO="swcoffee"

# 动态获取当前系统的架构平台
ARCH=$(uname -m)

case $ARCH in
    x86_64)
        TARGET_PLATFORM="linux/amd64"
        ;;
    aarch64)
        TARGET_PLATFORM="linux/arm64"
        ;;
    armv7l)
        TARGET_PLATFORM="linux/arm/v7"
        ;;
    armv6l)
        TARGET_PLATFORM="linux/arm/v6"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

echo "Building for platform: ${TARGET_PLATFORM}"

# 构建Docker镜像
docker build --platform ${TARGET_PLATFORM} -t ${IMAGE_NAME}:${DATE_TAG} .

# 登录Docker远程仓库（如果需要）
# docker login ${REMOTE_REPO}

# 标记Docker镜像
docker tag ${IMAGE_NAME}:${DATE_TAG} ${REMOTE_REPO}/${IMAGE_NAME}:${DATE_TAG}

# 推送Docker镜像到远程仓库
docker push ${REMOTE_REPO}/${IMAGE_NAME}:${DATE_TAG}

# 登出Docker远程仓库（如果需要）
# docker logout ${REMOTE_REPO}

echo "Docker镜像 ${IMAGE_NAME}:${DATE_TAG} 已成功推送到 ${REMOTE_REPO}"
