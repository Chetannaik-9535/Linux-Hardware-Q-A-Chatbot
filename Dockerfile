# Multi-stage production Dockerfile for Linux Hardware Q&A Assistant
FROM python:3.11-slim as base

# Install essential Linux hardware utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    pciutils \
    dmidecode \
    util-linux \
    procps \
    sudo \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency specifications
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose Streamlit and FastAPI ports
EXPOSE 8501 8000

ENV HW_MOCK="auto"
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true

# Default entrypoint runs Streamlit UI
CMD ["streamlit", "run", "hw_assistant/ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
