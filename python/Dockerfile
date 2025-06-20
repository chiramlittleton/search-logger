FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy app code
COPY . .

# Install dependencies (includes 'standard' extras for reload support)
RUN pip install --no-cache-dir fastapi uvicorn[standard] asyncpg

# Expose port
EXPOSE 8000

# Run FastAPI with live reload enabled
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
