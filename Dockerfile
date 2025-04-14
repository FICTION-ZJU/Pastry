FROM python:3.13-slim
# For (Chinese) users who cannot access docker.io, use the following
# FROM docker.1ms.run/library/python:3.13-slim


# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    vim \
    sudo \
    curl \
    time \
    && rm -rf /var/lib/apt/lists/*

# Add a user, and make it sudoer
RUN useradd -m -s /bin/bash artifact && echo 'artifact ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
RUN chown -R artifact:artifact /home/artifact

# Set artifact as default user
USER artifact
ENV HOME=/home/artifact

WORKDIR /home/artifact

# Install the latest Poetry using the official installer
RUN curl -sSL https://install.python-poetry.org | python3 -
# Add Poetry to PATH
ENV PATH="/home/artifact/.local/bin:$PATH"
ENV POETRY_REQUESTS_TIMEOUT=60

# Copy files
COPY pastry ./pastry
COPY baselines ./baselines
COPY benchmarks ./benchmarks
COPY run.py run.sh README.md INSTRUCTIONS.md ./
RUN sudo ln -s /home/artifact/benchmarks/pastry /home/artifact/pastry/benchmarks
RUN sudo ln -s /home/artifact/benchmarks/KoAT1 /home/artifact/baselines/KoAT1/benchmarks
RUN sudo ln -s /home/artifact/benchmarks/KoAT2 /home/artifact/baselines/KoAT2/benchmarks
RUN sudo ln -s /home/artifact/benchmarks/amber /home/artifact/baselines/amber/benchmarks


WORKDIR /home/artifact/pastry

# Install dependencies for pastry using Poetry
RUN sudo chmod -R a=u .
RUN poetry install

# Install python dependencies
WORKDIR /home/artifact/baselines/amber
RUN pip3 install -r requirements.txt
RUN pip3 install sympy mpmath setuptools rich

WORKDIR /home/artifact
RUN sudo chmod a+x run.sh pastry/run.sh baselines/amber/amber baselines/KoAT1/main/run.sh baselines/KoAT1/main/koat2 baselines/KoAT2/koat2

# Set the entrypoint
ENTRYPOINT ["/bin/bash"]

# Default command (can be overridden)
CMD ["--help"]

# to build the image:
# docker buildx build -t pastry:latest .

# to run the container:
# docker run -it -v "$(pwd)/outputs:/home/artifact/pastry/outputs" -v "$(pwd)/result:/home/artifact/result" --entrypoint bash pastry:latest
