FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.render.txt ./
RUN pip install --no-cache-dir -r requirements.render.txt \
    && pip install --no-cache-dir --no-deps face-recognition==1.3.0

COPY src ./src
RUN mkdir -p /app/data

CMD exec uvicorn src.web_app:app --host 0.0.0.0 --port $PORT
