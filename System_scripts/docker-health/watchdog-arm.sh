#!/bin/sh
echo "$(date '+%Y-%m-%d %H:%M:%S')[Watchdog] 守护进程已启动..."
while true; do
  unhealthy=$(docker ps --filter "health=unhealthy" --format "{{.ID}}")
  if [ -n "$unhealthy" ]; then
    echo "[Watchdog] 检测到容器[$unhealthy]不健康，执行重启..."
    docker restart $unhealthy
  fi
  echo "$(date '+%Y-%m-%d %H:%M:%S')持续监测中..."
  sleep 30
done