#!/bin/sh
# 确保脚本在遇到错误时退出
set -euo pipefail

# 日志输出函数，统一格式
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')][Watchdog] $1"
}

log "守护进程已启动，开始监测容器健康状态..."

while true; do
    # 获取所有不健康容器的ID列表，处理可能的空输出
    unhealthy_containers=$(docker ps --filter "health=unhealthy" --format "{{.ID}}" 2>/dev/null || true)

    if [ -n "$unhealthy_containers" ]; then
        # 使用兼容方式处理容器ID列表
        container_count=$(echo "$unhealthy_containers" | wc -w | tr -d '[:space:]')
        log "检测到${container_count}个不健康的容器，准备重启..."

        # 逐个处理不健康的容器
        echo "$unhealthy_containers" | while read -r container_id; do
            if [ -n "$container_id" ]; then
                log "开始重启容器: $container_id"

                # 执行重启并检查结果
                if docker restart "$container_id" >/dev/null 2>&1; then
                    log "容器$container_id重启成功"
                else
                    log "错误：容器$container_id重启失败"
                fi
            fi
        done
    fi

    log "持续监测中，30秒后再次检查..."
    sleep 30
done
