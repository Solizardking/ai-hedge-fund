FROM python:3.12-slim

WORKDIR /app

# requirements.txt is inlined on purpose: Railway's build-context snapshot
# for this repo intermittently drops small root files (observed across 8
# deploys), while directory transfers (hedge_fund/) arrive intact.
RUN printf 'PyYAML>=6.0,<7\n' > requirements.txt && pip install --no-cache-dir -r requirements.txt

COPY backend/hedge_fund/ ./hedge_fund/

ENV PYTHONUNBUFFERED=1
# Railway injects $PORT; default for local docker runs.
ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "hedge_fund.backend_api"]
