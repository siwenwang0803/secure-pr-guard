FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 先安装基础包（避免网络问题）
RUN pip install --no-cache-dir requests openai

# 复制entrypoint脚本
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 复制必要文件
COPY action_runner.py /app/ 2>/dev/null || echo "action_runner.py not found, using mock"

ENTRYPOINT ["/entrypoint.sh"]
