# Use slim Python 3.11 image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    asyncpg \
    redis==4.6.0  # ✅ This includes redis.asyncio

# Make sure the startup script is executable
RUN chmod +x start.sh

# Expose FastAPI's port
EXPOSE 8000

# Start API and background worker
CMD ["./start.sh"]
