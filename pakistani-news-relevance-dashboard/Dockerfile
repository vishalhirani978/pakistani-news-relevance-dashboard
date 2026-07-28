### Builder: create a wheelhouse so final image doesn't need build tools
FROM python:3.11-slim AS builder
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install build-time dependencies for building wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       g++ \
       libgl1 \
       libglib2.0-0 \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r /app/requirements.txt

### Runtime: minimal image that only contains runtime libs
FROM python:3.11-slim AS runtime
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install only runtime OS libs
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libgl1 \
       libglib2.0-0 \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
COPY requirements.txt /app/requirements.txt

# Install Python packages from the pre-built wheelhouse
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir --no-index --find-links /wheels -r /app/requirements.txt

# Copy app sources last for better cache
COPY . /app

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
