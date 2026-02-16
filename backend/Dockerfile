FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    swig \
    git \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

COPY pyproject.toml .
RUN uv pip install --system -r pyproject.toml

COPY backend ./backend

EXPOSE 8200

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8200"]
