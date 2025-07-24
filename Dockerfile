# Use Python 3.12 slim image for smaller size
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get dist-upgrade -y && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN uv pip install --system .

# Set default environment variables
ENV MEILI_HTTP_ADDR=http://meilisearch:7700
ENV MEILI_MASTER_KEY=""

# Run the MCP server
CMD ["python", "-m", "src.meilisearch_mcp"]