#!/usr/bin/env python3

import os
import sqlite3
import xmltodict

def parse_vm_metadata(meta_folder):
    xml_file = next(f for f in os.listdir(meta_folder) if f.endswith(".xml"))
    xml_path = os.path.join(meta_folder, xml_file)
    with open(xml_path, "r", encoding="utf-8") as f:
        domain = xmltodict.parse(f.read())["domain"]

    uuid = domain["uuid"]
    qvs_vm = domain["metadata"]["qvs:vm"]
    hdds = qvs_vm.get("qvs:hdds", {}).get("qvs:hdd", [])
    if isinstance(hdds, dict):
        hdds = [hdds]

    device_disks = domain.get("devices", {}).get("disk", [])
    if isinstance(device_disks, dict):
        device_disks = [device_disks]

    libvirt_disks = {
        d.get("target", {}).get("@dev"): {
            "cache": d.get("driver", {}).get("@cache", "writeback"),
            "format": d.get("driver", {}).get("@type", "qcow2")
        }
        for d in device_disks
        if d.get("@type") == "file" and d.get("@device") == "disk"
    }

    return uuid, hdds, libvirt_disks

def inject_disks(uuid, hdds, libvirt_disks, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM vms_vm WHERE uuid = ?", (uuid,))
    vm_row = cursor.fetchone()
    if not vm_row:
        raise Exception(f"UUID {uuid} not found in vms_vm")
    vm_id = vm_row[0]

    for hdd in hdds:
        dev = hdd["@dev"]
        index = int(hdd["@index"])
        size = int(hdd["@size"])
        path = hdd["@root"]
        format_ = libvirt_disks.get(dev, {}).get("format", "qcow2")
        cache = libvirt_disks.get(dev, {}).get("cache", "writeback")
        bus = hdd["@bus"]

        # Vérifier si le disque existe déjà (par VM + dev)
        cursor.execute("SELECT id FROM vms_disk WHERE vm_id = ? AND dev = ?", (vm_id, dev))
        existing = cursor.fetchone()

        if existing:
            disk_id = existing[0]
            cursor.execute("""
                UPDATE vms_disk
                SET path = ?, root_path = ?, size = ?, format = ?, bus = ?, "index" = ?, cache = ?
                WHERE id = ?
            """, (path, path, size, format_, bus, index, cache, disk_id))
            print(f"🔁 Updated disk {dev} (VM {uuid})")
        else:
            cursor.execute("""
                INSERT INTO vms_disk (
                    path, root_path, size, format, bus, dev, boot_order, "index", vm_id, cache
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
            """, (path, path, size, format_, bus, dev, index, vm_id, cache))
            print(f"➕ Inserted disk {dev} (VM {uuid})")

    conn.commit()

def main():
    meta_folder = os.environ.get("META_FOLDER", "/mnt/f/Temp/migrate_meta_uuid/.4c95884d-1089-41c2-8663-fb6c47d6f4bb.meta")
    db_path = os.environ.get("DB_PATH", "/mnt/f/Temp/qvs.db")

    uuid, hdds, libvirt_disks = parse_vm_metadata(meta_folder)
    conn = sqlite3.connect(db_path)
    inject_disks(uuid, hdds, libvirt_disks, conn)
    conn.close()


if __name__ == "__main__":
    main()
