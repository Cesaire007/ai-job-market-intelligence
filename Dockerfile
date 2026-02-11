FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download fr_core_news_sm || true

# Copy source code
COPY . .

# Expose ports
EXPOSE 8000 8501

# Default: run pipeline
CMD ["python", "-m", "src.pipeline"]
