FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Set environment variable for Gunicorn Python path
ENV PYTHONPATH=/app

# Run Gunicorn with factory pattern
CMD ["gunicorn", "app:create_app()", "-b", "0.0.0.0:5000", "--workers", "3", "--log-level", "info"]
