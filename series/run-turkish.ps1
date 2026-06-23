param(
    [int]$StartPage = 1,
    [int]$EndPage = 5,
    [int]$Workers = 4
)

$ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SCRAPER = "$ROOT\screpte\ahwak\0606206\scrape_turkish_series.py"

Write-Host "========== Turkish Series ==========" -ForegroundColor Cyan
Write-Host "Pages: $StartPage - $EndPage" -ForegroundColor Yellow

Write-Host "Scraping, converting, and merging..." -ForegroundColor Yellow
python $SCRAPER --start $StartPage --end $EndPage --workers $Workers --phase all --merge auto
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }

Write-Host "`nDone! Now commit and push:" -ForegroundColor Green
Write-Host "git add -A && git commit -m `"تحديث مسلسلات تركية`" && git push" -ForegroundColor White
