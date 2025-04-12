FROM python:3.11-slim

WORKDIR /data
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install the latest Poetry using the official installer
RUN curl -sSL https://install.python-poetry.org | python3 -
# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy only dependency files first for better caching
COPY pyproject.toml ./

# Copy the rest of the project
COPY pastry.py pastry_core.py ./
COPY src/ ./src/
COPY benchmarks/ ./benchmarks/
COPY benchmark.sh ./

RUN cat pyproject.toml

# Install dependencies using Poetry
RUN poetry install

# Set the entrypoint to run via Poetry
ENTRYPOINT ["poetry", "run", "python", "pastry.py"]

# Default command (can be overridden)
CMD ["--help"]


# to build the image:
# docker build -t pastry:latest .

# to run the container:
# docker run --rm -v $(pwd):/app pastry:latest --help