# 优化的C++项目Docker构建
# 使用gcc基础镜像，无需额外安装开发工具

FROM gcc:13

# 设置工作目录
WORKDIR /app

# 复制整个项目到容器
COPY cpp_temp/ .

# 使用项目的Makefile进行构建
# 由于不依赖外部工具，无需apt-get安装任何包
RUN make clean && make release

# # 暴露端口（如果需要）
# EXPOSE 9906

# 运行编译好的程序
CMD ["./build/system_monitor"]
