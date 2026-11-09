FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HAWKEYE_DATA_DIR=/data \
    HAWKEYE_BROWSER=cdp \
    HAWKEYE_CONTAINER=1 \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
      chromium chromium-driver xvfb xauth fonts-liberation \
      libnss3 libatk1.0-0 libatk-bridge2.0-0 libgbm1 libasound2 \
      libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 libxext6 \
      libxfixes3 libxrandr2 libxrender1 libxshmfence1 libxss1 libxtst6 \
      ca-certificates curl gosu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-web.txt /app/requirements-web.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /app/requirements-web.txt

COPY src/ /app/src/
COPY container-entrypoint.sh /usr/local/bin/container-entrypoint
RUN chmod 0755 /usr/local/bin/container-entrypoint \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin hawkeye \
    && mkdir -p /data \
    && chown -R hawkeye:hawkeye /data /app

VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3).read()" || exit 1

ENTRYPOINT ["/usr/local/bin/container-entrypoint"]
CMD ["xvfb-run", "-a", "-s", "-screen 0 1920x1080x24", "python", "src/web/host.py"]
