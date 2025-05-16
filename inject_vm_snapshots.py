#!/usr/bin/env python3

import os
import sqlite3
import xmltodict

def parse_snapshot_paths(domain, use_backingstore):
    disks = domain.get("devices", {}).get("disk", [])
    if isinstance(disks, dict):
        disks = [disks]

    snapshot_info = {}
    for d in disks:
        if d.get("@device") != "disk":
            continue

        dev = d.get("target", {}).get("@dev")
        active_path = d.get("source", {}).get("@file")
        backing = d.get("backingStore", {})

        # Collect full chain
        full_chain = [active_path] if active_path else []
        while backing:
            src = backing.get("source", {}).get("@file")
            if src:
                full_chain.append(src)
            backing = backing.get("backingStore")

        # By default we use the active file
        path = active_path
        if use_backingstore and len(full_chain) >= 2:
            path = full_chain[1]  # first backingStore

        root_path = full_chain[-1] if full_chain else active_path
        snapshot_info[dev] = {
            "path": path,
            "root_path": root_path
        }

    return snapshot_info

def inject_snapshots(domain, uuid, db_path, use_backingstore):
    vm_name = domain.get("metadata", {}).get("qvs:vm", {}).get("qvs:name", uuid)
    snapshot_map = parse_snapshot_paths(domain, use_backingstore)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM vms_vm WHERE uuid = ?", (uuid,))
    vm_row = cursor.fetchone()
    if not vm_row:
        raise Exception(f"UUID {uuid} not found in vms_vm")
    vm_id = vm_row[0]

    for dev, paths in snapshot_map.items():
        cursor.execute("SELECT id FROM vms_disk WHERE vm_id = ? AND dev = ?", (vm_id, dev))
        row = cursor.fetchone()
        if row:
            disk_id = row[0]
            cursor.execute("""
                UPDATE vms_disk
                SET path = ?, root_path = ?
                WHERE id = ?
            """, (paths["path"], paths["root_path"], disk_id))
            print(f"🔄 Updated disk {dev}: path={paths['path']} root={paths['root_path']}")
        else:
            print(f"⚠️ Disk {dev} not found for VM {uuid}")

    conn.commit()
    conn.close()

def main():
    meta_folder = os.environ.get("META_FOLDER", "/mnt/f/Temp/migrate_meta_uuid/.4c95884d-1089-41c2-8663-fb6c47d6f4bb.meta")
    db_path = os.environ.get("DB_PATH", "/mnt/f/Temp/qvs.db")

    xml_file = next(f for f in os.listdir(meta_folder) if f.endswith(".xml"))
    xml_path = os.path.join(meta_folder, xml_file)
    with open(xml_path, "r", encoding="utf-8") as f:
        domain = xmltodict.parse(f.read())["domain"]

    uuid = domain.get("uuid", os.path.basename(xml_file).replace(".xml", ""))
    vm_name = domain.get("metadata", {}).get("qvs:vm", {}).get("qvs:name", uuid)

    flag = os.environ.get("AFTER_BOOT")
    if flag is None:
        resp = input(f"🧠 Has the VM '{vm_name}' been booted at least once since the last snapshot was taken OR was the backup made while the VM was running? (default is no but safer answer is yes) [y/N] ").strip().lower()
        use_backingstore = resp == "y"
    else:
        use_backingstore = flag.lower() in ("1", "true", "yes", "y")
    if use_backingstore:
        print(f'Please check Usage section in the README before booting up the VM: {vm_name}')

    inject_snapshots(domain, uuid, db_path, use_backingstore)

if __name__ == "__main__":
    main()
