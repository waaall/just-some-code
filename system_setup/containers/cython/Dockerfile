# ----------- 第一阶段：构建阶段 -----------
FROM rcny-mlp:v1.0.0 AS builder
WORKDIR /build

# 先复制国内的源列表文件
COPY debian.sources /etc/apt/sources.list.d/

# 然后执行更新和安装，并修正包名
RUN apt-get update && \
    apt-get install -y build-essential python3-dev && \
    pip install Cython --default-timeout=300000 --trusted-host mirrors.aliyun.com -i https://mirrors.aliyun.com/pypi/simple/ && \
    rm -rf /var/lib/apt/lists/*

COPY . .

# 运行构建脚本生成C文件 & 编译C文件为SO文件
RUN python builder.py && \
    cd build && python ../compile.py

# ----------- 第二阶段：运行阶段 -----------
FROM rcny-mlp:v1.0.0
WORKDIR /home/machine-learning-platform

# 复制启动脚本
COPY help/docker-entrypoint.sh /
RUN mkdir /docker-entrypoint.d && chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

# 复制编译后的代码（SO文件+必要文件）
COPY --from=builder /build/build/ ./

# 清理不需要的文件并生成构建时间戳
RUN rm -rf help tests build dist *.spec requirements.txt && \
    TZ=Asia/Shanghai date +"%Y-%m-%d %H:%M:%S" > ./web/build_time.txt

# 使用gunicorn启动Flask应用
CMD [ "gunicorn", "-c", "gunicorn.conf.py", "manage:app" ]