param(
    [int]$StartPage = 1,
    [int]$EndPage = 5,
    [int]$Workers = 4,
    [switch]$Update = $false
)

$ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SCRAPER = "$ROOT\screpte\ahwak\0606206\scrape_turkish_series.py"
$DATA_DIR = "$ROOT\screpte\ahwak\0606206\data"

Write-Host "========== Turkish Series ==========" -ForegroundColor Cyan
Write-Host "Pages: $StartPage - $EndPage" -ForegroundColor Yellow

if ($Update) {
    Write-Host "Mode: UPDATE - will refresh all data for pages $StartPage-$EndPage" -ForegroundColor Magenta
    Write-Host "Clearing old data files..." -ForegroundColor Yellow
    Remove-Item "$DATA_DIR\turkish_series_listing.json" -ErrorAction SilentlyContinue
    Remove-Item "$DATA_DIR\turkish_series_detail.json" -ErrorAction SilentlyContinue
    Remove-Item "$DATA_DIR\turkish_series_full.json" -ErrorAction SilentlyContinue
    Remove-Item "$DATA_DIR\state.json" -ErrorAction SilentlyContinue
    Write-Host "Old data cleared. Re-scraping from scratch..." -ForegroundColor Yellow
}

python $SCRAPER --start $StartPage --end $EndPage --workers $Workers --phase all --merge auto
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }

Write-Host "`nDone! Now commit and push:" -ForegroundColor Green
Write-Host 'git add -A && git commit -m "تحديث مسلسلات تركية" && git push' -ForegroundColor White
