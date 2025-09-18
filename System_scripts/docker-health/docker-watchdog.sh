#!/bin/sh

# # 确保脚本在遇到错误时退出
# set -euo pipefail

# 配置参数
CHECK_INTERVAL=${CHECK_INTERVAL:-3}         # 检查间隔（秒）
LOG_LINES=${LOG_LINES:-1000}                # 收集的日志行数
LOG_DIR=${LOG_DIR:-"./container_logs"}      # 日志保存目录

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [Docker Watchdog] $1"
}

# 收集容器日志函数
collect_container_logs() {
    local container_id="$1"
    local log_lines="${2:-$LOG_LINES}"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local log_file="$LOG_DIR/container_${container_id}_${timestamp}.log"
    
    log "收集容器 $container_id 的最近 $log_lines 行日志..."
    
    # 获取容器名称
    local container_name=$(docker inspect --format='{{.Name}}' "$container_id" 2>/dev/null | sed 's/^[\/]//')
    [ -z "$container_name" ] && container_name="unknown"
    
    # 创建日志文件头部信息
    {
        echo "=========================================="
        echo "容器ID: $container_id"
        echo "容器名称: $container_name"
        echo "收集时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "日志行数: $log_lines"
        echo "=========================================="
        echo ""
    } > "$log_file"
    
    # 收集容器日志
    if docker logs --tail "$log_lines" "$container_id" >> "$log_file" 2>&1; then
        log "容器 $container_id 日志已保存到: $log_file"
    else
        log "警告：无法获取容器 $container_id 的日志"
        echo "错误：无法获取容器日志" >> "$log_file"
    fi
}

log "守护进程已启动，开始监测容器健康状态..."
log "配置参数 - 检查间隔: ${CHECK_INTERVAL}秒, 日志行数: $LOG_LINES, 日志目录: $LOG_DIR"

while true; do
    # 获取不健康容器 ID 列表
    unhealthy_containers=$(docker ps --filter "health=unhealthy" --format "{{.ID}}" 2>/dev/null || true)

    if [ -n "$unhealthy_containers" ]; then
        # 统计容器数量（使用更可靠的方法）
        container_count=$(echo "$unhealthy_containers" | wc -l | tr -d '[:space:]')
        log "检测到 $container_count 个不健康容器，准备收集日志并重启..."

        # 逐个处理容器
        echo "$unhealthy_containers" | while read -r container_id; do
            if [ -n "$container_id" ]; then
                # 先收集日志
                collect_container_logs "$container_id"
                
                # 然后重启容器
                log "开始重启容器: $container_id"
                if docker restart "$container_id" >/dev/null 2>&1; then
                    log "容器 $container_id 重启成功"
                else
                    log "错误：容器 $container_id 重启失败"
                fi
            fi
        done
    fi

    log "持续监测中，${CHECK_INTERVAL}秒后再次检查..."
    sleep "$CHECK_INTERVAL"
done