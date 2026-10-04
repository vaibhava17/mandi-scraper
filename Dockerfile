FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --system --uid 10010 --no-create-home scraper

COPY src ./src
COPY sql ./sql

USER scraper
CMD ["python", "src/main.py"]
