FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY hedge_fund/ ./hedge_fund/
COPY . ./ctx/
RUN echo "=== /app/ctx listing ===" && ls -la /app/ctx && echo "=== end ==="
COPY main.py ./
CMD ["python", "main.py"]
