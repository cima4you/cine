param(
    [int]$StartPage = 1,
    [int]$EndPage = 999,
    [int]$Parallel = 10
)

$ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SCRAPER = "$ROOT\screpte\cimafre\scrape_cimafre.py"
$CONVERT = "$ROOT\screpte\cimafre\convert_to_js.py"

Write-Host "========== Cimafre ==========" -ForegroundColor Cyan
Write-Host "Pages: $StartPage - $EndPage" -ForegroundColor Yellow

Write-Host "[1/3] Scraping movie list..." -ForegroundColor Yellow
python -X utf8 $SCRAPER --from $StartPage --to $EndPage
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }

Write-Host "[2/3] Fetching servers..." -ForegroundColor Yellow
python -X utf8 $SCRAPER --servers --parallel $Parallel
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }

Write-Host "[3/3] Converting to JS..." -ForegroundColor Yellow
python -X utf8 $CONVERT
if ($LASTEXITCODE -ne 0) { Write-Host "Convert FAILED" -ForegroundColor Red; exit 1 }

Write-Host "`nDone! Now commit and push:" -ForegroundColor Green
Write-Host "git add -A && git commit -m `"تحديث Cimafre`" && git push" -ForegroundColor White
