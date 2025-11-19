# Build stage
FROM python:3.12-alpine3.20 AS builder

WORKDIR /usr/src/iyconsoftNotifications

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    gcc \
    g++ \
    musl-dev \
    linux-headers \
    python3-dev

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools uvloop && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir hypercorn

# Runtime stage
FROM python:3.12-alpine3.20 as dev

WORKDIR /usr/src/iyconsoftNotifications

# Copy only necessary files from builder
COPY --from=builder /opt/venv /opt/venv
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Create temp directory with correct permissions
RUN mkdir -p /tmp && chmod 1777 /tmp

ENV PATH="$VENV_PATH/bin:$PATH"
EXPOSE 8000
CMD ["hypercorn", "src.main:app", "--workers", "1", "--bind", "0.0.0.0:8000", "--worker-class", "uvloop", "--max-requests", "10000", "--graceful-timeout", "60"]




FROM python:3.12-alpine3.20 as prod

RUN apk add --no-cache expat=2.6.3-r0
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENV_PATH=/opt/venv

RUN apk add --no-cache \
    build-base \
    gcc \
    g++ \
    libffi-dev \
    musl-dev \
    linux-headers \
    python3-dev

# Create a non-root user 'developer' with a home directory and assign to 'developer' group
RUN addgroup -S developer && adduser -S developer -G developer

# Create a virtual environment with permissions for 'developer' user
RUN python3 -m venv $VENV_PATH && \
    $VENV_PATH/bin/pip install --upgrade pip
    
RUN chown -R developer:developer $VENV_PATH

# Set user to 'developer' for running subsequent commands
USER developer

COPY installed_apps.txt .
RUN $VENV_PATH/bin/pip install --no-cache-dir -r installed_apps.txt

COPY --chown=developer:developer . /usr/src/iyconsoftNotifications/
WORKDIR /usr/src/iyconsoftNotifications
ENV PATH="$VENV_PATH/bin:$PATH"

EXPOSE 8053
CMD ["gunicorn", "--bind", "0.0.0.0:8053", "-w", "8", "-k", "uvicorn.workers.UvicornWorker", "app.main:app"]
