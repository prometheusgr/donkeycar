# Raspberry Pi Deploy Script

This file documents `scripts/deploy_pi.sh`, a small helper to update a Raspberry Pi clone of this repository, install Python dependencies, and restart the runtime service.

Quick overview
- Location: `scripts/deploy_pi.sh`
- Purpose: Pull changes from `origin`, create/activate a Python virtualenv (`.venv` by default), install dependencies, and restart the `systemd` service that runs your car.
- Behavior: If no SSH private key is found in `~/.ssh` and the `origin` remote is an SSH URL, the script will convert the remote to an HTTPS URL and retry the pull.

Usage

1. SSH into your Raspberry Pi and cd to the repository root:

```bash
cd /home/pi/mycarrepo
bash scripts/deploy_pi.sh
```

2. Optional flags:

- `--service <name>` — specify a different `systemd` service name (default: `donkeycar.service`).
- `--no-restart` — skip restarting the `systemd` service (useful for dry runs).
- `--venv <path>` — use a custom venv directory (default: `.venv`).

Examples

```bash
# Restart a service with a different name:
bash scripts/deploy_pi.sh --service mycar.service

# Update but don't restart the service:
bash scripts/deploy_pi.sh --no-restart
```

What the script does (high level)

- Verifies the current directory is a git repo and fetches latest from `origin`.
- If `git pull` fails and no SSH key is found, it attempts to convert `git@github.com:owner/repo.git` to `https://github.com/owner/repo.git` and pulls again.
- Creates a Python virtual environment at the configured `--venv` path if missing, activates it, upgrades `pip`, and installs `requirements.txt` (or does `pip install -e .` when appropriate).
- Restarts the configured `systemd` service using `sudo systemctl restart` and prints recent journal lines.

Notes & troubleshooting

- If your repo is private, pulling over HTTPS will require credentials (use a GitHub personal access token or set up `git credential` helpers). Prefer adding an SSH key for passwordless pulls.
- To make the script executable and run it directly:

```bash
chmod +x scripts/deploy_pi.sh
./scripts/deploy_pi.sh
```

- To revert the remote to SSH (if the script changed it to HTTPS):

```bash
git remote set-url origin git@github.com:<your-user>/<repo>.git
```

- The script assumes `systemd` is used to manage the car process. If you run your process differently (tmux, Docker, etc.), skip the service restart or modify the script to use your launch method.

Security

- The script will not create SSH keys for you. Ensure you protect your private keys with appropriate file permissions. If you prefer interactive credential prompts, do not convert the remote to HTTPS automatically.

If you want, I can also:
- Add a `scripts/deploy.ps1` for Windows-side push/rsync workflows.
- Add a `systemd` unit template under `scripts/` for `donkeycar.service`.
- Create a GitHub pull request with these changes (I will try to use the `gh` CLI automatically if available).
