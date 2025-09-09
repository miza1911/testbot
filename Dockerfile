# ===== Dockerfile =====
FROM python:3.12-slim

# 1) Базовые оптимизации
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# (опционально) локаль/таймзона, если надо
# ENV TZ=Asia/Seoul

WORKDIR /app

# 2) Устанавливаем системные пакеты (минимум)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# 3) Сначала зависимости — лучше кешируется
COPY requirements.txt .
RUN pip install -r requirements.txt

# 4) Копируем всё приложение
COPY . .

# 5) Стартовый процесс — просто Python-воркер
CMD ["python", "main.py"]
