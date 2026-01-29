FROM python:3.10-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY src/ src/

# Install the project
RUN uv pip install --system .
RUN uv pip install --system pydantic>=2.0.0

# Set entrypoint
ENTRYPOINT ["mcp-extent"]
