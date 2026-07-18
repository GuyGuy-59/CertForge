FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir Flask gunicorn cryptography
RUN mkdir -p /data

ENV PKI_DATA_DIR=/data \
    ADMIN_USER=admin \
    ADMIN_PASSWORD=changeme \
    SECRET_KEY=change-this-secret-key-in-production

EXPOSE 5000
WORKDIR /app/webapps

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["gunicorn", \
     "--bind",    "0.0.0.0:5000", \
     "--workers", "1", \
     "--threads", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "app:app"]
