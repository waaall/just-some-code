# Docker Health Watchdog

这是一个用于监控Docker容器健康状态的守护进程脚本。当检测到不健康的容器时，会自动收集日志并重启容器。


**Docker Engine 检查healthy逻辑**：

* 默认状态：**starting**（直到第一次检查完成）。
* 如果健康检查命令 **成功** → **healthy**。
* **如果连续失败 **--retries** 次 → **unhealthy**。**
* **你在 **docker ps** 或 **docker inspect** 里能看到 **Status: unhealthy**。**

## 使用方法

### 基本使用

```bash
# 使用默认配置运行
./docker-watchdog.sh

# 后台运行
nohup ./docker-watchdog.sh > watchdog.log 2>&1 &
```

### 开机自启

systemd: 创建一个 service 文件 `/etc/systemd/system/docker-watchdog.service`

其中 `/usr/local/bin/docker-watchdog.sh` 改成你的脚本绝对路径，并确保它有执行权限：`chmod +x /your/path/to/docker-watchdog.sh`

```bash
[Unit]
Description=Docker Watchdog Service
After=docker.service
Requires=docker.service

[Service]
ExecStart=/usr/local/bin/docker-watchdog.sh
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

然后开启服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable docker-watchdog
sudo systemctl start docker-watchdog
```

### 自定义配置

```bash
# 设置检查间隔为60秒
CHECK_INTERVAL=60 ./watchdog.sh

# 设置收集日志行数为200行
LOG_LINES=200 ./watchdog.sh

# 设置自定义日志目录
LOG_DIR="/var/log/docker-health" ./watchdog.sh

# 组合使用多个参数
CHECK_INTERVAL=60 LOG_LINES=200 LOG_DIR="/var/log/docker-health" ./watchdog.sh
```

### 简单测试

```
docker build -f Dockerfile-unhealthy -t unhealthy-test .
docker run -d --name test-unhealthy unhealthy-test
```

## 配置参数

| 参数               | 默认值               | 说明               |
| ------------------ | -------------------- | ------------------ |
| `CHECK_INTERVAL` | 3                    | 健康检查间隔（秒） |
| `LOG_LINES`      | 1000                 | 收集的容器日志行数 |
| `LOG_DIR`        | `./container_logs` | 日志文件保存目录   |

## 日志文件格式

当检测到不健康容器时，会在指定目录下生成日志文件：

```
container_logs/
├── container_abc123_20250918_143000.log
├── container_def456_20250918_143030.log
└── ...
```

每个日志文件包含：

- 容器ID和名称
- 收集时间
- 容器的最近N行日志

## 注意事项

1. 确保运行脚本的用户有Docker操作权限
2. 建议定期清理日志目录，避免磁盘空间不足
3. 可以配合系统监控工具使用，如systemd、supervisor等
4. 生产环境建议使用绝对路径指定日志目录
5. **脚本权限**: 确保脚本有执行权限 `chmod +x watchdog.sh`
