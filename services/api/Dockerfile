FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY packages /app/packages
COPY services /app/services
COPY Makefile /app/Makefile

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    pydantic-settings \
    pyjwt \
    httpx \
    python-multipart \
    alembic \
    sqlalchemy \
    asyncpg \
    redis \
    pytest \
    pytest-asyncio

EXPOSE 8000

CMD ["uvicorn", "services.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
