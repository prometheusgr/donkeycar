# Installing the Donkey Car Systemd Service

This guide explains how to set up the `donkeycar.service` systemd unit on your Raspberry Pi so the car starts automatically on boot and can be managed via `systemctl`.

## Quick Start

If you haven't installed the service yet, run the installation script:

```bash
bash scripts/install_service.sh
```

This will:

1. Show you the service configuration with your repository paths
2. Ask for confirmation
3. Install the service file to `/etc/systemd/system/donkeycar.service`
4. Enable the service to start on boot
5. Start the service immediately

## Manual Installation

If you prefer to install the service manually, follow these steps:

1. **Copy the service template** with the correct paths:

   ```bash
   sudo cp scripts/donkeycar.service /etc/systemd/system/donkeycar.service
   ```

2. **Edit the service file** to adjust paths for your environment:

   ```bash
   sudo nano /etc/systemd/system/donkeycar.service
   ```

   Update these lines if needed:

   - `WorkingDirectory`: Path to your donkeycar repository
   - `User`: The user that should run the car (typically `pi`)
   - `Environment PATH`: Path to your virtual environment's bin directory
   - `ExecStart`: Path to manage.py in your mycar directory

3. **Reload systemd**:

   ```bash
   sudo systemctl daemon-reload
   ```

4. **Enable the service** (start on boot):

   ```bash
   sudo systemctl enable donkeycar.service
   ```

5. **Start the service**:

   ```bash
   sudo systemctl start donkeycar.service
   ```

6. **Check the status**:
   ```bash
   sudo systemctl status donkeycar.service
   ```

## Service Management

Once installed, you can manage the service with:

```bash
# Check status
sudo systemctl status donkeycar.service

# Start the service
sudo systemctl start donkeycar.service

# Stop the service
sudo systemctl stop donkeycar.service

# Restart the service
sudo systemctl restart donkeycar.service

# View recent logs
sudo journalctl -u donkeycar.service -n 50 --no-pager

# Follow logs in real-time
sudo journalctl -u donkeycar.service -f

# View all logs for today
sudo journalctl -u donkeycar.service --since today
```

## Using a Custom Service Name

If you want to use a different service name (e.g., `mycar.service`):

```bash
# Install with a custom name
bash scripts/install_service.sh --service mycar.service

# Then use the custom name when managing:
sudo systemctl status mycar.service
sudo systemctl restart mycar.service
```

## Deploying with the Deploy Script

When you run the deploy script after the service is installed:

```bash
bash scripts/deploy_pi.sh
```

It will:

1. Pull the latest code from your repository
2. Update Python dependencies
3. **Restart** the systemd service

If the service is not yet installed, the deploy script will show you helpful instructions.

## Troubleshooting

### Service won't start

Check the logs:

```bash
sudo journalctl -u donkeycar.service -n 50 --no-pager
```

Common issues:

- **Path not found**: Verify the paths in the service file match your actual setup
- **Permission denied**: Make sure the user specified in the service file can access the car directory
- **Python module not found**: Ensure the virtual environment is activated in the service file path

### Service file not found

If you see "Unit donkeycar.service not found":

```bash
# List all installed services
systemctl list-units --all --type=service | grep donkey

# Try installing the service
bash scripts/install_service.sh
```

### Restarting manually

If the service is not installed, you can still restart the car process manually:

```bash
# SSH into your Pi and run the car directly
bash scripts/pi_start_and_calibrate.sh --start --yes
```

## Service File Template

The template file is located at `scripts/donkeycar.service`. It includes:

- **Auto-restart**: Service automatically restarts if it crashes
- **Journal logging**: Output is logged to systemd journal (viewable with `journalctl`)
- **User permissions**: Runs as the specified user (default: `pi`)
- **Boot startup**: Configured to start after the network is ready

## Environment-Specific Configuration

The `install_service.sh` script supports custom paths:

```bash
# Install with custom repository path and user
bash scripts/install_service.sh --repo /home/myuser/myrepo --user myuser

# Install with different car directory name
bash scripts/install_service.sh --car-dir my_car_config
```

## See Also

- `scripts/deploy_pi.sh` - Deploy script for pulling code and restarting the service
- `scripts/pi_start_and_calibrate.sh` - Start car directly or run calibration UI
- `PI_CALIBRATE.md` - Calibration guide
- `DEPLOY_PI.md` - Deployment guide
