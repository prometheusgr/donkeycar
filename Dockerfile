FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1 \
	JUPYTER_PORT=8888

WORKDIR /app

# Install minimal system deps needed for builds and git
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
	build-essential \
	git \
	curl \
	ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Ensure pip tooling is up-to-date
RUN python -m pip install --upgrade pip setuptools wheel

# Copy just packaging files first to leverage Docker layer cache
COPY pyproject.toml setup.cfg README.md requirements.txt /app/

# Copy package source needed for setup-time metadata (e.g. version attr)
# so setuptools can import `donkeycar` when evaluating setup.cfg
COPY donkeycar /app/donkeycar

# Install project with tensorflow extras and dev requirements
RUN pip install -e .[tf] && pip install -e .[dev]

# Install JupyterLab (modern interface) and matplotlib used by example notebooks.
RUN pip install jupyterlab matplotlib

# Create an unprivileged user for development
RUN useradd -m -s /bin/bash dev \
 && chown -R dev:dev /app

# Add the repository after installs so local edits are quick when mounted
COPY . /app

# Add entrypoint script to allow safer runtime configuration (token or insecure opt-in)
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER dev

# Expose ports (informational - use -p on `docker run` to publish)
EXPOSE 8887 8888

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["jupyter", "lab", "--no-browser", "--ip=0.0.0.0", "--port=8888", "--notebook-dir=/app/notebooks", "--allow-root"]