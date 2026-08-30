#!/usr/bin/env python3
"""
Launcher Publik Server GRAIN dengan Cloudflare Tunnel
====================================================
Menjalankan Web Server FastAPI (Uvicorn) di background dan menghubungkannya
ke Cloudflare Quick Tunnel untuk menghasilkan URL publik HTTPS instan (gratis & aman).
"""

import os
import sys
import time
import re
import signal
import subprocess
import threading
import urllib.request
from pathlib import Path

# Ensure UTF-8 output
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
CLOUDFLARED_PATHS = [
    r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
    r"C:\Program Files\cloudflared\cloudflared.exe",
    "cloudflared",
]

def find_cloudflared() -> str:
    for p in CLOUDFLARED_PATHS:
        if os.path.exists(p):
            return p
    # Fallback to PATH search
    try:
        res = subprocess.run(["where.exe", "cloudflared"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return "cloudflared"

def copy_to_clipboard(text: str):
    try:
        if sys.platform == "win32":
            subprocess.run("clip", input=text, text=True, check=True, shell=True)
            return True
    except Exception:
        pass
    return False

def get_lan_ip() -> str:
    try:
        cmd = 'powershell -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias \'Wi-Fi*\',\'Ethernet*\' -ErrorAction SilentlyContinue | Where-Object {$_.IPAddress -notlike \'127.*\' -and $_.IPAddress -notlike \'169.254.*\'} | Select-Object -ExpandProperty IPAddress -First 1"'
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        ip = res.stdout.strip()
        if ip:
            return ip
    except Exception:
        pass
    return "127.0.0.1"

def main():
    port = 8080
    host = "0.0.0.0"
    cloudflared_bin = find_cloudflared()

    print("=" * 80)
    print(" 🏔️  GRAIN SANDBOX EXPERIMENT DATA SERVER - PUBLIC CLOUDFLARE TUNNEL")
    print("=" * 80)
    print(f" [*] Direktori Kerja : {BASE_DIR}")
    print(f" [*] Cloudflared Bin  : {cloudflared_bin}")
    print(f" [*] Port Lokal       : {port}")
    print("=" * 80)

    # 1. Start Uvicorn Server Subprocess
    print("\n[1/3] Menjalankan Server FastAPI Uvicorn (Port 8080)...")
    uvicorn_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port)]
    uvicorn_proc = subprocess.Popen(
        uvicorn_cmd,
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    def log_uvicorn():
        for line in iter(uvicorn_proc.stdout.readline, ""):
            if "error" in line.lower() or "exception" in line.lower():
                print(f"[Uvicorn Error] {line.strip()}", file=sys.stderr)

    threading.Thread(target=log_uvicorn, daemon=True).start()

    # Wait for Uvicorn to be ready
    print("      Menunggu inisialisasi server lokal...")
    time.sleep(2)

    # 2. Start Cloudflare Tunnel Subprocess
    print("\n[2/3] Membuka Terowongan Cloudflare Quick Tunnel (HTTPS)...")
    cf_cmd = [cloudflared_bin, "tunnel", "--url", f"http://localhost:{port}"]
    cf_proc = subprocess.Popen(
        cf_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    public_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    # Read cloudflared output to grab the tunnel URL
    start_time = time.time()
    while time.time() - start_time < 20:
        line = cf_proc.stdout.readline()
        if not line:
            if cf_proc.poll() is not None:
                break
            time.sleep(0.1)
            continue
        
        match = url_pattern.search(line)
        if match:
            public_url = match.group(0)
            break

    if not public_url:
        print("[-] Gagal mendeteksi URL Cloudflare Tunnel otomatis dalam 20 detik.")
        print("    Memeriksa log cloudflared:")
        print("    Pastikan koneksi internet aktif dan cloudflared diizinkan di Windows Firewall.")
    else:
        lan_ip = get_lan_ip()
        copied = copy_to_clipboard(public_url)

        print("\n" + "=" * 80)
        print(" 🎉 SERVER GRAIN BERHASIL TERHUBUNG KE INTERNET SECARA PUBLIK!")
        print("=" * 80)
        print(f" 🌐 URL Publik (HTTPS) : {public_url}")
        print(f" ⚙️ Admin & Setup Panel : {public_url}/setup")
        print(f" 🏠 URL Lokal PC       : http://localhost:{port}")
        print(f" 📶 URL Jaringan LAN   : http://{lan_ip}:{port}")
        print("-" * 80)
        if copied:
            print(" [OK] URL Publik telah OTOMATIS DISALIN ke clipboard Anda!")
        print(" Siapa saja dapat membuka URL di atas tanpa perlu login akun Cloudflare.")
        print("=" * 80)
        print(" Tekan [Ctrl + C] untuk menutup server dan terowongan publik.")
        print("=" * 80 + "\n")

        # Open in browser
        try:
            os.startfile(public_url)
        except Exception:
            pass

    try:
        # Keep running and streaming logs if any
        while True:
            time.sleep(1)
            if uvicorn_proc.poll() is not None or cf_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\n[*] Menghentikan server dan terowongan Cloudflare...")
    finally:
        try:
            uvicorn_proc.terminate()
            cf_proc.terminate()
        except Exception:
            pass
        print("[+] Server berhasil dihentikan. Sampai jumpa!")

if __name__ == "__main__":
    main()
