# 1. 基础镜像：使用一个官方的、轻量级的 Python 3.11 镜像
FROM python:3.11-slim

# 2. 工作目录：在容器内创建一个 /app 文件夹，并进入
WORKDIR /app

# 3. 复制清单：把我们的依赖清单复制到容器的 /app 文件夹中
COPY requirements.txt .

# 4. 安装依赖：在容器内运行 pip install，安装清单里的所有库
RUN pip install --no-cache-dir -r requirements.txt

# 5. 复制所有代码：把当前文件夹(.)的所有代码 (main.py, .env) 复制到容器的 /app
COPY . .

# 6. 暴露端口：告诉 Docker，我们的应用在容器内部的 8000 端口上运行
EXPOSE 8000

# 7. 启动命令：当容器启动时，运行这个命令来启动 uvicorn
#    --host 0.0.0.0 是必须的，它让容器可以从外部访问
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]