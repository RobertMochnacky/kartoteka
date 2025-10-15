FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . .

# Expose Flask port
EXPOSE 5000

# Default command for local testing (overridden by docker-compose)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
