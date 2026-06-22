# Master scraper — all sites in one command
param([string]$Site = "help")

$ErrorActionPreference = "Continue"
$git = "C:\Program Files\Git\bin\git.exe"
$start = Get-Date

function Log($m) { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $m" -ForegroundColor Green }
function RunPy($n, $s, $a) { Log ">>> $n"; python -X utf8 $s $a 2>&1 }

function Deploy {
    Log "--- Converting ---"
    python -X utf8 "screpte/streamimdb/convert_to_js.py" 2>&1
    python -X utf8 "screpte/cimafre/convert_to_js.py" 2>&1
    python -X utf8 "screpte/ooanime/convert_to_js.py" 2>&1
    Log "--- Deploying ---"
    & $git add -A; & $git commit -m "auto update"; & $git push
    $d = [math]::Round(((Get-Date)-$start).TotalMinutes,1)
    Log "Done in ${d}min"
}

switch -Wildcard ($Site.ToLower()) {
    "streamimdb" { RunPy "streamimdb" "screpte/streamimdb/scrape_streamimdb.py" "--embeds-only --resume --parallel 5"; Deploy }
    "ooanime"    { RunPy "ooanime" "screpte/ooanime/scrape_ooanime.py" "--episodes-only --resume --parallel 5"; Deploy }
    "cimafre"    { RunPy "cimafre listing" "screpte/cimafre/scrape_cimafre.py" "--to 999"; RunPy "cimafre servers" "screpte/cimafre/scrape_cimafre.py" "--servers --parallel 10"; Deploy }
    "tuktuk"     { RunPy "foreign movies" "screpte/tuktukhd/tuktuk/scripte-film.py" "--all -s 1 -e 5 -o screpte/tuktukhd/tuktuk/foreign.json"; RunPy "dubbed movies" "screpte/tuktukhd/tuktuk/scripte-dubbed.py" "--all -s 1 -e 5 -o screpte/tuktukhd/tuktuk/dubbed.json"; RunPy "foreign series" "screpte/tuktukhd/scrape_foreign_series.py" "--resume --workers 4"; Deploy }
    "turkish"    { RunPy "turkish" "screpte/ahwak/0606206/scrape_turkish_series.py" "--resume --workers 4"; Deploy }
    "asian"      { RunPy "asian scrape" "screpte/ahwak/07062026/scrape_yam_all.py" "--cat asian-series --episodes-only --start-page 1 --end-page 5"; RunPy "asian merge" "screpte/ahwak/ASSIAN/merge_asian_to_data.py" ""; Deploy }
    "all" {
        RunPy "streamimdb" "screpte/streamimdb/scrape_streamimdb.py" "--embeds-only --resume --parallel 5"
        RunPy "ooanime" "screpte/ooanime/scrape_ooanime.py" "--episodes-only --resume --parallel 5"
        RunPy "cimafre listing" "screpte/cimafre/scrape_cimafre.py" "--to 999"
        RunPy "cimafre servers" "screpte/cimafre/scrape_cimafre.py" "--servers --parallel 10"
        RunPy "turkish" "screpte/ahwak/0606206/scrape_turkish_series.py" "--resume --workers 4"
        RunPy "tuktuk foreign" "screpte/tuktukhd/tuktuk/scripte-film.py" "--all -s 1 -e 5 -o screpte/tuktukhd/tuktuk/foreign.json"
        RunPy "tuktuk dubbed" "screpte/tuktukhd/tuktuk/scripte-dubbed.py" "--all -s 1 -e 5 -o screpte/tuktukhd/tuktuk/dubbed.json"
        RunPy "tuktuk series" "screpte/tuktukhd/scrape_foreign_series.py" "--resume --workers 4"
        Deploy
    }
    default {
        Write-Host @"
Usage: .\scrape_all.ps1 -Site <name>
  streamimdb  foreign movies (70k+)
  ooanime     old cartoons (7k eps)
  cimafre     arabic movies (419)
  tuktuk      foreign/dubbed movies + series
  turkish     turkish series
  asian       asian series
  all         everything (slow!)
"@
    }
}
