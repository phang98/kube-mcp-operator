FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_operator.py ./
CMD ["kopf", "run", "--standalone", "mcp_operator.py"]
