#!/bin/sh

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [Watchdog] $1"
}

log "守护进程已启动，开始监测容器健康状态..."

while true; do
    # 获取不健康容器 ID 列表
    unhealthy_containers=$(docker ps --filter "health=unhealthy" --format "{{.ID}}" 2>/dev/null)

    if [ -n "$unhealthy_containers" ]; then
        # 统计容器数量（兼容 busybox）
        container_count=$(echo "$unhealthy_containers" | wc -l | tr -d '[:space:]')
        log "检测到 $container_count 个不健康容器，准备重启..."

        # 逐个重启容器
        echo "$unhealthy_containers" | while read container_id; do
            if [ -n "$container_id" ]; then
                log "开始重启容器: $container_id"
                if docker restart "$container_id" >/dev/null 2>&1; then
                    log "容器 $container_id 重启成功"
                else
                    log "错误：容器 $container_id 重启失败"
                fi
            fi
        done
    fi

    log "持续监测中，30秒后再次检查..."
    sleep 30
done