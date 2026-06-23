param(
    [int]$StartPage = 1,
    [int]$EndPage = 2
)

$ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SCRAPER = "$ROOT\screpte\ahwak\07062026\scrape_yam_all.py"
$OUTPUT = "$ROOT\screpte\ahwak\ASSIAN\asian_series_full.json"
$MERGER = "$ROOT\screpte\ahwak\ASSIAN\merge_asian_to_data.py"

Write-Host "========== Asian Series ==========" -ForegroundColor Cyan
Write-Host "Pages: $StartPage - $EndPage" -ForegroundColor Yellow

Write-Host "[1/2] Scraping Asian series..." -ForegroundColor Yellow
python $SCRAPER --cat asian-series --episodes-only --start-page $StartPage --end-page $EndPage --output $OUTPUT
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }

Write-Host "[2/2] Merging into data files..." -ForegroundColor Yellow
python $MERGER --source $OUTPUT
if ($LASTEXITCODE -ne 0) { Write-Host "Merge FAILED" -ForegroundColor Red; exit 1 }

Write-Host "`nDone! Now commit and push:" -ForegroundColor Green
Write-Host 'git add -A && git commit -m "تحديث مسلسلات آسيوية" && git push' -ForegroundColor White
