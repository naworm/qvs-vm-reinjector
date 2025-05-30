#!/usr/bin/env python3

import argparse
import subprocess
import os

def run_script(script_path, meta_folder, db_path, before_boot=False):
    env = os.environ.copy()
    env["META_FOLDER"] = meta_folder
    env["DB_PATH"] = db_path
    if before_boot:
        env["BEFORE_BOOT"] = "1"
    result = subprocess.run(["python3", script_path], env=env)
    if result.returncode != 0:
        print(f"❌ Error while running {script_path}")
        exit(1)

def main():
    parser = argparse.ArgumentParser(description="Inject full VM into QVS DB")
    parser.add_argument("--meta_folder", help="Path to the .meta folder")
    parser.add_argument("--db_path", help="Path to the qvs.db SQLite database")
    parser.add_argument("--before-boot", action="store_true", help="Use first backingStore instead of active path if VM was booted after last snapshot or backup was hot")
    args = parser.parse_args()

    meta_folder = args.meta_folder or input("🗂️  Path to meta_folder: ").strip()
    db_path = args.db_path or input("🗃️  Path to qvs.db: ").strip()

    print(f"\n📦 Injecting VM from:\n- Meta folder: {meta_folder}\n- DB path: {db_path}\n")

    base_dir = os.path.dirname(os.path.realpath(__file__))

    steps = [
        "inject_vm_into_qvsdb.py",
        "inject_vm_disks.py",
        "inject_vm_nics.py",
        "inject_vm_snapshots.py"
    ]

    for step in steps:
        script_path = os.path.join(base_dir, step)
        print(f"🚀 Running {step}...")
        run_script(script_path, meta_folder, db_path, before_boot=args.before_boot)

    print("✅ All steps completed successfully. Please consider creating backup plans in Virtualization Station.")

if __name__ == "__main__":
    main()
