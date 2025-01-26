# 使用更小的基础镜像
FROM python:3.9-alpine

# 安装构建 psutil 所需的依赖
RUN apk add --no-cache gcc python3-dev musl-dev linux-headers ffmpeg

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY config/app.py  .

# 暴露端口
EXPOSE 8000

# 启动应用，优化参数
CMD ["gunicorn", "-w", "3", "-k", "gthread", "-t", "60", "--bind", "0.0.0.0:8000", "app:app"]
