# --- Builder stage ---
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Runtime stage ---
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    libjpeg62-turbo \
    zlib1g \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash botuser

COPY --from=builder /install /usr/local

WORKDIR /app
COPY bot/ bot/

RUN mkdir -p /opt/bot/data && chown -R botuser:botuser /opt/bot/data
USER botuser

ENV PYTHONUNBUFFERED=1
ENV MPLBACKEND=Agg

CMD ["python", "-m", "bot"]
