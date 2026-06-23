param(
    [int]$StartPage = 1,
    [int]$EndPage = 5,
    [int]$Delay = 2
)

$ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SCRAPER = "$ROOT\screpte\tuktukhd\tuktuk\scripte-film.py"
$MERGER = "$ROOT\screpte\tuktukhd\tuktuk\merge_anime_to_data.py"
$OUTPUT = "$ROOT\screpte\tuktukhd\tuktuk\anime_movies.json"
$ANIME_URL = 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%A7%D9%86%D9%85%D9%8A/'

Write-Host '========== Anime Films (TukTuk) ==========' -ForegroundColor Cyan
Write-Host "Pages: $StartPage - $EndPage" -ForegroundColor Yellow

Write-Host '[1/2] Scraping Anime films...' -ForegroundColor Yellow
python -u $SCRAPER --all -s $StartPage -e $EndPage -u $ANIME_URL -o $OUTPUT -d $Delay
if ($LASTEXITCODE -ne 0) { Write-Host 'FAILED' -ForegroundColor Red; exit 1 }

Write-Host '[2/2] Merging into data-anime.js...' -ForegroundColor Yellow
python $MERGER
if ($LASTEXITCODE -ne 0) { Write-Host 'Merge FAILED' -ForegroundColor Red; exit 1 }

Write-Host "`nDone! Now commit and push:" -ForegroundColor Green
Write-Host 'git add -A; git commit -m "تحديث أنمي"; git push' -ForegroundColor White
