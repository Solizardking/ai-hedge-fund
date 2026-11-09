FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY hedge_fund/ ./hedge_fund/
COPY server.py ./

ENV PYTHONUNBUFFERED=1
# Railway injects $PORT; default for local docker runs.
ENV PORT=8080
EXPOSE 8080

CMD ["python", "server.py"]
