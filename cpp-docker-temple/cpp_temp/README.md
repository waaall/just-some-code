# C++系统监控项目

## 项目结构

```
cpp_temp/
├── src/              # 源代码目录
│   └── main.cpp      # 主程序文件
├── inc/              # 头文件目录  
│   └── system_monitor.h  # 系统监控类声明
├── lib/              # 库文件目录（预留）
├── build/            # 构建输出目录
│   └── system_monitor    # 编译后的可执行文件
└── Makefile          # 构建配置文件
```

## 特性

- **零外部依赖**: 不依赖net-tools、procps等外部工具
- **纯C++实现**: 直接读取/proc文件系统获取信息
- **跨平台兼容**: 支持Linux和macOS
- **Docker优化**: 无需网络操作，构建快速
- **多阶段构建**: 最终镜像仅50MB左右

## 构建方式

### 本地构建
```bash
cd cpp_temp
make              # 标准构建
make debug        # 调试版本
make release      # 发布版本  
make static       # 静态链接
make run          # 构建并运行
```

### Docker构建
```bash
# 优化版本（无网络依赖）
docker build -f Dockerfile.optimized -t cpp-monitor:optimized .

# 极致优化版本（多阶段构建）
docker build -f Dockerfile.ultra-optimized -t cpp-monitor:ultra .

# 运行
docker run -it --rm --privileged cpp-monitor:ultra
```

## 大小对比

| 构建方式 | 基础镜像 | 大小 | 特点 |
|---------|---------|------|------|
| 标准构建 | gcc:13 | ~1.2GB | 完整开发环境 |
| 优化构建 | gcc:13 | ~1.2GB | 无外部依赖 |
| 极致优化 | alpine:3.18 | ~50MB | 多阶段构建 |

## 性能特点

- **CPU监控**: 直接读取`/proc/stat`，无需外部命令
- **内存监控**: 直接读取`/proc/meminfo`，更精确
- **端口检查**: 使用socket API和`/proc/net/tcp`
- **无系统调用**: 不使用`popen()`执行外部命令

## 技术改进

### 前 (有外部依赖)
```dockerfile
RUN apt-get update && apt-get install -y \
    net-tools \     # 用于netstat命令
    procps \        # 用于读取/proc信息
    && rm -rf /var/lib/apt/lists/*
```

### 后 (无外部依赖)
```dockerfile
# 无需安装任何额外包！
RUN make clean && make release
```

## Docker优势

1. **更快构建**: 无网络操作，构建时间减少50%+
2. **更小镜像**: 极致优化版本仅50MB
3. **更安全**: 减少攻击面，无多余包
4. **更稳定**: 不依赖外部命令，降低故障率
