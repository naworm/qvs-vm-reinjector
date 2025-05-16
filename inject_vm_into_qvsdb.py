#!/usr/bin/env python3

import os
import xmltodict
import sqlite3
import json
from datetime import datetime

def load_overrides(template_path):
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def inject_vm_into_qvsdb(meta_folder, db_path, template_path):
    # Charger overrides
    overrides = load_overrides(template_path)
    xml_file = next((f for f in os.listdir(meta_folder) if f.endswith('.xml')), None)
    if not xml_file:
        raise FileNotFoundError("No .xml file found in meta folder.")

    xml_path = os.path.join(meta_folder, xml_file)
    with open(xml_path, 'r', encoding='utf-8') as f:
        domain = xmltodict.parse(f.read())['domain']

    uuid = domain.get('uuid')
    libvirt_name = uuid

    memory_kib = int(domain['memory']['#text'])
    memory_bytes = memory_kib * 1024

    vcpu = int(domain['vcpu']['#text']) if isinstance(domain['vcpu'], dict) else int(domain['vcpu'])
    qvs_vm = domain.get('metadata', {}).get('qvs:vm', {})
    os_type = qvs_vm.get('qvs:os', {}).get('@type', 'linux')
    machine = domain.get('os', {}).get('type', {}).get('@machine', 'pc')

    # Données issues du XML
    name = qvs_vm.get('qvs:name', libvirt_name)
    meta_path = qvs_vm.get('qvs:meta_path', meta_folder)
    keymap = qvs_vm.get('qvs:graphics', {}).get('qvs:graphics', {}).get('@keymap', 'en-us')
    description = qvs_vm.get('qvs:description', '')
    snapshot_type = qvs_vm.get('qvs:snapshot', {}).get('@type', 'none')
    host_cpu = qvs_vm.get('qvs:host_cpu', libvirt_name)
    nas_model = qvs_vm.get('qvs:nas_model', libvirt_name)
    auto_start_delay = int(qvs_vm.get('qvs:auto_start_delay', {}).get('#text', 0))
    usb = "enable" if qvs_vm.get('qvs:usbs') else "disable"
    qvm = 1 if qvs_vm.get('qvs:qvm', {}).get('@enable', 'no') == 'yes' else 0
    test = 1 if qvs_vm.get('qvs:test', {}).get('@enable', 'no') == 'yes' else 0
    ballooning_rsvd = int(qvs_vm.get('qvs:mom', {}).get('@reserved_memory', 0))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    # Champs communs
    fields = {
        "libvirt_name": libvirt_name,
        "name": name,
        "cores": vcpu,
        "memory": memory_bytes,
        "os_type": os_type,
        "description": description,
        "meta_path": meta_path,
        "boot_menu": 0,
        "boot_order": "cd",
        "keymap": keymap,
        "cpu_model": "host",
        "machine": machine,
        "bios": "bios",
        "video_type": "vga",
        "auto_start": "disable",
        "auto_start_state": "",
        "auto_start_delay": auto_start_delay,
        "usb": usb,
        "sound": "",
        "qvm": qvm,
        "test": test,
        "rollback": None,
        "snapshot_type": snapshot_type,
        "host_cpu": host_cpu,
        "nas_model": nas_model,
        "auto_start_detach_device": 1,
        "channel_switch": json.dumps({"previous": True, "current": True}),
        "hide_kvm_sign": 0,
        "arch": "x86",
        "source": "import",
        "ballooning": 0,
        "ballooning_rsvd": ballooning_rsvd,
        "hot_plug_cpu": 0,
        "memory_sharing": 0,
        "cpuset_policy_id": 0,
        "running_before_upgrade": 0,
        "create_time": now,
        "last_bootup_time": None,
        "last_shutdown_time": None,
        "last_suspend_time": None,
        "tpm_model": None,
    }

    # Appliquer le template JSON s'il existe pour cet os_type
    overrides_by_os = overrides.get("vms_vm", {}).get(os_type, {})
    for key, val in overrides_by_os.items():
        fields[key] = val

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM vms_vm WHERE uuid = ?", (uuid,))
    exists = cursor.fetchone()[0] > 0

    if exists:
        set_clause = ', '.join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [uuid]
        cursor.execute(f"UPDATE vms_vm SET {set_clause} WHERE uuid = ?", values)
        print(f"✅ Updated VM {uuid} ({name})")
    else:
        columns = ', '.join(['uuid'] + list(fields.keys()))
        placeholders = ', '.join(['?'] * (1 + len(fields)))
        values = [uuid] + list(fields.values())
        cursor.execute(f"INSERT INTO vms_vm ({columns}) VALUES ({placeholders})", values)
        print(f"✅ Inserted VM {uuid} ({name})")

    conn.commit()
    conn.close()

def main():
    meta_folder = os.environ.get("META_FOLDER", "/mnt/f/Temp/migrate_meta_uuid/.4c95884d-1089-41c2-8663-fb6c47d6f4bb.meta")
    db_path = os.environ.get("DB_PATH", "/mnt/f/Temp/qvs.db")
    template_path = "vm_template_overrides.json"
    inject_vm_into_qvsdb(meta_folder, db_path, template_path)



if __name__ == "__main__":
    main()
