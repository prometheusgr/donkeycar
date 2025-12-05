# Local Development — Donkeycar

This document explains how to use the provided `Dockerfile` and `docker-compose.yml` to run a local development environment, or how to run locally in your Python venv.

## Prerequisites

- Docker Desktop installed and running (Windows: enable WSL2 integration if needed).
- `docker compose` available (bundled with Docker Desktop).
- Optional: Python 3.11 venv for running locally without Docker.

## Files added for development

- `docker-compose.yml` — builds the local image and mounts the repo.
- `docker-entrypoint.sh` — configures Jupyter at container start (supports `JUPYTER_TOKEN` or `JUPYTER_ALLOW_INSECURE`).
- `.env.example` — example environment variables for `docker compose`.

## Quickstart (Docker Compose)

1. Copy `.env.example` to `.env` and edit the values (set a token or enable insecure local mode):

```powershell
copy .env.example .env
# Edit .env in your editor and set JUPYTER_TOKEN or JUPYTER_ALLOW_INSECURE=1
```

2. Build the image and start services:

```powershell
docker compose build
docker compose up -d
```

3. Check service status and logs:

```powershell
docker compose ps
docker compose logs -f app
```

4. Open JupyterLab in your browser:

- `http://localhost:8888` (the token is printed in the container logs)

To map Jupyter to a different host port (e.g. 8080), edit `docker-compose.yml` and change the `ports` mapping for the `app` service to include `"8080:8888"`.

## Recommended `.env` values (example)

- `JUPYTER_TOKEN`: a secure token to use with Jupyter (preferred)
- `JUPYTER_ALLOW_INSECURE`: set to `1` only on trusted local networks (allows access without token/password)

See `.env.example` for the exact keys.

## Running locally without Docker (fast iteration)

If you prefer not to use Docker, use your local venv (you already have a `.venv` in this repo):

```powershell
# Activate venv (Windows PowerShell)
& .\.venv\Scripts\Activate.ps1

# Install dependencies (editable)
pip install -e .
# or, if needed with dev extras
pip install -e .[dev]

# Run Jupyter Lab
jupyter lab --no-browser --ip=127.0.0.1 --port=8888 --notebook-dir=./notebooks
```

The browser will prompt with a token, or the token will be printed in the terminal output.

## Troubleshooting

- "docker: not recognized": ensure Docker Desktop is installed and restart your terminal/VS Code after install.
- Docker client errors about connecting to daemon: ensure Docker Desktop is running and you have started the Docker service (Windows may require elevated permissions at first).
- Container repeatedly restarts: check `docker compose logs -f app` for errors — common issues include missing host directories (e.g. `notebooks/`) or file permission errors.
- Large build context causing slow builds: `.dockerignore` is present to exclude `mycar/models`, logs, `.venv`, and other large files — add further exclusions if needed.

## Useful commands

```powershell
# Rebuild and restart
docker compose build --no-cache
docker compose up -d

# Stop and remove
docker compose down

# Exec a shell
docker compose exec app bash

# View logs
docker compose logs -f app
```

## Next improvements (optional)

- Add a `Makefile` with targets: `make build`, `make up`, `make down`.
- Add a healthcheck to `docker-compose.yml`.
- Configure container to run as mapped host UID/GID for seamless file ownership on mount (optional; helpful on Linux/macOS).

If you'd like, I can add a `README.dev.md` section to the project README or create a `Makefile` now.

## Example Notebooks

The `notebooks/` folder contains several example notebooks you can open in JupyterLab. They are intended to be safe to run inside the development container and to demonstrate common tasks:

- `00-Getting-Started.ipynb` — starter notebook that checks the Python environment and verifies the editable install.
- `01-Data-Capture.ipynb` — shows how to locate data folders and creates a small placeholder recording in `notebooks/sample_data`.
- `02-Quick-Drive-Simulation.ipynb` — a small interactive playground: lists `scripts/`, runs an import test, and demonstrates running shell commands.
- `03-Visualize-Recorded-Data.ipynb` — looks for image files in common locations and displays the first image found; useful for quickly validating recorded datasets.

Tips:

- Run `00-Getting-Started.ipynb` first to confirm the environment and find the Jupyter token (if you didn't set `JUPYTER_TOKEN`).
- Run the Data Capture notebook to create `notebooks/sample_data` and a small placeholder file; then open the Visualize notebook to display images.
- Files you add to `notebooks/` are mounted into the container and available immediately in the running JupyterLab instance.

## Git / housekeeping

- To avoid committing Jupyter checkpoints, add `.ipynb_checkpoints/` to `.gitignore` (see the repo's `.gitignore`).

If you'd like, I can add a sample image to `notebooks/sample_data/` so the visualization notebook shows something immediately. I can also add a `Makefile` with convenience targets.
