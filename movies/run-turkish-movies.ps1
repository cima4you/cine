param(
    [int]$StartPage = 1,
    [int]$EndPage = 5,
    [int]$Delay = 2
)

$ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SCRAPER = "$ROOT\screpte\tuktukhd\tuktuk\scripte-film.py"
$MERGER = "$ROOT\screpte\tuktukhd\tuktuk\merge_turkish_movies_to_data.py"
$OUTPUT = "$ROOT\screpte\tuktukhd\tuktuk\turkish_movies.json"
$TURKISH_URL = 'https://tuktukhd.com/tag/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%AA%D8%B1%D9%83%D9%8A%D8%A9'

Write-Host '========== Turkish Films (TukTuk) ==========' -ForegroundColor Cyan
Write-Host "Pages: $StartPage - $EndPage" -ForegroundColor Yellow

Write-Host '[1/2] Scraping Turkish films...' -ForegroundColor Yellow
python -u $SCRAPER --all -s $StartPage -e $EndPage -u $TURKISH_URL -o $OUTPUT -d $Delay
if ($LASTEXITCODE -ne 0) { Write-Host 'FAILED' -ForegroundColor Red; exit 1 }

Write-Host '[2/2] Merging into data-turkish-movies.js...' -ForegroundColor Yellow
python $MERGER
if ($LASTEXITCODE -ne 0) { Write-Host 'Merge FAILED' -ForegroundColor Red; exit 1 }

Write-Host "`nDone! Now commit and push:" -ForegroundColor Green
Write-Host 'git add -A && git commit -m "تحديث أفلام تركية" && git push' -ForegroundColor White
