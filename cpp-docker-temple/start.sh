#!/bin/bash

# C++ Docker系统监控启动脚本

echo "==================================="
echo "    C++ Docker 系统监控程序"
echo "==================================="
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker是否运行
if ! docker info &> /dev/null; then
    echo "错误: Docker未运行，请启动Docker服务"
    exit 1
fi

echo "Docker环境检查通过"
echo ""

# 提供选择菜单
echo "请选择运行方式:"
echo "1) 使用Docker Compose启动 (推荐)"
echo "2) 使用Docker命令启动 (GCC基础镜像)"
echo "3) 使用多阶段构建Docker启动 (更小镜像)"
echo "4) 本地编译运行"
echo "5) 构建Docker镜像"
echo "6) 比较不同镜像大小"
echo "7) 清理Docker容器和镜像"
echo ""

read -p "请输入选择 (1-7): " choice

case $choice in
    1)
        echo "使用Docker Compose启动..."
        docker-compose up --build
        ;;
    2)
        echo "使用Docker命令启动 (GCC基础镜像)..."
        echo "构建镜像..."
        make build
        echo "启动容器..."
        docker run -it --privileged --name system-monitor cpp-system-monitor
        ;;
    3)
        echo "使用多阶段构建Docker启动..."
        echo "构建镜像..."
        make build-multi
        echo "启动容器..."
        docker run -it --privileged --name system-monitor cpp-system-monitor:multi-stage
        ;;
    4)
        echo "本地编译运行..."
        echo "编译程序..."
        make compile
        if [ $? -eq 0 ]; then
            echo "启动程序..."
            ./build/system_monitor
        else
            echo "编译失败"
        fi
        ;;
    5)
        echo "构建Docker镜像..."
        echo "构建GCC基础镜像版本..."
        make build
        echo "构建多阶段优化版本..."
        make build-multi
        echo "镜像构建完成"
        make compare-images
        ;;
    6)
        echo "比较镜像大小..."
        make compare-images
        ;;
    7)
        echo "清理Docker环境..."
        make clean
        echo "清理完成"
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac
