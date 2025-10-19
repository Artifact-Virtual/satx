FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ../requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy web app
COPY . .

# Expose port
EXPOSE 8080

# Run app
CMD ["python", "app.py"]
