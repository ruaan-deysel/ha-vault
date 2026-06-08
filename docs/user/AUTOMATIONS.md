# Automation Ideas and Examples

This guide provides examples of automations you can create with the Vault integration to automate your backup workflows.

## Overview

The Vault integration exposes the following services for automation:

- **`vault.run_backup`** - Trigger an immediate backup of any Vault job
- **`vault.restore`** - Restore an item from a backup restore point
- **`vault.test_storage`** - Test connectivity to a storage destination

Use these services to create automations that fit your backup strategy and reduce manual intervention.

## Common Automation Scenarios

### 1. Backup Before Home Assistant Updates

Automatically create a VM snapshot before Home Assistant updates to safely test breaking changes.

```yaml
automation:
  - id: vault_backup_before_ha_update
    alias: Vault Backup Before Home Assistant Update
    description: "Take a VM snapshot before potentially breaking Home Assistant updates"
    
    trigger:
      - platform: state
        entity_id: update.home_assistant_core_update
        to: "on"  # Triggered when an update is available
    
    condition:
      # Limit to once per day to avoid snapshot spam
      - condition: template
        value_template: >
          {% set last_backup = state_attr('automation.vault_backup_before_ha_update', 'last_triggered') %}
          {{ last_backup is none or (now() - last_backup).total_seconds() > 86400 }}
    
    action:
      - service: vault.run_backup
        data:
          job_name: "HomeAssistant VM"  # Replace with your actual VM backup job name
```

**Configuration:**

- Replace `"HomeAssistant VM"` with the name of your VM backup job
- Adjust the cooldown duration (86400 seconds = 24 hours) as needed
- Alternatively, use `job_id: 1` if you prefer to reference by ID

### 2. Daily Automatic Backups

Run daily backups at a scheduled time to maintain recent restore points.

```yaml
automation:
  - id: vault_daily_backup
    alias: Daily Vault Backup
    description: "Run backup daily at 2 AM"
    
    trigger:
      - platform: time
        at: "02:00:00"
    
    action:
      - service: vault.run_backup
        data:
          job_name: "Daily Backup"
```

**Configuration:**

- Change `at: "02:00:00"` to your preferred time
- Use `condition` to skip weekends or specific days if desired

### 3. Backup on Critical Home Assistant Changes

Trigger backups when critical integrations or automations are modified.

```yaml
automation:
  - id: vault_backup_on_critical_update
    alias: Backup on Critical Home Assistant Update
    description: "Backup when critical addon/integration updates"
    
    trigger:
      - platform: state
        entity_id: 
          - update.z2m_update
          - update.esphome_update
          - update.nabu_casa_update
        to: "on"
    
    condition:
      - condition: template
        value_template: >
          {% set last_backup = state_attr('automation.vault_backup_on_critical_update', 'last_triggered') %}
          {{ last_backup is none or (now() - last_backup).total_seconds() > 43200 }}  # 12 hours
    
    action:
      - service: vault.run_backup
        data:
          job_id: 2  # Your important backup job
      - service: notify.notify
        data:
          message: "Vault backup triggered due to critical addon update"
```

**Configuration:**

- Add entity IDs for critical addons/integrations you want to protect
- Adjust cooldown duration as needed
- Optional: Add notification to alert you of the backup

### 4. Backup Before Storage Maintenance

Test storage connection and trigger backups before planned storage maintenance.

```yaml
automation:
  - id: vault_backup_before_storage_maintenance
    alias: Backup Before Storage Maintenance
    description: "Backup and test storage before planned maintenance"
    
    trigger:
      - platform: time
        at: "03:00:00"
    
    condition:
      - condition: template
        value_template: >
          {{ now().weekday() == 5 }}  # Only on Saturdays
    
    action:
      - service: vault.test_storage
        data:
          storage_id: 1
      
      - delay: "00:01:00"  # Wait for storage test to complete
      
      - service: vault.run_backup
        data:
          job_name: "Weekly Full Backup"
      
      - service: notify.notify
        data:
          message: "Weekly storage maintenance and backup completed"
```

**Configuration:**

- Adjust day of week (0 = Monday, 5 = Saturday, 6 = Sunday)
- Replace storage_id and job_name with your values

### 5. Low Storage Warning with Cleanup

Monitor storage capacity and trigger cleanup backups when space runs low.

```yaml
automation:
  - id: vault_low_storage_backup
    alias: Low Storage Cleanup Backup
    description: "Run retention cleanup when storage is low"
    
    trigger:
      - platform: numeric_state
        entity_id: sensor.vault_storage_available_percent
        below: 20  # Less than 20% free
        for:
          minutes: 10
    
    action:
      - service: notify.notify
        data:
          message: "⚠️ Vault storage is running low ({{ states('sensor.vault_storage_available_percent') }}% free)"
      
      - delay: "00:05:00"  # Give admin time to cancel if needed
      
      - service: vault.run_backup
        data:
          job_id: 3  # Cleanup job optimized for space
```

**Configuration:**

- Adjust storage threshold (20%) to match your risk tolerance
- Optional: Add condition to prevent running during backups
- Consider creating a cleanup-focused job in Vault for this purpose

## Snapshot Limiting Strategies

Since backups/snapshots consume storage, here are strategies to limit their frequency:

### Time-Based Cooldown (Recommended)

```yaml
condition:
  - condition: template
    value_template: >
      {% set last_backup = state_attr('automation.your_automation_name', 'last_triggered') %}
      {{ last_backup is none or (now() - last_backup).total_seconds() > 86400 }}  # 24 hours
```

### Day-of-Week Limiting

```yaml
condition:
  - condition: template
    value_template: >
      {{ now().weekday() in [4, 5, 6] }}  # Only Friday-Sunday
```

### Storage-Based Limiting

```yaml
condition:
  - condition: numeric_state
    entity_id: sensor.vault_storage_available_percent
    above: 25  # Only backup if >25% storage available
```

### Combination Approach

```yaml
condition:
  - condition: template
    value_template: >
      {% set last_backup = state_attr('automation.your_automation', 'last_triggered') %}
      {{ last_backup is none or (now() - last_backup).total_seconds() > 86400 }}
  
  - condition: numeric_state
    entity_id: sensor.vault_storage_available_percent
    above: 20
  
  - condition: template
    value_template: >
      {{ now().hour >= 1 and now().hour <= 5 }}  # Off-peak hours
```

## Best Practices

### 1. Use Descriptive Job Names

Keep backup jobs clearly named in Vault so automations are self-documenting:

- ✅ "HomeAssistant VM Daily"
- ❌ "backup_1"

### 2. Add Notifications

Notify yourself of backup outcomes:

```yaml
- service: notify.notify
  data:
    title: "Vault Backup"
    message: "{{ state_attr('sensor.vault_current_job_name', 'status') }}"
```

### 3. Monitor Job Status

Track backup health with sensors:

- `sensor.vault_current_job_name` - Currently running job
- `sensor.vault_runner_queue_length` - Jobs waiting to run
- `sensor.vault_storage_available_bytes` - Available storage

Create automations that trigger if jobs queue up or fail repeatedly.

### 4. Set Vault Retention Policies

The most effective way to manage snapshots is to configure retention in Vault itself:

- Set max snapshots per job
- Auto-delete snapshots older than X days
- Auto-delete when storage reaches threshold

This prevents automation from needing to manage cleanup logic.

### 5. Test Automations Safely

Before deploying:

1. Test with manual `vault.run_backup` service call
2. Start with notifications only (no actual backups)
3. Use the `condition` to temporarily disable the automation
4. Monitor logs for errors: `custom_components.vault: debug`

### 6. Offset Times for Multiple Backups

If running multiple backups, stagger them to avoid overwhelming your system:

```yaml
# Backup 1: 2:00 AM
# Backup 2: 2:30 AM
# Backup 3: 3:00 AM
```

## Debugging Automations

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.vault: debug
```

Then check `config/home-assistant.log` for Vault messages.

### Check Service Calls

View recent service calls:

1. Go to **Developer Tools** → **Events**
2. Filter for `call_service` events
3. Look for `vault.run_backup` calls to see parameters and results

### Monitor Sensor States

Check sensor values to debug issues:

```yaml

sensor.vault_current_job_name        # What's running
sensor.vault_runner_queue_length     # Jobs queued
sensor.vault_storage_available_bytes # Space available
```

## Examples Using Templates

### Conditional Backup Based on Multiple Conditions

```yaml
action:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ states('sensor.vault_runner_queue_length') | int(0) == 0 }}"
          - condition: numeric_state
            entity_id: sensor.vault_storage_available_percent
            above: 15
        sequence:
          - service: vault.run_backup
            data:
              job_name: "Backup when queue is clear and storage OK"
      
      - conditions:
          - condition: state
            entity_id: sensor.vault_runner_status
            state: "stopped"
        sequence:
          - service: notify.notify
            data:
              message: "⚠️ Vault runner is stopped, backup skipped"
```

## Adding Automations to Home Assistant

### Via YAML

1. Add the automation YAML to `config/automations.yaml`
2. Restart Home Assistant or reload automations:
   - Go to **Developer Tools** → **YAML** → **Automations**
   - Click **Reload automations**

### Via UI

1. Go to **Settings** → **Automations & Scenes** → **Automations**
2. Click **+ Create Automation**
3. Switch to **Edit in YAML** mode
4. Paste the automation YAML
5. Click **Save**

## Next Steps

- Review [Home Assistant Automation Documentation](https://www.home-assistant.io/docs/automation/) for advanced patterns
- Join the [Home Assistant Community Forum](https://community.home-assistant.io/) for automation help
- Check [Configuration Reference](CONFIGURATION.md) for all Vault service options
