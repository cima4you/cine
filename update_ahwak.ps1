# Update Asian / Turkish series from ahwak
Write-Host "========== Ahwak Series Update ==========" -ForegroundColor Cyan

$AHWAK = "screpte/ahwak"

# --- Asian Series ---
Write-Host "`n[1/2] Asian series..." -ForegroundColor Yellow
python "$AHWAK/07062026/scrape_yam_all.py" --cat asian-series --output "$AHWAK/ASSIAN/asian_series_full.json" --start-page 1 --end-page 2 --episodes-only
if ($LASTEXITCODE -eq 0) {
    python "$AHWAK/ASSIAN/merge_asian_to_data.py"
}

# --- Turkish Series ---
Write-Host "`n[2/2] Turkish series..." -ForegroundColor Yellow
python "$AHWAK/0606206/merge_turkish_to_data.py"

Write-Host "`nDone!" -ForegroundColor Green
