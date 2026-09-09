param(
    [string]$PackageRoot = '',
    [string]$GameRoot = 'D:\GAME\steamapps\common\MGS_PW',
    [string]$BackupRoot = ''
)

$ErrorActionPreference = 'Stop'

$v2Root = Split-Path -Parent $PSScriptRoot
if (-not $PackageRoot) {
    $PackageRoot = Join-Path $v2Root 'build\readiness\full_package'
}
if (-not $BackupRoot) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $BackupRoot = Join-Path $v2Root "backups\steam-before-ascii-ui-fix-$stamp"
}

$packageResolved = (Resolve-Path -LiteralPath $PackageRoot).Path
$gameResolved = (Resolve-Path -LiteralPath $GameRoot).Path
$files = Get-ChildItem -LiteralPath $packageResolved -Recurse -File | Sort-Object FullName
if ($files.Count -ne 20) {
    throw "Expected 20 package files, found $($files.Count)"
}

$items = foreach ($file in $files) {
    $relative = [System.IO.Path]::GetRelativePath($packageResolved, $file.FullName)
    if ($relative.StartsWith('..')) {
        throw "Package file escaped package root: $($file.FullName)"
    }
    $target = Join-Path $gameResolved $relative
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw "Missing Steam target: $target"
    }
    [PSCustomObject]@{
        Relative = $relative
        Source = $file.FullName
        Target = $target
        Backup = Join-Path $BackupRoot $relative
    }
}

foreach ($item in $items) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $item.Backup) -Force | Out-Null
    Copy-Item -LiteralPath $item.Target -Destination $item.Backup
}

foreach ($item in $items) {
    Copy-Item -LiteralPath $item.Source -Destination $item.Target -Force
}

$mismatches = @()
foreach ($item in $items) {
    $sourceHash = (Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash
    if ($sourceHash -ne $targetHash) {
        $mismatches += $item.Relative
    }
}

[PSCustomObject]@{
    INSTALLED_FILES = $items.Count
    VERIFY_MISMATCHES = $mismatches.Count
    BACKUP_PATH = (Resolve-Path -LiteralPath $BackupRoot).Path
    PACKAGE_ROOT = $packageResolved
    STEAM_ROOT = $gameResolved
} | ConvertTo-Json -Compress
