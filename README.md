# QVS VM Reinjector

**QVS VM Reinjector** is a full restoration toolkit for re-importing Virtualization Station VMs (QNAP) from filesystem backups, especially when `.QKVM` metadata has been lost or QVS has been reset.

This tool parses the original `.meta` folder (XMLs and snapshots), then reinjects all relevant data directly into the QVS `qvs.db` SQLite database.

## ✅ Features

- Restores `vms_vm` (UUID, config, template)
- Reconstructs `vms_disk` from libvirt + snapshot chain
- Restores `vms_adapter` with preserved MAC/port_id
- Injects VNC graphics config if needed
- Detects snapshots and corrects snapshot root/active
- Optional handling for "hot backup" with `--after-boot`

## 💻 Requirements

- Python 3.7+
- `xmltodict` module
- Runs outside the NAS (Linux or Windows WSL)
- Access to:
  - The VM `.meta` folder (extracted from backup)
  - The `qvs.db` file from your QNAP (exported via SCP/SFTP)

## 🚀 Usage

```bash
python3 inject_vm_full.py \
  --meta_folder /path/to/.uuid.meta \
  --db_path /path/to/qvs.db \
  [--after-boot]
```

⚠️ Warning: Using this option may break the snapshot structure in Virtualization Station. To avoid issues: 
- Make sure the VM is shut down or remains powered off
- Then, delete all associated snapshots from the Virtualization Station GUI

An error may appear once:
```
[Virtualization Station] Failed to delete snapshot "Snapshot_145706" for virtual machine "srvdocker". Error message: 'NoneType' object has no attribute 'children'
```
To resolve this, manually delete the remaining .xml file inside the VM's `snapshot/` directory (within the .meta folder), then the snapshot structure should be fixed.


> Use `--after-boot` if the VM was running or rebooted after the last snapshot (hot backup scenario).

If you use the option its higly probable that the snapshot structure become broken. So the p
shutdown vm or keep it off, delete all snapshots from VS
an error may appear :
Error	2025-05-16	15:54:20	---	---	localhost	---	Virtualization Station	Snapshots	[Virtualization Station] Failed to delete snapshot "Snapshot_145706" for virtual machine "srvdocker". Error message: 'NoneType' object has no attribute 'children'

delete the probable unique xml file remaining in snapshot folder, fix.



## 🧠 Design philosophy

- Fully idempotent: re-running scripts doesn't create duplicates
- No destructive DELETEs: only `UPDATE` and smart `INSERT` operations
- Modular: one Python file per table for easier debugging and testing


## 🔒 Disclaimer

Ensure you keep a full, untouched backup of your system before proceeding, and retain it until all your data has been successfully recovered and a proper backup strategy is in place.

Use at your own risk. While this tool avoids destructive operations, it directly modifies the QNAP Virtualization Station database. Always make a backup of `qvs.db` before performing any injection.


