FROM python:3.9-alpine3.13
LABEL maintainer="H.Bazai"

ENV PYTHONUNBUFFERED 1

COPY requirements.txt /tmp/
COPY requirements.dev.txt /tmp/
COPY app /app/
WORKDIR /app
EXPOSE 8000

ARG DEV=true
RUN rm -rf /var/cache/apk/*
RUN apk update && \
    apk add --no-cache --virtual .build-deps \
        build-base postgresql-dev musl-dev zlib-dev jpeg-dev && \
    apk add --no-cache postgresql-client postgresql-dev jpeg && \
    python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; then \
        /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp/* && \
    apk --purge del .build-deps && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R root:users /vol && \
    chown -R root /app && \
    chmod -R 755 /vol && \
    chmod -R 777 /app

ENV PATH="/py/bin:$PATH"
USER root
