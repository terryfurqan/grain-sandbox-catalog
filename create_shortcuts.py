"""
Helper Script: create_shortcuts.py
Membuat shortcut Windows di Start Menu dan Desktop agar server GRAIN
bisa dipanggil dengan cepat hanya dengan mengetik 'GRAIN' di Start Menu Windows.
"""

import os
import sys
from pathlib import Path

def create_shortcut_powershell():
    base_dir = Path(__file__).resolve().parent
    public_bat = base_dir / "run_public_server.bat"
    local_bat = base_dir / "run_server.bat"

    # Start Menu Programs & Desktop paths
    appdata = os.environ.get("APPDATA", "")
    userprofile = os.environ.get("USERPROFILE", "")
    
    start_menu = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    desktop = Path(userprofile) / "Desktop"

    start_menu.mkdir(parents=True, exist_ok=True)
    desktop.mkdir(parents=True, exist_ok=True)

    ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell

# 1. Start Menu: GRAIN Sandbox Server (Public Tunnel)
$lnk1 = Join-Path "{start_menu}" "GRAIN Sandbox Server (Public Tunnel).lnk"
$sc1 = $WshShell.CreateShortcut($lnk1)
$sc1.TargetPath = "{public_bat}"
$sc1.WorkingDirectory = "{base_dir}"
$sc1.Description = "Jalankan GRAIN Sandbox Data Server dengan Cloudflare Public HTTPS Tunnel"
$sc1.IconLocation = "shell32.dll,13"
$sc1.Save()

# 2. Desktop: GRAIN Sandbox Server (Public Tunnel)
$deskLnk1 = Join-Path "{desktop}" "GRAIN Sandbox Server (Public Tunnel).lnk"
$deskSc1 = $WshShell.CreateShortcut($deskLnk1)
$deskSc1.TargetPath = "{public_bat}"
$deskSc1.WorkingDirectory = "{base_dir}"
$deskSc1.Description = "Jalankan GRAIN Sandbox Data Server dengan Cloudflare Public HTTPS Tunnel"
$deskSc1.IconLocation = "shell32.dll,13"
$deskSc1.Save()

# 3. Start Menu: GRAIN Sandbox Server (Localhost)
$lnk2 = Join-Path "{start_menu}" "GRAIN Sandbox Server (Local).lnk"
$sc2 = $WshShell.CreateShortcut($lnk2)
$sc2.TargetPath = "{local_bat}"
$sc2.WorkingDirectory = "{base_dir}"
$sc2.Description = "Jalankan GRAIN Sandbox Data Server di Localhost"
$sc2.IconLocation = "shell32.dll,14"
$sc2.Save()

# 4. Shortcut singkat 'GRAIN Server' di Start Menu untuk pencarian super cepat
$lnk3 = Join-Path "{start_menu}" "GRAIN Server.lnk"
$sc3 = $WshShell.CreateShortcut($lnk3)
$sc3.TargetPath = "{public_bat}"
$sc3.WorkingDirectory = "{base_dir}"
$sc3.Description = "Jalankan GRAIN Sandbox Data Server"
$sc3.IconLocation = "shell32.dll,13"
$sc3.Save()

Write-Output "Shortcuts created successfully."
"""

    ps_file = base_dir / "_make_shortcuts.ps1"
    with open(ps_file, "w", encoding="utf-8") as f:
        f.write(ps_script)

    import subprocess
    res = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_file)], capture_output=True, text=True)
    if ps_file.exists():
        ps_file.unlink()

    print(res.stdout)
    if res.stderr:
        print("Stderr:", res.stderr)

    print("=" * 70)
    print("[SUKSES] Shortcut Windows berhasil dipasang!")
    print(f"1. Start Menu : {start_menu / 'GRAIN Server.lnk'}")
    print(f"2. Start Menu : {start_menu / 'GRAIN Sandbox Server (Public Tunnel).lnk'}")
    print(f"3. Desktop    : {desktop / 'GRAIN Sandbox Server (Public Tunnel).lnk'}")
    print("=" * 70)

if __name__ == "__main__":
    create_shortcut_powershell()
