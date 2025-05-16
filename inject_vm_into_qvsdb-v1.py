import sqlite3
import uuid
import os
from xml.etree import ElementTree as ET

def inject_vm_into_qvsdb(db_path, meta_folder, disk_filename, vm_name=None):
    xml_file = [f for f in os.listdir(meta_folder) if f.endswith(".xml")][0]
    xml_path = os.path.join(meta_folder, xml_file)
    tree = ET.parse(xml_path)
    root = tree.getroot()

    vm_uuid = os.path.splitext(xml_file)[0]
    vm_name = vm_name or vm_uuid
    memory_kib = int(root.findtext("memory", default="262144"))
    memory_bytes = memory_kib * 1024
    disk_path = f"/share/VMs/{vm_name}/{disk_filename}"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(id) FROM vms_vm")
    max_vm_id = cursor.fetchone()[0] or 0
    new_vm_id = max_vm_id + 1

    cursor.execute("""
    INSERT INTO vms_vm (
      id, uuid, libvirt_name, name, cores, memory, os_type, meta_path,
      boot_menu, boot_order, keymap, cpu_model, machine, bios, video_type,
      auto_start, auto_start_state, auto_start_delay, usb, qvm, test,
      snapshot_type, host_cpu, nas_model, auto_start_detach_device,
      channel_switch, hide_kvm_sign, arch, source, ballooning, ballooning_rsvd,
      hot_plug_cpu, memory_sharing, cpuset_policy_id, running_before_upgrade
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        new_vm_id, vm_uuid, vm_uuid, vm_name, 2, memory_bytes, "debian910",
        f"/share/VMs/{vm_name}/.{vm_uuid}.meta", 0, '', 'fr', '', '', '', '',
        'false', '', 0, 'ehci', 1, 0, '', '', '', 0, '', 0, 'x86', '', 0, 0,
        0, 0, 0, 0
    ))

    cursor.execute("""
    INSERT INTO vms_disk (
      path, root_path, size, format, bus, dev, boot_order, "index", vm_id, cache
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        disk_path, disk_path, 2147483648, 'qcow2', 'virtio', '', None, 0,
        new_vm_id, 'none'
    ))

    conn.commit()
    conn.close()
    print(f"✅ VM '{vm_name}' injected with UUID {vm_uuid} (ID {new_vm_id})")

# Exemple d'utilisation :
inject_vm_into_qvsdb("/mnt/f/Temp/qvs.db", "/mnt/f/Temp/migrate_meta_uuid/.4c95884d-1089-41c2-8663-fb6c47d6f4bb.meta/", "srvdocker_00.img", "srvdocker")
