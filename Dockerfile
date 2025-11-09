# 🐍 Use official lightweight Python base image
FROM python:3.12-slim

# Prevent Python from writing .pyc files & enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# 🧰 Install required system dependencies + MariaDB client for RDS testing
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev gcc mariadb-client \
    && rm -rf /var/lib/apt/lists/*

# 📦 Copy project files into the container
COPY . /app

# 🐍 Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 🌐 Expose Flask default port
EXPOSE 5000

# 🏃 Command to start the Flask app
CMD ["python", "app.py"]
