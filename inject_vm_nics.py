#!/usr/bin/env python3

import os
import sqlite3
import xmltodict
import secrets

def generate_hex_token():
    return secrets.token_hex(16)

def parse_vm_metadata(meta_folder):
    xml_file = next(f for f in os.listdir(meta_folder) if f.endswith(".xml"))
    xml_path = os.path.join(meta_folder, xml_file)
    with open(xml_path, "r", encoding="utf-8") as f:
        domain = xmltodict.parse(f.read())["domain"]

    uuid = domain["uuid"]
    qvs_vm = domain["metadata"]["qvs:vm"]
    nics = qvs_vm.get("qvs:nics", {}).get("qvs:nic", [])
    if isinstance(nics, dict):
        nics = [nics]

    return uuid, nics

def inject_graphic_console(uuid, conn):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM vms_vm WHERE uuid = ?", (uuid,))
    row = cursor.fetchone()
    if not row:
        raise Exception(f"UUID {uuid} not found in vms_vm")
    vm_id = row[0]

    cursor.execute("SELECT COUNT(*) FROM vms_graphic WHERE vm_id = ?", (vm_id,))
    exists = cursor.fetchone()[0]

    if not exists:
        cursor.execute("""
            INSERT INTO vms_graphic (
                auto_port, _port, enable_password, password, vm_id, localhost_only, type
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (1, None, 0, None, vm_id, 1, "vnc"))
        print(f"✅ Inserted VNC console for VM {uuid}")
    else:
        print(f"ℹ️ VNC console already exists for VM {uuid}")

def inject_nics(uuid, nics, conn):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM vms_vm WHERE uuid = ?", (uuid,))
    vm_row = cursor.fetchone()
    if not vm_row:
        raise Exception(f"UUID {uuid} not found in vms_vm")
    vm_id = vm_row[0]

    for nic in nics:
        mac = nic["@mac"]

        cursor.execute("SELECT id, port_id FROM vms_adapter WHERE vm_id = ? AND mac = ?", (vm_id, mac))
        existing = cursor.fetchone()

        if existing:
            adapter_id, port_id = existing
            cursor.execute("""
                UPDATE vms_adapter
                SET bridge = ?, model = ?, "index" = ?, queues = ?, type = ?
                WHERE id = ?
            """, (
                nic.get("@bridge", "br0"),
                nic["@model"],
                int(nic["@index"]),
                int(nic.get("@queues", "1")),
                nic["@type"],
                adapter_id
            ))
            print(f"🔁 Updated NIC {mac} (port_id={port_id})")
        else:
            port_id = generate_hex_token()
            cursor.execute("""
                INSERT INTO vms_adapter (
                    mac, bridge, model, "index", vm_id, port_id, queues, type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mac,
                nic.get("@bridge", "br0"),
                nic["@model"],
                int(nic["@index"]),
                vm_id,
                port_id,
                int(nic.get("@queues", "1")),
                nic["@type"]
            ))
            print(f"➕ Inserted NIC {mac} (port_id={port_id})")

    conn.commit()

def main():
    meta_folder = os.environ.get("META_FOLDER", "/mnt/f/Temp/migrate_meta_uuid/.4c95884d-1089-41c2-8663-fb6c47d6f4bb.meta")
    db_path = os.environ.get("DB_PATH", "/mnt/f/Temp/qvs.db")

    uuid, nics = parse_vm_metadata(meta_folder)
    conn = sqlite3.connect(db_path)

    inject_graphic_console(uuid, conn)
    inject_nics(uuid, nics, conn)

    conn.close()



if __name__ == "__main__":
    main()
