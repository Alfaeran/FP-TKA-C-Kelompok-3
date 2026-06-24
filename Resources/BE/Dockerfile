# ──────────────────────────────────────────────
# Dockerfile — Backend (Flask + Gunicorn)
# Lokasi: Resources/BE/Dockerfile
# ──────────────────────────────────────────────
FROM python:3.10-slim

# Prevent Python from buffering stdout/stderr (logs langsung muncul)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies terlebih dahulu (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port 5000
EXPOSE 5000

# Jalankan Gunicorn dengan 4 worker dan 100 thread per worker (mode asinkron I/O)
CMD ["gunicorn", "--workers", "4", "--threads", "100", "--worker-class", "gthread", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
