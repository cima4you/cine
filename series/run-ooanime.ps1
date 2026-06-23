param(
    [int]$StartIndex = 0,
    [int]$EndIndex = 0,
    [int]$Parallel = 5,
    [switch]$Update = $false
)

$ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SCRAPER = "$ROOT\screpte\ooanime\scrape_ooanime.py"
$CONVERT = "$ROOT\screpte\ooanime\convert_to_js.py"

Write-Host "========== OOAnime ==========" -ForegroundColor Cyan
if ($StartIndex -gt 0 -or $EndIndex -gt 0) {
    Write-Host "Series index: $StartIndex - $(if ($EndIndex -eq 0) { 'end' } else { $EndIndex })" -ForegroundColor Yellow
}
if ($Update) { Write-Host "Mode: UPDATE (seasons + episodes)" -ForegroundColor Magenta }

$fromArg = if ($StartIndex -gt 0) { "--from", $StartIndex } else { @() }
$toArg = if ($EndIndex -gt 0) { "--to", $EndIndex } else { @() }

if ($Update) {
    Write-Host "[1/3] Refreshing season lists (checking for new episodes)..." -ForegroundColor Yellow
    python -X utf8 $SCRAPER --seasons-only @fromArg @toArg --resume --parallel $Parallel
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }
}

Write-Host "[$(if ($Update) { '2' } else { '1' })/$(if ($Update) { '3' } else { '2' })] Fetching episode video URLs..." -ForegroundColor Yellow
python -X utf8 $SCRAPER --episodes-only @fromArg @toArg --resume --parallel $Parallel
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }

Write-Host "[$(if ($Update) { '3' } else { '2' })/$(if ($Update) { '3' } else { '2' })] Converting to JS..." -ForegroundColor Yellow
python -X utf8 $CONVERT
if ($LASTEXITCODE -ne 0) { Write-Host "Convert FAILED" -ForegroundColor Red; exit 1 }

Write-Host "`nDone! Now commit and push:" -ForegroundColor Green
Write-Host 'git add -A && git commit -m "تحديث OOAnime" && git push' -ForegroundColor White
