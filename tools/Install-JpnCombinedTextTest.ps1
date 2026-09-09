$ErrorActionPreference = 'Stop'

$v2Root = Split-Path -Parent $PSScriptRoot
$projectParent = Split-Path -Parent $v2Root
$legacyPayload = Join-Path $projectParent 'JPVoice_CNText_Experimental\build\text-only'
$gameRoot = 'D:\GAME\steamapps\common\MGS_PW'
$combinedRoot = Join-Path $v2Root 'build\test_1C79F2AD_fulltext'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupRoot = Join-Path $v2Root ("backups\steam-before-fulltext-test-$stamp")

$items = @(
    [PSCustomObject]@{
        Relative = 'mgspw\JPN\disc0_rel\002aba34.DAT'
        Source = Join-Path $combinedRoot 'mgspw\JPN\disc0_rel\002aba34.DAT'
    }
    [PSCustomObject]@{
        Relative = 'mgspw\JPN\disc0_rel\002aba34.KEY'
        Source = Join-Path $combinedRoot 'mgspw\JPN\disc0_rel\002aba34.KEY'
    }
    [PSCustomObject]@{
        Relative = 'mgspw\JPN\disc0_rel\009645fa.PDT'
        Source = Join-Path $legacyPayload 'mgspw\JPN\disc0_rel\009645fa.PDT'
    }
)

Get-ChildItem -LiteralPath (Join-Path $legacyPayload 'mgspw\JPN\Text') -Filter '*.olang' -File |
    Sort-Object Name |
    ForEach-Object {
        $items += [PSCustomObject]@{
            Relative = "mgspw\JPN\Text\$($_.Name)"
            Source = $_.FullName
        }
    }

foreach ($name in @('0007ccd8.xpr', '000ebbe8.xpr', '00c7c9f9.xpr')) {
    $items += [PSCustomObject]@{
        Relative = "mgspw\FONT\$name"
        Source = Join-Path $legacyPayload "mgspw\FONT\$name"
    }
}

if ($items.Count -ne 20) {
    throw "Expected 20 text payload files, got $($items.Count)"
}

foreach ($item in $items) {
    $target = Join-Path $gameRoot $item.Relative
    if (-not (Test-Path -LiteralPath $item.Source -PathType Leaf)) {
        throw "Missing source: $($item.Source)"
    }
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw "Missing Steam target: $target"
    }
}

foreach ($item in $items) {
    $target = Join-Path $gameRoot $item.Relative
    $backup = Join-Path $backupRoot $item.Relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
    Copy-Item -LiteralPath $target -Destination $backup
}

foreach ($item in $items) {
    $target = Join-Path $gameRoot $item.Relative
    Copy-Item -LiteralPath $item.Source -Destination $target -Force
}

$mismatches = @()
foreach ($item in $items) {
    $target = Join-Path $gameRoot $item.Relative
    $sourceHash = (Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if ($sourceHash -ne $targetHash) {
        $mismatches += $item.Relative
    }
}

[PSCustomObject]@{
    INSTALLED_FILES = $items.Count
    VERIFY_MISMATCHES = $mismatches.Count
    BACKUP_PATH = $backupRoot
    STEAM_ROOT = $gameRoot
} | ConvertTo-Json -Compress
