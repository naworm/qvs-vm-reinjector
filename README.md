# QVS VM Reinjector

**QVS VM Reinjector** is a full restoration toolkit for re-importing QNAP Virtualization Station VMs from filesystem backups, especially when `.QKVM` database has been lost.

This tool parses the XML of the VM `.meta` folder, then reinjects all relevant data directly into the QVS SQLite database (`qvs.db`).

## ✅ Features

- Restores `vms_vm` (UUID and full config)
  - `vm_template_overrides.json` avoids VM auto_start and helps you force some parameters in the config
- Reinjects `vms_disk` with image path + snapshot chain
- Restores `vms_adapter` with preserved MAC
- Injects `vms_graphic` VNC minimal config (not customizable for now)
- Injects snapshot as active disk path (latest snapshot)
  - Optional handling for "hot backup" with the flag `--after-boot` (previous snapshot)

## 💻 Requirements

- Python 3.7+
- `xmltodict` module
- Runs outside the NAS (Tested on WSL Debian, Python 3.11+)
- Access to:
  - The VM `.meta` folder (copied from backup)
  - The `qvs.db` file from your QNAP (exported via SCP/SFTP)

## 🚀 Usage

```bash
python3 inject_vm_full.py \
  --meta_folder /path/to/.uuid.meta \
  --db_path /path/to/qvs.db \
  [--after-boot]
```

> Use `--after-boot` if the VM was running or had been rebooted after the last snapshot (hot backup scenario).

⚠️ **Warning**: In this scenario, it may break the snapshot structure in Virtualization Station. The easy fix is:
- Obviously, make sure you are not testing on the last copy of your VM backup
- Ensure the VM is **shut down** or stays **powered off**
- Then, delete all associated snapshots from the **Virtualization Station GUI**

You may encounter this error once:

```
[Virtualization Station] Failed to delete snapshot "Snapshot_145706" for virtual machine "srvdocker". Error message: 'NoneType' object has no attribute 'children'
```

✅ To fix this:
- Manually delete the remaining `.xml` file inside the VM’s `snapshot/` directory (within the `.meta` folder)
- The snapshot structure should then be operational

## 🧠 Design philosophy

- Fully idempotent: re-running scripts doesn't create duplicates
- No destructive DELETEs: only `UPDATE` and smart `INSERT` operations
- Modular: one Python file per table for easier debugging and testing

## 🔒 Disclaimer

Ensure you keep a full, untouched backup of your system before proceeding, and retain it until all your data has been successfully recovered and a proper backup strategy is in place.

Use at your own risk. While this tool avoids destructive operations, it directly modifies the QNAP Virtualization Station database. Always make a backup of `qvs.db` before performing any injection.