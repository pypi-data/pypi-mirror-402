FROM ubuntu:latest

# 更新apt源并安装必要的依赖
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 创建软链接使python指向python3.12
RUN ln -s /usr/bin/python3.12 /usr/bin/python

# 使用虚拟环境并安装uv包管理器
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install uv

# 将虚拟环境的bin目录添加到PATH
ENV PATH="/opt/venv/bin:${PATH}"

# 创建工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 验证uv是否安装成功
RUN echo "Verifying uv installation..." && \
    uv --version

# 安装项目依赖并构建wheel文件
RUN uv sync --all-extras --all-packages --no-sources

# 构建项目wheel文件
RUN mkdir -p dist && \
    uv build --package kimi-cli --no-sources --out-dir dist && \
    uv build --package kimi-code --no-sources --out-dir dist && \
    uv build --package kosong --no-sources --out-dir dist/kosong && \
    uv build --package pykaos --no-sources --out-dir dist/pykaos && \
    uv build --package kimi-sdk --no-sources --out-dir dist/kimi-sdk

# 显示构建结果
RUN ls -la dist/

CMD ["/bin/bash"]