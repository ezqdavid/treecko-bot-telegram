# Dockerfile for Treecko Telegram Bot - Optimized for Google Cloud Run
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Expose port (Cloud Run uses PORT env variable, default 8080)
EXPOSE 8080

# Run the application
CMD ["python", "-m", "treecko_bot.main"]
