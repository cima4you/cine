param(
    [int]$StartPage = 1,
    [int]$EndPage = 5,
    [int]$Delay = 2
)

$ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SCRAPER = "$ROOT\screpte\tuktukhd\tuktuk\scripte-dubbed.py"
$MERGER = "$ROOT\screpte\tuktukhd\tuktuk\merge_dubbed_to_data.py"
$OUTPUT = "$ROOT\screpte\tuktukhd\tuktuk\dubbed.json"

Write-Host "========== TukTuk Dubbed Films ==========" -ForegroundColor Cyan
Write-Host "Pages: $StartPage - $EndPage" -ForegroundColor Yellow

Write-Host "[1/2] Scraping dubbed films..." -ForegroundColor Yellow
python $SCRAPER --all -s $StartPage -e $EndPage -o $OUTPUT -d $Delay
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }

Write-Host "[2/2] Merging into data-dubbed.js..." -ForegroundColor Yellow
python $MERGER
if ($LASTEXITCODE -ne 0) { Write-Host "Merge FAILED" -ForegroundColor Red; exit 1 }

Write-Host "`nDone! Now commit and push:" -ForegroundColor Green
Write-Host "git add -A && git commit -m `"تحديث أفلام مدبلجة TukTuk`" && git push" -ForegroundColor White
