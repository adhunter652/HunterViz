# Admin server for Cloud Run. Auth via IAP; no sign-in in app.
FROM python:3.11-slim

WORKDIR /app

# So "app" package is found when uvicorn runs (Cloud Run may not inherit WORKDIR for CMD in some setups)
ENV PYTHONPATH=/app
ENV PORT=8080

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY static ./static

EXPOSE 8080

# Use python -m so sys.path is correct; port from PORT env (Cloud Run sets PORT=8080)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
