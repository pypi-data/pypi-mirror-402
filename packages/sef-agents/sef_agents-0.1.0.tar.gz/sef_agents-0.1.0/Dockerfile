# Production Dockerfile for SEF-Agents MCP Server
# Fallback option if FastMCP Cloud doesn't support Python 3.13 via fastmcp.json

FROM python:3.13-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/
COPY README.md ./

# Install dependencies using uv
RUN uv pip install --system . && \
    uv pip cache purge

# Lambda Web Adapter expects port 8080 by default
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["python", "-m", "sef_agents.server"]
