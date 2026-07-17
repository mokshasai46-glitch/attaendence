FROM python:3.11-slim

WORKDIR /code

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose port dynamically (using $PORT assigned by Render, falling back to 7860 for Hugging Face)
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-7860}"]
