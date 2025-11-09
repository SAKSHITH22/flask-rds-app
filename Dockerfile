# Dockerfile
FROM python:3.12-slim

# Create app directory
WORKDIR /app

# Install system deps required by mysql-connector or bcrypt
RUN apt-get update && apt-get install -y build-essential default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirement.txt /app/requirement.txt
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirement.txt

# Copy app code
COPY . /app

# Expose port
EXPOSE 5000

# Use non-root user (optional but recommended)
# RUN useradd --create-home appuser
# USER appuser

ENV FLASK_ENV=production

CMD ["python", "app.py"]
