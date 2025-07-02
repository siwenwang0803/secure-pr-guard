FROM python:3.11-slim

WORKDIR /app

# 只添加一个包测试
RUN pip install requests

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
