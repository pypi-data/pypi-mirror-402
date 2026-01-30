FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container
COPY . /app

# Set working directory
WORKDIR /app

# Install dependencies (from lockfile for reproducibility)
RUN uv sync --frozen --no-cache

# Run the MCP server (adjust entrypoint as needed)
CMD ["uv", "run", "server.py"]