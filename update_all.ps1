# Full automation script: scrape -> convert -> deploy
param([string]$Scraper = "all", [switch]$Help)

if ($Help) {
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\update_all.ps1               # run all scrapers"
    Write-Host "  .\update_all.ps1 -Scraper streamimdb"
    Write-Host "  .\update_all.ps1 -Scraper ooanime"
    Write-Host "  .\update_all.ps1 -Scraper cimafre"
    Write-Host "  .\update_all.ps1 -Help"
    exit
}

$ErrorActionPreference = "Continue"
$startTime = Get-Date
$git = "C:\Program Files\Git\bin\git.exe"

function Log($msg) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor Green
}

function RunPy($name, $script, $args) {
    Log "--- Starting $name ---"
    python -X utf8 $script $args 2>&1
    Log "--- Finished $name ---"
}

# 1. Run scrapers
if ($Scraper -eq "all" -or $Scraper -eq "streamimdb") {
    RunPy "StreamIMDb embeds" "screpte/streamimdb/scrape_streamimdb.py" "--embeds-only --resume --parallel 5"
}
if ($Scraper -eq "all" -or $Scraper -eq "cimafre") {
    RunPy "Cimafre listing" "screpte/cimafre/scrape_cimafre.py" "--to 999"
    RunPy "Cimafre servers" "screpte/cimafre/scrape_cimafre.py" "--servers --parallel 10"
}
if ($Scraper -eq "all" -or $Scraper -eq "ooanime") {
    RunPy "OOAnime episodes" "screpte/ooanime/scrape_ooanime.py" "--episodes-only --resume --parallel 5"
}

# 2. Convert to JS
Log "--- Converting to JS ---"
python -X utf8 "screpte/streamimdb/convert_to_js.py" 2>&1
python -X utf8 "screpte/cimafre/convert_to_js.py" 2>&1
python -X utf8 "screpte/ooanime/convert_to_js.py" 2>&1

# 3. Deploy to GitHub
Log "--- Deploying to GitHub ---"
$msg = if ($Scraper -eq "all") { "auto update" } else { "auto update $Scraper" }

& $git add -A
& $git commit -m $msg
& $git push

$dur = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
Log "Done in ${dur}min"
Log "Site: https://cima4you.github.io/cine/"
