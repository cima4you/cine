# 🚀 Update all movies from tuktukhd
Write-Host "========== Movie Update ==========" -ForegroundColor Cyan

$BASE = "screpte/tuktukhd/tuktuk"

Write-Host "`n[1/2] Dubbed movies..." -ForegroundColor Yellow
python "$BASE/scripte-dubbed.py" --all -s 1 -e 5 -o "$BASE/dubbed.json"
if ($LASTEXITCODE -eq 0) {
    python "$BASE/merge_dubbed_to_data.py"
}

Write-Host "`n[2/2] Foreign movies..." -ForegroundColor Yellow
python "$BASE/scripte-film.py" --all -s 1 -e 5 -o "$BASE/foreign.json"
if ($LASTEXITCODE -eq 0) {
    python merge_tuktuk_to_data.py
}

Write-Host "`nDone!" -ForegroundColor Green
