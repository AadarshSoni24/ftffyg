FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application and bundled datasets
COPY . /app/backend

ENV PYTHONPATH=/app
ENV PORT=8000
ENV TZ=UTC

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
