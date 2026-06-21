# update series from tuktukhd
Write-Host "========== Series Update ==========" -ForegroundColor Cyan

$SERIES = "screpte/tuktukhd"

Write-Host "[1/1] Foreign series..." -ForegroundColor Yellow
python "$SERIES/scrape_foreign_series.py" --start 1 --end 3 --workers 4 --phase all
if ($LASTEXITCODE -eq 0) {
    python "$SERIES/scrape_foreign_series.py" --convert --merge "data/data-foreign-series.js" --output "data/data-foreign-series.js"
}

Write-Host "Done!" -ForegroundColor Green
