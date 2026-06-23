param(
    [int]$StartPage = 1,
    [int]$EndPage = 5,
    [int]$Delay = 2
)

$ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SCRAPER = "$ROOT\screpte\tuktukhd\tuktuk\scripte-film.py"
$MERGER = "$ROOT\screpte\tuktukhd\tuktuk\merge_netflix_to_data.py"
$OUTPUT = "$ROOT\screpte\tuktukhd\tuktuk\netflix.json"
$NETFLIX_URL = 'https://tuktukhd.com/channel/film-netflix-1'

Write-Host '========== Netflix Films ==========' -ForegroundColor Cyan
Write-Host "Pages: $StartPage - $EndPage" -ForegroundColor Yellow

Write-Host '[1/2] Scraping Netflix films...' -ForegroundColor Yellow
python -u $SCRAPER --all -s $StartPage -e $EndPage -u $NETFLIX_URL -o $OUTPUT -d $Delay
if ($LASTEXITCODE -ne 0) { Write-Host 'FAILED' -ForegroundColor Red; exit 1 }

Write-Host '[2/2] Merging into data-netflix.js...' -ForegroundColor Yellow
python $MERGER
if ($LASTEXITCODE -ne 0) { Write-Host 'Merge FAILED' -ForegroundColor Red; exit 1 }

Write-Host "`nDone! Now commit and push:" -ForegroundColor Green
Write-Host 'git add -A && git commit -m "تحديث أفلام نتفليكس" && git push' -ForegroundColor White
