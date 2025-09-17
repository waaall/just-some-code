ARG ARCH=cuda

FROM python:3.11.13-slim AS base-cpu
FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime AS base-cuda

FROM base-${ARCH} AS final

WORKDIR /app
COPY train_gpu_test.py .

CMD ["python", "train_gpu_test.py"]