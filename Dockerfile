# Production image for Cloud Run. Landing page is 3rd-party; app serves /app/* and /api/*.
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App package and static assets used by /app/* pages (logo, company-name)
COPY app ./app
COPY static/assets ./static/assets

# Cloud Run sets PORT=8080; use it so the server listens on the correct port
ENV PORT=8080
EXPOSE 8080

# Shell form so ${PORT} is expanded at runtime
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
