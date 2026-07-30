# # 构建镜像（cpu）
# docker build --build-arg ARCH=cpu -t pytorch-cpu-test .
# # 运行容器，测试 CPU
# docker run --rm pytorch-cpu-test

## ========================================

# 构建镜像（gpu）
docker build-t pytorch-cuda-test .

# 运行容器，测试 GPU
docker run --rm --gpus all pytorch-cuda-test