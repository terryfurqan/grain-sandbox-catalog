#!/usr/bin/env python3
"""
Helper Script: generate_cloud_env.py
Memformat credentials.json Google Service Account menjadi 1 baris string raw JSON
yang siap di-copy-paste ke Environment Variable Cloud Dashboard (Render.com, Railway, Fly.io, dsb).
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path

# Ensure UTF-8 output encoding on Windows terminals
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent

def parse_args():
    parser = argparse.ArgumentParser(
        description="Helper untuk memformat Google Service Account credentials.json menjadi 1 baris string Environment Variable."
    )
    parser.add_argument(
        "-f", "--file",
        default="credentials.json",
        help="Path ke file credentials service account JSON (default: credentials.json di root project)"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Hanya cetak string raw JSON satu baris tanpa dekorasi teks (cocok untuk piping/skrip)"
    )
    parser.add_argument(
        "--export-env",
        action="store_true",
        help="Simpan output ke file .env.cloud sebagai template siap pakai"
    )
    return parser.parse_args()


def copy_to_clipboard(text: str) -> bool:
    """Mencoba menyalin teks ke clipboard sistem operasi (Windows clip, macOS pbcopy, Linux xclip/wl-copy)."""
    try:
        if sys.platform == "win32":
            subprocess.run("clip", input=text, text=True, check=True, shell=True)
            return True
        elif sys.platform == "darwin":
            subprocess.run("pbcopy", input=text, text=True, check=True)
            return True
        elif sys.platform.startswith("linux"):
            for cmd in ["xclip -selection clipboard", "xsel --clipboard --input", "wl-copy"]:
                try:
                    subprocess.run(cmd.split(), input=text, text=True, check=True)
                    return True
                except FileNotFoundError:
                    continue
    except Exception:
        pass
    return False


def main():
    args = parse_args()
    
    file_path = Path(args.file)
    if not file_path.is_absolute():
        file_path = BASE_DIR / file_path

    if not file_path.exists():
        print(f"[-] ERROR: File credentials tidak ditemukan di: {file_path}", file=sys.stderr)
        print("    Pastikan Anda telah meletakkan 'credentials.json' hasil unduhan dari Google Cloud Console.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[-] ERROR: File '{file_path.name}' bukan format JSON yang valid: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[-] ERROR: Gagal membaca file '{file_path.name}': {e}", file=sys.stderr)
        sys.exit(1)

    # Validasi struktur Service Account
    if not isinstance(data, dict):
        print("[-] ERROR: Format JSON tidak valid (bukan JSON object).", file=sys.stderr)
        sys.exit(1)

    account_type = data.get("type", "")
    client_email = data.get("client_email", "")
    project_id = data.get("project_id", "")
    private_key = data.get("private_key", "")

    if account_type != "service_account":
        print(f"[-] PERINGATAN: field 'type' bernilai '{account_type}', bukan 'service_account'.", file=sys.stderr)
    
    if not client_email or not private_key:
        print("[-] ERROR: File credentials tidak memiliki field 'client_email' atau 'private_key'.", file=sys.stderr)
        sys.exit(1)

    # Minify JSON ke satu baris tanpa spasi berlebih
    compact_json = json.dumps(data, separators=(",", ":"))

    if args.raw:
        print(compact_json)
        return

    # Salin ke clipboard jika memungkinkan
    copied = copy_to_clipboard(compact_json)

    # Simpan ke .env.cloud jika diminta
    if args.export_env:
        env_cloud_path = BASE_DIR / ".env.cloud"
        with open(env_cloud_path, "w", encoding="utf-8") as f:
            f.write("# GRAIN Sandbox Cloud Environment Variables Template\n")
            f.write(f"GDRIVE_SERVICE_ACCOUNT_RAW_JSON='{compact_json}'\n")
            f.write("GDRIVE_ROOT_FOLDER_ID=\n")
            f.write("ADMIN_PIN=123456\n")
            f.write("PORTAL_TITLE=GRAIN Sandbox Experiment Data Server\n")
            f.write("PORTAL_SUBTITLE=Analog Geological & Tectonic Modeling Video/Photo Catalog\n")
        print(f"[+] Template tersimpan ke: {env_cloud_path.name}")

    print("=" * 80)
    print(" GRAIN Sandbox Data Catalog - Cloud Environment Variable Generator")
    print("=" * 80)
    print(f" Source File  : {file_path.name}")
    print(f" Project ID   : {project_id}")
    print(f" Client Email : {client_email}")
    print("-" * 80)
    print(" 📂 Langkah di Google Drive:")
    print(f" 1. Buka Google Drive, klik kanan folder eksperimen GRAIN Sandbox.")
    print(f" 2. Bagikan (Share) ke email di atas dengan role 'Viewer' (atau 'Editor').")
    print(f" 3. Salin Folder ID dari URL browser.")
    print("-" * 80)
    print(" 🤗 Langkah di HUGGING FACE SPACES (Settings -> Variables and secrets):")
    print(" Tambahkan di bagian SECRETS (New secret):")
    print("   • Key: GDRIVE_SERVICE_ACCOUNT_RAW_JSON")
    print(f"     Value: (String raw JSON yang telah disalin ke clipboard)")
    print("   • Key: ADMIN_PIN")
    print("     Value: 123456 (atau PIN admin pilihan Anda)")
    print()
    print(" Tambahkan di bagian VARIABLES (New variable):")
    print("   • Key: GDRIVE_ROOT_FOLDER_ID")
    print("     Value: (Folder ID Google Drive Anda)")
    print("   • Key: PORTAL_TITLE")
    print("     Value: GRAIN Sandbox Experiment Data Server")
    print("   • Key: PORTAL_SUBTITLE")
    print("     Value: Analog Geological & Tectonic Modeling Video/Photo Catalog")
    print("-" * 80)
    print(" 🚀 Langkah di RENDER.COM / RAILWAY:")
    print(" Tambahkan Environment Variable:")
    print("   • GDRIVE_SERVICE_ACCOUNT_RAW_JSON")
    print("   • GDRIVE_ROOT_FOLDER_ID")
    print("   • ADMIN_PIN")
    print()
    if copied:
        print(" [OK] JSON Kredensial telah OTOMATIS DISALIN ke clipboard Anda! Tinggal Ctrl+V.")
    else:
        print(" Salin string JSON lengkap di bawah ini:")
        print("-" * 80)
        print(compact_json)
        print("-" * 80)
    print("=" * 80)


if __name__ == "__main__":
    main()
