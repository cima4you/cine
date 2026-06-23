param(
    [int]$StartPage = 1,
    [int]$EndPage = 3,
    [int]$Workers = 4
)

$ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SCRAPER = "$ROOT\screpte\tuktukhd\scrape_foreign_series.py"

Write-Host "========== TukTuk Foreign Series ==========" -ForegroundColor Cyan
Write-Host "Pages: $StartPage - $EndPage" -ForegroundColor Yellow

Write-Host "[1/2] Scraping foreign series..." -ForegroundColor Yellow
python $SCRAPER --start $StartPage --end $EndPage --workers $Workers --phase all
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }

Write-Host "[2/2] Converting and merging..." -ForegroundColor Yellow
python $SCRAPER --convert --merge "data-foreign-series.js" --output "data-foreign-series.js"
if ($LASTEXITCODE -ne 0) { Write-Host "Convert FAILED" -ForegroundColor Red; exit 1 }

Write-Host "`nDone! Now commit and push:" -ForegroundColor Green
Write-Host 'git add -A && git commit -m "تحديث مسلسلات أجنبية TukTuk" && git push' -ForegroundColor White
