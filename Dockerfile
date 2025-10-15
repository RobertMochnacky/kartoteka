# Use official Python slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose port
EXPOSE 5000

# Use Gunicorn with factory pattern
CMD ["gunicorn", "app:create_app()", "-b", "0.0.0.0:5000", "--workers", "3"]
