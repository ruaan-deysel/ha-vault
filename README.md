# Vault Backup Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

<!--
Uncomment and customize these badges if you want to use them:

[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]
[![Discord][discord-shield]][discord]
-->

**✨ Develop in the cloud:** Want to contribute or customize this integration? Open it directly in GitHub Codespaces - no local setup required!

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ruaan-deysel/ha-vault-backup?quickstart=1)

## ✨ Features

- **Easy Setup**: Simple configuration through the UI - no YAML required
- **Backup Job Monitoring**: Track status and progress of all your backup jobs
- **Real-time Updates**: WebSocket connection for instant status updates
- **Job Control**: Run backup jobs on-demand with button entities or service calls
- **Restore Capability**: Restore backups directly from Home Assistant
- **Storage Management**: Test storage destinations and monitor health
- **Encryption Support**: Track encryption status and manage encrypted backups
- **Diagnostic Info**: View Vault version, job statistics, and system health
- **Reconfigurable**: Change connection settings anytime without removing the integration

**This integration will set up the following platforms.**

| Platform        | Description                                                       |
| --------------- | ----------------------------------------------------------------- |
| `sensor`        | Vault status, version, job statistics, per-job status and metrics |
| `binary_sensor` | Connection status, per-job running state and success indicators   |
| `button`        | Run backup jobs on-demand (one button per job)                    |

## 🚀 Quick Start

### Prerequisites

- **Vault Server**: You must have a Vault backup server running and accessible from Home Assistant
- **API Access**: You'll need the host, port (default: 24085), and API key for your Vault instance
- **HACS**: This integration requires [HACS](https://hacs.xyz/) (Home Assistant Community Store) to be installed

### Step 1: Install the Integration

Click the button below to open the integration directly in HACS:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ruaan-deysel&repository=ha-vault-backup&category=integration)

Then:

1. Click "Download" to install the integration
2. **Restart Home Assistant** (required after installation)

> **Note:** The My Home Assistant redirect will first take you to a landing page. Click the button there to open your Home Assistant instance.

<details>
<summary>**Manual Installation (Advanced)**</summary>

If you prefer not to use HACS:

1. Download the `custom_components/vault/` folder from this repository
2. Copy it to your Home Assistant's `custom_components/` directory
3. Restart Home Assistant

</details>

### Step 2: Add and Configure the Integration

**Important:** You must have installed the integration first (see Step 1) and restarted Home Assistant!

#### Option 1: One-Click Setup (Quick)

Click the button below to open the configuration dialog:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=vault)

Follow the setup wizard:

1. Enter your Vault server **host** (e.g., `vault.local` or `192.168.1.100`)
2. Enter the **port** (default: `24085`)
3. Enter your **API key** (if authentication is required)
4. Enable **TLS** if your Vault server uses HTTPS
5. Click Submit

The integration will connect to your Vault server and start monitoring your backup jobs.

#### Option 2: Manual Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for "Vault"
4. Follow the same setup steps as Option 1

### Step 3: Verify Connection

After setup, check that the integration is working:

1. Go to **Settings** → **Devices & Services** → **Vault**
2. You should see sensors for:
   - Vault Status (should show "ok" or "healthy")
   - Vault Online (binary sensor - should be "On")
3. If you have backup jobs configured, you'll see entities for each job

### Step 4: Start Using!

The integration creates entities for monitoring and controlling your Vault backup system:

- **Global Sensors**: Vault status, version, job counts, encryption status
- **Per-Job Sensors**: Job status, last run time, backup size, duration, etc.
- **Global Binary Sensors**: Connection status
- **Per-Job Binary Sensors**: Running state, last success indicator
- **Per-Job Buttons**: Run backup job on-demand

Find all entities in **Settings** → **Devices & Services** → **Vault** → click on the device.

## Available Entities

### Global Sensors

These sensors provide information about your Vault instance:

- **Vault Status**: Current health status of the Vault service
  - States: `ok`, `healthy`, `running`, or error states
- **Vault Version** (Diagnostic): Version of the Vault server
- **Jobs Total** (Diagnostic): Total number of backup jobs configured
  - Disabled by default - enable in entity settings if needed
- **Jobs Enabled** (Diagnostic): Number of enabled backup jobs
  - Disabled by default - enable in entity settings if needed
- **Encryption Status** (Diagnostic): Whether encryption is enabled
  - States: `enabled` or `disabled`
  - Disabled by default - enable in entity settings if needed

### Per-Job Sensors

For each backup job configured in Vault, the integration creates sensors to monitor that job:

- **Job Status**: Current status of the backup job
  - States: `idle`, `running`, `completed`, `failed`
- **Last Run** (Diagnostic): Timestamp of the last backup run
- **Last Run Duration** (Diagnostic): How long the last backup took (in seconds)
- **Total Runs** (Diagnostic): Total number of times this job has run
- **Last Backup Size** (Diagnostic): Size of the last backup (in bytes/MB/GB)
- **Last Run Progress** (Diagnostic): Completion percentage during active backup (0-100%)

### Global Binary Sensors

- **Vault Online**: Connection status to the Vault server
  - On: Connected and receiving data from Vault API
  - Off: Connection lost or authentication failed
  - Device class: Connectivity
  - Shows last update time and connection details

### Per-Job Binary Sensors

For each backup job, the integration creates binary sensors:

- **Job Running**: Indicates whether the backup job is currently running
  - On: Job is actively running
  - Off: Job is idle or completed
  - Device class: Running
- **Last Success**: Indicates whether the last backup completed successfully
  - On: Last backup completed successfully
  - Off: Last backup failed or no runs yet

### Per-Job Buttons

For each backup job, the integration creates a button:

- **Run Now**: Trigger an immediate backup run for this job
  - Press to start the backup job via the Vault API
  - Real-time progress updates via WebSocket
  - Coordinator refreshes automatically after triggering

## Custom Services

The integration provides powerful services for backup management and automation:

### `vault.run_backup`

Trigger an immediate backup run for a specific Vault job. You can specify the job by ID or name.

**Parameters:**

- `job_id` (optional): The numeric ID of the backup job to run
- `job_name` (optional): The name of the backup job to run

> **Note:** Provide either `job_id` or `job_name`, not both.

**Example using job ID:**

```yaml
action: vault.run_backup
data:
  job_id: 1
```

**Example using job name:**

```yaml
action: vault.run_backup
data:
  job_name: "My Important Backups"
```

### `vault.restore`

Restore an item from a Vault backup restore point. This allows you to restore containers, VMs, or folders directly from Home Assistant.

**Parameters:**

- `job_id` (required): The job ID that created the restore point
- `restore_point_id` (required): The ID of the restore point to restore from
- `item_name` (required): Name of the item to restore (container name, VM name, or folder)
- `item_type` (required): Type of item - `container`, `vm`, or `folder`
- `passphrase` (optional): Encryption passphrase if the backup was encrypted
- `destination` (optional): Override the default restore destination path

**Example restoring a container:**

```yaml
action: vault.restore
data:
  job_id: 1
  restore_point_id: 42
  item_name: "my-container"
  item_type: "container"
```

**Example restoring an encrypted backup:**

```yaml
action: vault.restore
data:
  job_id: 1
  restore_point_id: 42
  item_name: "my-vm"
  item_type: "vm"
  passphrase: "my-secure-passphrase"
  destination: "/mnt/restored-vms/"
```

### `vault.test_storage`

Test connectivity to a Vault storage destination. Useful for verifying storage configuration or diagnosing connection issues.

**Parameters:**

- `storage_id` (required): The ID of the storage destination to test

**Example:**

```yaml
action: vault.test_storage
data:
  storage_id: 1
```

The test result will be logged. Check your Home Assistant logs for success or error messages.

## Automation Examples

### Automated Nightly Backups

Create an automation to run your backups at 2 AM every day:

```yaml
automation:
  - alias: "Run Nightly Vault Backups"
    trigger:
      - platform: time
        at: "02:00:00"
    action:
      - action: vault.run_backup
        data:
          job_name: "Nightly Full Backup"
```

### Backup Before System Updates

Trigger a backup before running system updates:

```yaml
automation:
  - alias: "Backup Before Updates"
    trigger:
      - platform: state
        entity_id: update.home_assistant_core_update
        to: "on"
    action:
      - action: vault.run_backup
        data:
          job_id: 1
      - delay:
          minutes: 30
      - action: update.install
        target:
          entity_id: update.home_assistant_core_update
```

### Alert on Backup Failure

Get notified when a backup job fails:

```yaml
automation:
  - alias: "Vault Backup Failed Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.my_backup_job_last_success
        to: "off"
        for:
          minutes: 5
    action:
      - action: notify.mobile_app
        data:
          title: "Backup Failed"
          message: "Vault backup job failed. Check the logs."
```

### Monitor Backup Progress

Track backup progress and show a notification:

```yaml
automation:
  - alias: "Backup Progress Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.my_backup_job_running
        to: "on"
    action:
      - action: notify.persistent_notification
        data:
          title: "Backup Running"
          message: "Backup job started. Current progress: {{ states('sensor.my_backup_job_last_run_progress') }}%"
```

## Configuration Options

### During Setup

| Name    | Required | Description                                             | Default |
| ------- | -------- | ------------------------------------------------------- | ------- |
| Host    | Yes      | Hostname or IP address of your Vault server             | -       |
| Port    | No       | Port number for Vault API                               | 24085   |
| API Key | No       | Authentication key (if required by your Vault instance) | -       |
| TLS     | No       | Enable HTTPS/TLS connection                             | False   |

### After Setup (Options)

You can change connection settings anytime:

1. Go to **Settings** → **Devices & Services**
2. Find **Vault**
3. Click the **3 dots menu** → **Reconfigure**
4. Update the connection settings
5. Click Submit

## Troubleshooting

### Connection Issues

#### Check Vault Service

If the **Vault Online** binary sensor shows "Off":

1. Verify your Vault server is running and accessible
2. Check the host and port settings
3. Ensure Home Assistant can reach the Vault server (network connectivity)
4. Verify firewall rules allow access to the Vault port (default: 24085)
5. Check API key if authentication is required

#### Enable TLS

If your Vault server uses HTTPS:

1. Go to **Settings** → **Devices & Services** → **Vault**
2. Click **Reconfigure**
3. Enable the **TLS** option
4. Click Submit

### Enable Debug Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.vault: debug
```

Then restart Home Assistant. Check the logs at:

- **Settings** → **System** → **Logs**
- Or in `config/home-assistant.log`

### Common Issues

#### "Cannot Connect" Error

If you receive connection errors:

1. Verify the Vault server is running: `curl http://YOUR_HOST:24085/health`
2. Check the host and port settings in the integration configuration
3. Verify network connectivity between Home Assistant and Vault server
4. Check firewall rules on both sides
5. Try accessing the Vault API from Home Assistant's container/machine

#### "API Error" Messages

If you receive API-related errors:

1. Verify your API key is correct (if authentication is required)
2. Check the Vault server logs for detailed error messages
3. Ensure your Vault version is compatible
4. Download diagnostics (Settings → Devices & Services → Vault → 3 dots → Download diagnostics)

#### No Entities Appearing

If entities aren't showing up:

1. Verify the **Vault Online** sensor shows "On"
2. Check that backup jobs are configured in Vault
3. Wait for the initial data fetch (up to 1 minute)
4. Reload the integration (Settings → Devices & Services → Vault → 3 dots → Reload)
5. Check logs for errors

#### WebSocket Connection Issues

If real-time updates aren't working:

1. WebSocket connections to Vault use the same host/port as the REST API
2. Check that WebSocket connections aren't blocked by firewalls or proxies
3. Verify the Vault server supports WebSocket connections
4. Check logs for WebSocket-specific errors

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request if you have suggestions or improvements.

### 🛠️ Development Setup

Want to contribute or customize this integration? You have two options:

#### Cloud Development (Recommended)

The easiest way to get started - develop directly in your browser with GitHub Codespaces:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ruaan-deysel/ha-vault-backup?quickstart=1)

- ✅ Zero local setup required
- ✅ Pre-configured development environment
- ✅ Home Assistant included for testing
- ✅ 60 hours/month free for personal accounts

#### Local Development

Prefer working on your machine? You'll need:

- Docker Desktop
- VS Code with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

Then:

1. Clone this repository
2. Open in VS Code
3. Click "Reopen in Container" when prompted

Both options give you the same fully-configured development environment with Home Assistant, Python 3.13, and all necessary tools.

---

## 🤖 AI-Assisted Development

> **ℹ️ Transparency Notice**
>
> This integration was developed with assistance from AI coding agents (GitHub Copilot, Claude, and others). While the codebase follows Home Assistant Core standards, AI-generated code may not be reviewed or tested to the same extent as manually written code.
>
> AI tools were used to:
>
> - Generate boilerplate code following Home Assistant patterns
> - Implement standard integration features (config flow, coordinator, entities)
> - Ensure code quality and type safety
> - Write documentation and comments
>
> Please be aware that AI-assisted development may result in unexpected behavior or edge cases that haven't been thoroughly tested. If you encounter any issues, please [open an issue](../../issues) on GitHub.
>
> _Note: This section can be removed or modified if AI assistance was not used in your integration's development._

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by [@ruaan-deysel][user_profile]**

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/ruaan-deysel/ha-vault-backup.svg?style=for-the-badge
[commits]: https://github.com/ruaan-deysel/ha-vault-backup/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/ruaan-deysel/ha-vault-backup.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40ruaan-deysel-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/ruaan-deysel/ha-vault-backup.svg?style=for-the-badge
[releases]: https://github.com/ruaan-deysel/ha-vault-backup/releases
[user_profile]: https://github.com/ruaan-deysel

<!-- Optional badge definitions - uncomment if needed:
[buymecoffee]: https://www.buymeacoffee.com/ruaan-deysel
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
-->
