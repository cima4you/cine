param(
    [int]$StartPage = 1,
    [int]$EndPage = 5,
    [switch]$EpisodesOnly = $false
)

$ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SCRAPER = "$ROOT\screpte\ahwak\07062026\scrape_yam_all.py"
$MERGER = "$ROOT\screpte\ahwak\07062026\merge_hindi_to_data.py"
$OUTPUT = "$ROOT\screpte\ahwak\07062026\hindi_movies.json"

Write-Host '========== Hindi Films (Ahwak) ==========' -ForegroundColor Cyan
Write-Host "Pages: $StartPage - $EndPage" -ForegroundColor Yellow

$epFlag = if ($EpisodesOnly) { '--episodes-only' } else { '' }

Write-Host '[1/2] Scraping Hindi films from yam.ahwaktv.net...' -ForegroundColor Yellow
python -X utf8 $SCRAPER --cat hindi-movies --start-page $StartPage --end-page $EndPage $epFlag --output $OUTPUT
if ($LASTEXITCODE -ne 0) { Write-Host 'FAILED' -ForegroundColor Red; exit 1 }

Write-Host '[2/2] Merging into data-hindi.js...' -ForegroundColor Yellow
python -X utf8 $MERGER
if ($LASTEXITCODE -ne 0) { Write-Host 'Merge FAILED' -ForegroundColor Red; exit 1 }

Write-Host "`nDone! Now commit and push:" -ForegroundColor Green
Write-Host 'git add -A && git commit -m "تحديث أفلام هندية" && git push' -ForegroundColor White
