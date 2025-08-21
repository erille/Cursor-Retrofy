FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8888

ENV DB_PATH=/srv/sqlite/ma_base.sqlite \
    IMAGES_DIR=/data/images \
    SECRET_KEY=please-change-me

CMD ["python", "app.py"]


