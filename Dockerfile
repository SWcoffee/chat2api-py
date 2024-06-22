FROM python:3.11-slim

WORKDIR /app

# 仅复制requirements.txt，安装依赖
COPY requirements.txt /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制其他代码文件
COPY . /app

EXPOSE 5005

CMD ["python", "app.py"]
