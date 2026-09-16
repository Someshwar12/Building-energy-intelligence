FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml ./
COPY ml ./ml
COPY apps/model_service ./apps/model_service

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "apps.model_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]