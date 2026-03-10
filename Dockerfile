FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git unzip zip \
    && rm -rf /var/lib/apt/lists/*

CMD ["bash"]
