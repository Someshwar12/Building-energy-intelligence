FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY apps/model_service/requirements.txt ./requirements.txt

COPY ml ./ml
COPY apps/model_service ./apps/model_service
COPY reports/generated/phase1_baseline_results.csv ./reports/generated/phase1_baseline_results.csv

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "apps.model_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]