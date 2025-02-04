FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY . .

RUN mkdir -p /app/.pytest_cache && \
    chown -R appuser:appgroup /app/.pytest_cache && \
    chmod 777 /app/.pytest_cache

USER appuser

CMD ["python", "-m", "pytest", "tests/test_cases.py", "-v"]