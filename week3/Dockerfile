
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

# UVICORN_WORKERS sets the number of API processes per container (default 1).
# keep-alive 75 s is longer than the load balancer idle timeout (60 s); with
# uvicorn default of 5 s the load balancer occasionally got a 502.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-1} --timeout-keep-alive 75"]
