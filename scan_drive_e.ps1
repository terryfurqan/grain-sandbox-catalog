# Comprehensive scan of Drive E:

function Get-FolderStats {
    param([string]$Path)
    $output = robocopy "$Path" "C:\NULL_TARGET_NONEXIST" /L /S /NJH /BYTES /NP /R:0 /W:0 /XJ 2>&1
    $bytes = [int64]0
    $files = [int64]0
    $dirs = [int64]0
    foreach ($line in $output) {
        if ($line -match "^\s*Files\s*:\s*(\d+)") {
            $files = [int64]$matches[1]
        }
        if ($line -match "^\s*Bytes\s*:\s*(\d+)") {
            $bytes = [int64]$matches[1]
        }
        if ($line -match "^\s*Dirs\s*:\s*(\d+)") {
            $dirs = [int64]$matches[1]
        }
    }
    return [PSCustomObject]@{
        Path = $Path
        Name = (Split-Path $Path -Leaf)
        SizeBytes = $bytes
        SizeMB = [math]::Round($bytes / 1MB, 2)
        SizeGB = [math]::Round($bytes / 1GB, 3)
        SizeTB = [math]::Round($bytes / 1TB, 3)
        FileCount = $files
        DirCount = $dirs
    }
}

Write-Host "==============================================================="
Write-Host "1. DRIVE E: ROOT FILES (INCLUDING HIDDEN & SYSTEM)"
Write-Host "==============================================================="
$rootFiles = Get-ChildItem -Path "E:\" -Force | Where-Object { -not $_.PSIsContainer }
$rootFiles | Select-Object Name, Length, @{N="SizeMB";E={[math]::Round($_.Length/1MB,2)}}, @{N="SizeGB";E={[math]::Round($_.Length/1GB,3)}}, Attributes, LastWriteTime | Format-Table -AutoSize

Write-Host "==============================================================="
Write-Host "2. DRIVE E: ROOT FOLDERS OVERVIEW"
Write-Host "==============================================================="
$rootFolders = Get-ChildItem -Path "E:\" -Force | Where-Object { $_.PSIsContainer }
$rootStats = foreach ($f in $rootFolders) {
    Write-Host "Scanning $($f.FullName)..."
    Get-FolderStats -Path $f.FullName
}
$rootStats | Format-Table Name, SizeGB, SizeTB, FileCount, DirCount -AutoSize

Write-Host "==============================================================="
Write-Host "3. SUBFOLDER BREAKDOWN (LEVEL 1 & LEVEL 2)"
Write-Host "==============================================================="
foreach ($rf in $rootFolders) {
    if ($rf.Name -in @('$RECYCLE.BIN', 'System Volume Information')) { continue }
    Write-Host "`n--- Breakdown for Folder: $($rf.Name) ---"
    $sub1 = Get-ChildItem -Path $rf.FullName -Force -ErrorAction SilentlyContinue | Where-Object { $_.PSIsContainer }
    $sub1Stats = foreach ($s in $sub1) {
        Get-FolderStats -Path $s.FullName
    }
    $sub1Stats | Sort-Object -Property SizeBytes -Descending | Format-Table Name, SizeGB, FileCount, DirCount -AutoSize
}
