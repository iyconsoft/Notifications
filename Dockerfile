FROM python:3.12-alpine3.20 AS dev

WORKDIR /usr/src/referralapi
RUN apk add --no-cache \
    expat \
    build-base \
    g++ \
    libffi-dev \
    openssl-dev \
    python3-dev 
    

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENV_PATH=/opt/venv

RUN python3 -m venv $VENV_PATH && \
    $VENV_PATH/bin/pip install --upgrade pip && pip install --upgrade setuptools

RUN mkdir -p /tmp /usr/src/referralapi && \
    chmod 1777 /tmp /usr/src/referralapi

COPY requirements.txt ./
RUN $VENV_PATH/bin/pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PATH="$VENV_PATH/bin:$PATH"

EXPOSE 8000
CMD ["hypercorn", "src.main:app", "--bind", "0.0.0.0:8000", "--workers", "2", "--worker-class", "uvloop", "--max-requests", "10000", "--timeout", "300", "--graceful-timeout", "60"]

