FROM python:3.11-slim
WORKDIR /app
RUN pip install requests
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
