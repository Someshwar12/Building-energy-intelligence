FROM python:3.11-slim

WORKDIR /mlflow

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "mlflow>=3.5,<4" \
    && mkdir -p /mlflow/artifacts

EXPOSE 5000

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000", "--workers", "1", "--backend-store-uri", "sqlite:////mlflow/mlflow.db", "--default-artifact-root", "/mlflow/artifacts"]